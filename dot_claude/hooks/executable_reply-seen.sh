#!/bin/sh
# Claude Code Stop hook. When a reply ends, marks its tmux window seen if a focused kitty is showing it and unseen
# otherwise; tmux marks it seen once focus enters it (pane-focus-in in .tmux.conf). notify.sh skips the idle
# reminder for a seen window.
[ -n "$TMUX_PANE" ] || exit 0
win=$(tmux display-message -p -t "$TMUX_PANE" '#{window_id}')
tmux list-clients -F '#{window_id} #{client_flags}' | grep -q "^$win .*focused" && seen=1 || seen=0
tmux set-option -w -t "$TMUX_PANE" @claude-seen "$seen"
