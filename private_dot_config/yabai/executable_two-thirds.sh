#!/bin/sh
# skhd: give the focused window 2/3 of the display's width. A tiled window moves the edge that faces its
# neighbor (yabai changes the split that owns that edge); a floating window takes the left two thirds.

win=$(yabai -m query --windows --window) || exit 0
id=$(echo "$win" | jq '.id')
if [ "$(echo "$win" | jq '."is-floating"')" = true ]; then
  yabai -m window "$id" --grid 1:3:0:0:2:1
  exit 0
fi

display=$(yabai -m query --displays --display)
target=$(( $(echo "$display" | jq '.frame.w | round') * 2 / 3 ))
dx=$(( target - $(echo "$win" | jq '.frame.w | round') ))

# a window at the display's left edge grows or shrinks to the right, any other one to the left
if [ "$(echo "$win" | jq '.frame.x | round')" -le "$(echo "$display" | jq '.frame.x | round')" ]; then
  yabai -m window "$id" --resize "right:$dx:0"
else
  yabai -m window "$id" --resize "left:$((-dx)):0"
fi
