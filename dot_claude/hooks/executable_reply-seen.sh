#!/bin/sh
# Claude Code Stop hook. When a reply ends, marks its tmux pane seen if it's the pane you're in, in a focused kitty,
# and unseen otherwise; tmux marks it seen once focus enters it (pane-focus-in in .tmux.conf). notify.sh skips the
# idle reminder for a seen pane.
[ -n "$TMUX_PANE" ] || exit 0
tmux list-clients -F '#{pane_id} #{client_flags}' | grep -q "^$TMUX_PANE .*focused" && seen=1 || seen=0
tmux set-option -p -t "$TMUX_PANE" @claude-seen "$seen"
