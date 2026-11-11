#!/bin/sh
# Load yabai's scripting addition as root through the sudoers rule from ~/scripts/yabai-sudoers.sh. That rule
# only matches the yabai build it was made for, so after an upgrade sudo -n fails (instead of waiting for a
# password nobody can type) and this says what to run.
sudo -n /opt/homebrew/bin/yabai --load-sa ||
  osascript -e 'display notification "If yabai was just upgraded, run ~/scripts/yabai-sudoers.sh" with title "yabai couldn’t load its scripting addition"'
