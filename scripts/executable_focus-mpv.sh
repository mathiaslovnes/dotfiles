#!/bin/bash
# Focus the mpv window that's playing video; launch mpv if none is open.
# "open -a mpv" / "activate" can't be used: a script running in mpv starts a
# second, windowless mpv process with the same app ID, and macOS sometimes
# activates that one, so keys go nowhere until you click the video.
# Focusing the window itself always activates the right process.

id=$(/opt/homebrew/bin/yabai -m query --windows \
  | /opt/homebrew/bin/jq -r 'map(select(.app == "mpv")) | first | .id // empty')

if [ -n "$id" ]; then
  /opt/homebrew/bin/yabai -m window --focus "$id"
else
  open -a mpv
fi
