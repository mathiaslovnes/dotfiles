#!/bin/sh
# Claude Code Notification hook. Puts a bell on the pane's window in the status bar until you go to the pane, and
# has kitty show a desktop notification, passed through tmux (allow-passthrough all). kitty on macOS can only play
# the default sound, the system alert sound, so the notification is silent and Glass plays instead.
[ -n "$TMUX_PANE" ] || exit 0
# nothing to flag while you're in the pane, in a focused kitty
tmux list-clients -F '#{pane_id} #{client_flags}' | grep -q "^$TMUX_PANE .*focused" && exit 0
input=$(cat)
# no reminder that Claude is waiting if you've seen the reply since it ended (reply-seen.sh)
[ "$(printf '%s' "$input" | jq -r .notification_type)" = idle_prompt ] &&
  [ "$(tmux display-message -p -t "$TMUX_PANE" '#{@claude-seen}')" = 1 ] && exit 0
tty=$(tmux display-message -p -t "$TMUX_PANE" '#{pane_tty}')
# not tmux's own bell, which never marks the window you're in (Claude next to Neovim); the status bar draws this
# one, and pane-focus-in in .tmux.conf clears it
tmux set-option -p -t "$TMUX_PANE" @claude-bell 1
# while kitty is the app in front, the bell icon is enough
lsappinfo info -only bundleid "$(lsappinfo front)" | grep -q '"net.kovidgoyal.kitty"' && exit 0
msg=$(printf '%s' "$input" | jq -r '.message // "Claude Code needs you"')
code=$(kitten notify --only-print-escape-code --sound-name silent \
  "Claude Code · $(tmux display-message -p -t "$TMUX_PANE" '#S:#I')" "$msg")
esc=$(printf '\033')
# tmux passthrough: \ePtmux; + the code with every Esc doubled + \e\\
printf '%sPtmux;%s%s\\' "$esc" "$(printf '%s' "$code" | sed "s/$esc/$esc$esc/g")" "$esc" > "$tty"
afplay -v 0.3 /System/Library/Sounds/Glass.aiff > /dev/null 2>&1 &   # -v: 1 is full volume
