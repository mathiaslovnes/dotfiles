#!/bin/sh
# Claude Code Notification hook. Rings the pane's bell, so tmux marks the window in the status bar.
[ -n "$TMUX_PANE" ] || exit 0
printf '\a' > "$(tmux display-message -p -t "$TMUX_PANE" '#{pane_tty}')"
