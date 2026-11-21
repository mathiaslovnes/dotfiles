#!/bin/sh
# Output volume; at startup there's no event $INFO, so ask macOS
vol=${INFO:-$(osascript -e 'output volume of (get volume settings)')}
case $vol in
  [6-9][0-9] | 100) icon=󰕾 ;;
  [3-5][0-9]) icon=󰖀 ;;
  [1-9] | [1-2][0-9]) icon=󰕿 ;;
  *) icon=󰖁 ;;
esac
sketchybar --set "$NAME" icon="$icon" label="$vol%"
