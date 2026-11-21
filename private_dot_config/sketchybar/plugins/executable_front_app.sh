#!/bin/bash
# The front app's icon and name; at startup there's no event $INFO, so ask yabai
source "$CONFIG_DIR/plugins/icon_map.sh"
app=${INFO:-$(yabai -m query --windows --window | jq -r .app)}
sketchybar --set "$NAME" icon="$(icon_map "$app")" label="$app"
