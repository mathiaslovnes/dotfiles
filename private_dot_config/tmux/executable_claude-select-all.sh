#!/bin/sh
# Cmd+A in a Claude Code pane (tmux.conf): select the whole prompt with vim mode's gg V G, then d deletes it,
# c replaces it and y copies it. The mode comes from the label under the prompt: INSERT needs Esc first, sent
# with a pause so Claude doesn't read Esc+g as Alt+g; NORMAL has no label and gets no Esc, since a stray Esc
# could interrupt Claude while it works; an existing VISUAL selection is left alone.
pane=$1
footer=$(tmux capture-pane -p -t "$pane" | grep -v '^[[:space:]]*$' | tail -n 6)
case $footer in
  *"-- VISUAL"*) exit 0 ;;
  *"-- INSERT --"*) tmux send-keys -t "$pane" Escape; sleep 0.05 ;;   # 0.03 is too short
esac
for k in g g V G; do   # one send-keys each: sent together, Claude dropped the G
  tmux send-keys -t "$pane" "$k"
done
