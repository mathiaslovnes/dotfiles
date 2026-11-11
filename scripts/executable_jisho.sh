#!/bin/sh
# Caps+F (Karabiner): bring the Jisho scratchpad (see yabairc) to the current space and focus it, or open Jisho
# if it isn't running. yabai's --toggle also hides it when it's already on this space, so then it only gets focus.
PATH=/opt/homebrew/bin:$PATH   # Karabiner runs commands with a minimal PATH

w=$(yabai -m query --windows | jq -c 'first(.[] | select(.scratchpad == "jisho")) // empty')
if [ -z "$w" ]; then
  open "$HOME/Applications/Brave Browser Apps.localized/Jisho.org.app"
  exit
fi

id=$(echo "$w" | jq .id)
here=$(yabai -m query --spaces --space | jq .index)
if [ "$(echo "$w" | jq '."is-minimized"')" = true ]; then
  yabai -m window "$id" --space "$here" 2>/dev/null   # fails harmlessly if it's already here
  yabai -m window "$id" --deminimize
  yabai -m window "$id" --focus
elif [ "$(echo "$w" | jq --argjson s "$here" '."is-visible" and .space == $s')" = true ]; then
  yabai -m window "$id" --focus
else
  yabai -m window --toggle jisho   # on another space, or hidden (Option+W): shows it here and focuses it
fi
