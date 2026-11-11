#!/bin/sh
# Claude Code Notification hook. Rings the pane's bell, so tmux marks the window in the status bar, and posts a
# macOS notification when the pane's window isn't visible: kitty's notification only comes from the visible window.
[ -n "$TMUX_PANE" ] || exit 0
printf '\a' > "$(tmux display-message -p -t "$TMUX_PANE" '#{pane_tty}')"
[ "$(tmux display-message -p -t "$TMUX_PANE" '#{&&:#{window_active},#{session_attached}}')" = 1 ] && exit 0
msg=$(jq -r '.message // "Claude Code needs you"')
loc=$(tmux display-message -p -t "$TMUX_PANE" '#S:#I #W')
osascript -e 'on run argv' -e 'display notification (item 1 of argv) with title "Claude Code" subtitle (item 2 of argv)' -e 'end run' "$msg" "$loc"
