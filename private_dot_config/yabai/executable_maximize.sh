#!/bin/sh
# skhd's maximize key: a tiled window toggles yabai's zoom-fullscreen. That ignores floating windows (and windows
# on a float-layout space), so those fill the space through the grid instead, and the next press puts them back
# where they were.
w=$(yabai -m query --windows --window) || exit 0
if [ "$(echo "$w" | jq '."is-floating"')" = false ] && [ "$(yabai -m query --spaces --space | jq -r .type)" != float ]; then
  exec yabai -m window --toggle zoom-fullscreen
fi

frame() { yabai -m query --windows --window | jq -r '.frame | "\(.x|round) \(.y|round) \(.w|round) \(.h|round)"'; }
mem=/tmp/yabai-maximize-$(id -u)-$(echo "$w" | jq .id)   # line 1: the frame before, line 2: the maximized frame
now=$(frame)
# still maximized (apps report their frame a pixel off now and then): restore
if [ -f "$mem" ] && echo "$now $(sed -n 2p "$mem")" |
  awk '{ for (i = 1; i <= 4; i++) { d = $i - $(i + 4); if (d > 2 || d < -2) exit 1 } }'; then
  read -r x y width height < "$mem"
  yabai -m window --resize "abs:$width:$height"   # resize first, so the move isn't clamped by the full size
  yabai -m window --move "abs:$x:$y"
  rm -f "$mem"
else
  yabai -m window --grid 1:1:0:0:1:1
  printf '%s\n%s\n' "$now" "$(frame)" > "$mem"
fi
