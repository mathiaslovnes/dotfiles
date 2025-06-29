#!/bin/bash

# Focus space and make it floating
yabai -m space --focus 4
yabai -m space --layout float

# Launch apps
open -a mpv
open -na "Brave Browser"
open -a "ChatGPT"
# open -a "Pycharm"

osascript <<EOF
tell application "Brave Browser"
    activate
    delay 0.5
    if (count of windows) = 0 then
        make new window
    end if
    set URL of active tab of front window to "https://anacreondjt.gitlab.io/texthooker.html"
end tell
EOF

# Slight delay to let windows settle
sleep 0.5

# Get window IDs
mpv_id=$(yabai -m query --windows | jq '.[] | select(.app == "mpv") | .id')
gpt_id=$(yabai -m query --windows | jq '.[] | select(.app == "ChatGPT") | .id')
brave_id=$(yabai -m query --windows | jq '.[] | select(.app == "Brave Browser") | .id')
# pycharm_id=$(yabai -m query --windows | jq '.[] | select(.app == "Pycharm") | .id')

# Move mpv 
if [ -n "$mpv_id" ]; then
  yabai -m window "$mpv_id" --space 4
  yabai -m window "$mpv_id" --move abs:0:0
  yabai -m window "$mpv_id" --resize abs:3440:1440  
fi

# Move Brave 
if [ -n "$brave_id" ]; then
  yabai -m window "$brave_id" --space 4
  yabai -m window "$brave_id" --move abs:450:0
  yabai -m window "$brave_id" --resize abs:1147:1440
fi

# Move GPT
if [ -n "$gpt_id" ]; then
  yabai -m window "$gpt_id" --space 4
  yabai -m window "$gpt_id" --move abs:325:125
  yabai -m window "$gpt_id" --resize abs:1575:1200
fi

# Move Pycharm
# if [ -n "$pycharm_id" ]; then
#  yabai -m window "$pycharm_id" --space 4
#  yabai -m window "$pycharm_id" --move abs:325:125
#  yabai -m window "$pycharm_id" --resize abs:1575:1200
#fi

# Ensure Pycharm is front
#open -a "Pycharm"
