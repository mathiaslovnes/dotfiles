#!/bin/sh
# Battery percent, with an icon that's green, yellow or red by charge, and a charging icon while on power
. "$CONFIG_DIR/colors.sh"
batt=$(pmset -g batt)
pct=$(echo "$batt" | grep -Eo '[0-9]+%' | tr -d %)
case $pct in
  9[0-9] | 100) icon=󰁹 color=$GREEN ;;
  [5-8][0-9]) icon=󰂀 color=$GREEN ;;
  [2-4][0-9]) icon=󰁾 color=$YELLOW ;;
  *) icon=󰁻 color=$RED ;;
esac
echo "$batt" | grep -q 'AC Power' && icon=󰂄
sketchybar --set "$NAME" icon="$icon" icon.color="$color" label="$pct%"
