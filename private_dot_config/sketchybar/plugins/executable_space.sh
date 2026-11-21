#!/bin/sh
# The current space's box is peach, like tmux's current window
. "$CONFIG_DIR/colors.sh"
if [ "$SELECTED" = true ]; then
  sketchybar --set "$NAME" background.color=$PEACH icon.color=$MANTLE label.color=$MANTLE
else
  sketchybar --set "$NAME" background.color=$SURFACE0 icon.color=$TEXT label.color=$TEXT
fi
