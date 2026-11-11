#!/bin/bash
# Focus the mpv process that's playing video; launch mpv if none is open (Karabiner Caps+V).
# "open -a mpv" / "activate" can't be used: thumbfast starts a second, windowless mpv process with the same
# app ID, and macOS sometimes activates that one, so keys go nowhere until you click the video.
# yabai can't focus a fullscreen mpv on another space (no AX reference), but it reports the window's pid, and
# activating that process switches to its space.

pid=$(/opt/homebrew/bin/yabai -m query --windows \
  | /opt/homebrew/bin/jq -r 'map(select(.app == "mpv")) | first | .pid // empty')

if [ -n "$pid" ]; then
  osascript -e "tell application \"System Events\" to set frontmost of (first process whose unix id is $pid) to true"
else
  open -a mpv
fi
