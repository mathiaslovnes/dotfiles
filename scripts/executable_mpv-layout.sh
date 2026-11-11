#!/bin/bash
# Mining layout on space 4 (skhd ctrl+cmd+m): mpv fullscreen underneath (it fullscreens itself, see
# mpv's yabai_track.lua), with Brave's texthooker, Claude and the subs and Torrents folders floating on top.
# Activating an app makes macOS switch to a space where it already has windows, so nothing here activates an
# app that's running, and every window is looked up by id and moved to space 4 wherever it opened.

yabai -m space --focus 4 2>/dev/null   # fails harmlessly if already there
yabai -m space 4 --layout float

before=$(yabai -m query --windows | jq -c 'map(.id)')   # so the windows opened below can be told apart

# id of app $1's first standard window titled $2 (any title if empty); with $3 = new, only a window that
# wasn't in $before. The subrole check leaves out Brave's tooltip windows
win() {
  yabai -m query --windows | jq --arg a "$1" --arg t "${2-}" --arg new "${3-}" --argjson old "$before" '
    first(.[] | select(.app == $a and .subrole == "AXStandardWindow" and ($t == "" or .title == $t)
      and ($new == "" or (.id | IN($old[]) | not))) | .id) // empty'
}
# the same, waiting up to ~5 s for the window to appear
wait_win() {
  for _ in $(seq 25); do
    id=$(win "$@")
    [ -n "$id" ] && { echo "$id"; return 0; }
    sleep 0.2
  done
  return 1
}

[ -n "$(win mpv)" ] || open -a mpv

osascript -e 'tell application "Brave Browser"' \
  -e 'set w to make new window' \
  -e 'set URL of active tab of w to "https://anacreondjt.gitlab.io/texthooker.html"' \
  -e 'end tell'

# one new window per folder (`open -na Finder <dir>` also opened Finder's default window)
subs=~/Documents/日本語/subscript/subs
for dir in "$subs" ~/Torrents; do
  osascript -e 'on run argv' \
    -e 'set f to (POSIX file (item 1 of argv)) as alias' \
    -e 'tell application "Finder" to make new Finder window to f' \
    -e 'end run' "$dir" >/dev/null
done

claude_id=$(win Claude)
[ -n "$claude_id" ] || { open -a Claude; claude_id=$(wait_win Claude); }
brave_id=$(wait_win "Brave Browser" "" new)
subs_id=$(wait_win Finder "${subs##*/}" new)
torr_id=$(wait_win Finder Torrents new)

# move to space 4 (fails harmlessly if already there), unminimize, then --grid rows:cols:x:y:w:h, which
# places a floating window as a fraction of the screen, so it fits any display
place() {
  yabai -m window "$1" --space 4 2>/dev/null
  yabai -m window "$1" --deminimize 2>/dev/null
  yabai -m window "$1" --grid "$2"
}
[ -n "$brave_id" ]  && place "$brave_id"  1:24:3:0:8:1
[ -n "$claude_id" ] && place "$claude_id" 12:48:13:1:22:10   # centered
[ -n "$subs_id" ]   && place "$subs_id"   12:24:11:0:6:6
[ -n "$torr_id" ]   && place "$torr_id"   12:24:18:0:6:6

yabai -m space --focus 4 2>/dev/null   # in case a launch switched spaces
