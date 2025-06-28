
yabai -m space --focus 4

yabai -m space --layout float

# Launch apps (or bring to front)
open -a mpv
open -a "Brave Browser"
open -a "ChatGPT"
open -a "Pycharm" 

sleep 1  # wait a bit for apps to launch

osascript -e 'tell application "Brave Browser"
    make new window
    set URL of active tab of front window to "https://anacreondjt.gitlab.io/texthooker.html"
end tell'

# Get window IDs
mpv_id=$(yabai -m query --windows | jq '.[] | select(.app == "mpv") | .id')
brave_id=$(yabai -m query --windows | jq '.[] | select(.app == "Brave Browser") | .id')
gpt_id=$(yabai -m query --windows | jq '.[] | select(.app == "ChatGPT") | .id')
pycharm_id=$(yabai -m query --windows | jq '.[] | select(.app == "Pycharm") | .id')

# Move mpv 
yabai -m window "$mpv_id" --space 4
yabai -m window "$mpv_id" --move abs:0:0
yabai -m window "$mpv_id" --resize abs:3440:1440  

# Move Brave 
yabai -m window "$brave_id" --space 4
yabai -m window "$brave_id" --move abs:450:0
yabai -m window "$brave_id" --resize abs:1147:1440

# Move GPT
yabai -m window "$gpt_id" --space 4
yabai -m window "$gpt_id" --move abs:325:125
yabai -m window "$gpt_id" --resize abs:1575:1200

# Move Pycharm
yabai -m window "$pycharm_id" --space 4
yabai -m window "$pycharm_id" --move abs:325:125
yabai -m window "$pycharm_id" --resize abs:1575:1200
open -a "Pycharm"




