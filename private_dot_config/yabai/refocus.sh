#!/bin/sh
# Run by yabai signals (yabairc) when a window closes, minimizes, hides or its app quits: if nothing has
# focus, focus the window under the mouse, else the first visible window on the space.
yabai -m query --windows --window >/dev/null 2>&1 && exit 0
yabai -m window --focus mouse >/dev/null 2>&1 && exit 0
id=$(yabai -m query --windows --space | jq 'map(select(."is-visible" and (."is-minimized" | not)))[0].id // empty')
[ -n "$id" ] && yabai -m window --focus "$id"
