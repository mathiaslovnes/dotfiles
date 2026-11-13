#!/usr/bin/env python3
# Even out the panes of a tmux window at every level of its layout, like Vim's Ctrl-w = (prefix =).
# tmux's own select-layout -E only spreads panes that sit next to each other as single panes, so a pane
# beside a split group keeps its size. This rewrites the window's layout (JSON since tmux 3.8) with even
# sizes and applies it.
# Usage: equalize.py [target-window]
import json
import subprocess
import sys


def even(cell):
    """Give the cell's children equal shares of its size (one border column/row between them), recursively.
    Cell types: "h" holds children side by side, "v" stacked, "p" is a pane."""
    kids = cell.get('c')
    if not kids:
        return
    side_by_side = cell['t'] == 'h'
    total = (cell['w'] if side_by_side else cell['h']) - (len(kids) - 1)
    base, extra = divmod(total, len(kids))
    pos = cell['x'] if side_by_side else cell['y']
    for n, kid in enumerate(kids):
        size = base + (1 if n < extra else 0)
        if side_by_side:
            kid.update(x=pos, y=cell['y'], w=size, h=cell['h'])
        else:
            kid.update(x=cell['x'], y=pos, w=cell['w'], h=size)
        pos += size + 1
        even(kid)


target = ['-t', sys.argv[1]] if len(sys.argv) > 1 else []
layout = json.loads(subprocess.check_output(['tmux', 'display-message', '-p', *target, '#{window_layout}'], text=True))
even(layout['L'])
subprocess.run(['tmux', 'select-layout', *target, json.dumps(layout, separators=(',', ':'))], check=True)
