#!/bin/bash
# Mining layout on space 4 (skhd ctrl+cmd+m): mpv fullscreen underneath (it fullscreens itself, see
# mpv's yabai_track.lua), with Brave's texthooker, Claude and the Torrents folder floating on top.

# Focus space and make it floating
yabai -m space --focus 4
yabai -m space --layout float

# Launch apps
open -a mpv
open -na "Brave Browser"
open -a "Claude"
open -na "Finder" ~/Torrents

osascript <<EOF
tell application "Brave Browser"
    activate
    delay 0.5
    if (count of windows) = 0 then
        make new window
    end if
    set URL of active tab of front window to "https://anacreondjt.gitlab.io/texthooker.html"
end tell
EOF

# id of app $1's front-most standard window (titled $2 / on space $3 if given), waiting up to ~5 s; the
# subrole check leaves out Brave's tooltip windows
wait_win() {
  for _ in $(seq 25); do
    id=$(yabai -m query --windows | jq --arg a "$1" --arg t "${2-}" --arg s "${3-}" \
      'first(.[] | select(.app == $a and .subrole == "AXStandardWindow" and ($t == "" or .title == $t)
        and ($s == "" or (.space | tostring) == $s)) | .id) // empty')
    [ -n "$id" ] && { echo "$id"; return 0; }
    sleep 0.2
  done
  return 1
}

claude_id=$(wait_win "Claude")
brave_id=$(wait_win "Brave Browser" "" 4)   # the new window; other Brave windows stay where they are
torr_id=$(wait_win "Finder" "Torrents")

# move to space 4 (fails harmlessly if already there), then --grid rows:cols:x:y:w:h, which places a
# floating window as a fraction of the screen, so it fits any display
place() {
  yabai -m window "$1" --space 4 2>/dev/null
  yabai -m window "$1" --grid "$2"
}
[ -n "$brave_id" ]  && place "$brave_id"  1:24:3:0:8:1
[ -n "$claude_id" ] && place "$claude_id" 12:24:2:1:11:10
[ -n "$torr_id" ]   && place "$torr_id"   12:24:18:0:6:6

yabai -m space --focus 4 2>/dev/null   # opening Claude can switch to the space its window was on
