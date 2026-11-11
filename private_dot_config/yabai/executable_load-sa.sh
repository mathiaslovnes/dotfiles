#!/bin/sh
# Load yabai's scripting addition as root through the sudoers rule from ~/scripts/yabai-sudoers.sh. sudo -n
# fails at once without that rule (on a new Mac) instead of waiting for a password nobody can type, and this
# says what to run.
sudo -n /opt/homebrew/bin/yabai --load-sa ||
  osascript -e 'display notification "On a new Mac, run ~/scripts/yabai-sudoers.sh once" with title "yabai couldn’t load its scripting addition"'
