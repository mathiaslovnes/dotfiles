#!/bin/bash
# Shows the icons of the apps with windows on the space the event is about ($INFO: {"space": 2, "apps": {"kitty": 1}})
[ "$SENDER" = space_windows_change ] || exit 0
source "$CONFIG_DIR/plugins/icon_map.sh"
icons=""
while read -r app; do
  icons+=" $(icon_map "$app")"
done < <(jq -r '.apps | keys[]' <<< "$INFO")
sketchybar --set space.$(jq .space <<< "$INFO") label="${icons# }" label.drawing=$([ -n "$icons" ] && echo on || echo off)
