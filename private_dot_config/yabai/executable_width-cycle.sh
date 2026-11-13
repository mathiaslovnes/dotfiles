#!/bin/sh
# skhd: cycle the focused window's width through 1/2, 2/3 and 3/4 of the display: each press picks the
# first of those wider than the window is now, and after 3/4 starts over at 1/2. A tiled window moves the
# edge that faces its neighbor (yabai changes the split that owns that edge); a floating window is placed
# at the left of the screen.

win=$(yabai -m query --windows --window) || exit 0
id=$(echo "$win" | jq '.id')
display=$(yabai -m query --displays --display)
dw=$(echo "$display" | jq '.frame.w | round')
w=$(echo "$win" | jq '.frame.w | round')

# numerator/denominator of the next width; 10 px of slack so a width that is already a step counts as that step
for f in 1/2 2/3 3/4; do
  num=${f%/*} den=${f#*/}
  [ $((dw * num / den)) -gt $((w + 10)) ] && break
  num=1 den=2
done

if [ "$(echo "$win" | jq '."is-floating"')" = true ]; then
  yabai -m window "$id" --grid "1:$den:0:0:$num:1"
  exit 0
fi

dx=$((dw * num / den - w))
# a window at the display's left edge grows or shrinks to the right, any other one to the left
if [ "$(echo "$win" | jq '.frame.x | round')" -le "$(echo "$display" | jq '.frame.x | round')" ]; then
  yabai -m window "$id" --resize "right:$dx:0"
else
  yabai -m window "$id" --resize "left:$((-dx)):0"
fi
