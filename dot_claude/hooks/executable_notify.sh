#!/bin/sh
# Claude Code Notification hook. Rings the pane's bell, so tmux marks the window in the status bar, and has kitty
# show a desktop notification, passed through tmux (allow-passthrough all). kitty on macOS can only play the
# default sound, the system alert sound, so the notification is silent and Glass plays instead.
[ -n "$TMUX_PANE" ] || exit 0
tty=$(tmux display-message -p -t "$TMUX_PANE" '#{pane_tty}')
printf '\a' > "$tty"
msg=$(jq -r '.message // "Claude Code needs you"')
code=$(kitten notify --only-print-escape-code --sound-name silent \
  "Claude Code · $(tmux display-message -p -t "$TMUX_PANE" '#S:#I')" "$msg")
esc=$(printf '\033')
# tmux passthrough: \ePtmux; + the code with every Esc doubled + \e\\
printf '%sPtmux;%s%s\\' "$esc" "$(printf '%s' "$code" | sed "s/$esc/$esc$esc/g")" "$esc" > "$tty"
afplay /System/Library/Sounds/Glass.aiff > /dev/null 2>&1 &
