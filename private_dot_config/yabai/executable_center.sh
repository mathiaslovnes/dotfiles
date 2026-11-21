#!/bin/sh
# Center the focused window, floating it first, in the area macOS leaves for windows (below the menu bar and
# beside the Dock) minus sketchybar's strip at the top; yabai only reports the whole display, which put the window
# half a menu bar too high
[ "$(yabai -m query --windows --window | jq '."is-floating"')" = false ] && yabai -m window --toggle float
area=$(osascript -l JavaScript -e 'ObjC.import("AppKit"); const v = $.NSScreen.mainScreen.visibleFrame, p = $.NSScreen.screens.objectAtIndex(0).frame; JSON.stringify({x: v.origin.x, y: p.size.height - v.origin.y - v.size.height, w: v.size.width, h: v.size.height})')
bar=$(yabai -m config external_bar | cut -d: -f2)   # "all:32:0" in yabairc
yabai -m window --move "abs:$(yabai -m query --windows --window | jq -r --argjson a "$area" --argjson bar "$bar" '"\($a.x + ($a.w - .frame.w) / 2 | floor):\($a.y + $bar + ($a.h - $bar - .frame.h) / 2 | floor)"')"
