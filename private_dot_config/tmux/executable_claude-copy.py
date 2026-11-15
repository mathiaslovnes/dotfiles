#!/usr/bin/env python3
# Cmd+C in a Claude Code pane when kitty has no selection of its own (tmux.conf, User1): copy the prompt's vim
# visual selection to the clipboard, or the whole prompt when nothing is selected. Claude Code keeps visual-mode
# yanks in its own register, so this reads the prompt off the screen: it's the box between the last two ───
# rules, and a visual selection is drawn in reverse video.
# Usage: claude-copy.py <pane-id>
import re
import subprocess
import sys

pane = sys.argv[1]
width = int(subprocess.check_output(['tmux', 'display-message', '-p', '-t', pane, '#{pane_width}'], text=True))
screen = subprocess.check_output(['tmux', 'capture-pane', '-p', '-e', '-t', pane], text=True).split('\n')

SGR = re.compile(r'\x1b\[([0-9;:]*)m')


def styled(line):
    """The line's characters as (char, reverse, dim) after following its SGR codes"""
    out, reverse, dim, pos = [], False, False, 0
    for m in list(SGR.finditer(line)) + [None]:
        end = m.start() if m else len(line)
        out += [(ch, reverse, dim) for ch in re.sub(r'\x1b\[[0-9;:?]*[A-Za-z]', '', line[pos:end])]
        if not m:
            break
        params = (m[1] or '0').split(';')
        i = 0
        while i < len(params):
            p = params[i]
            if p in ('38', '48', '58'):  # colors: skip their arguments, which may contain 7
                i += 3 if params[i + 1:i + 2] == ['5'] else 5
                continue
            if p in ('0', ''):
                reverse = dim = False
            elif p == '7':
                reverse = True
            elif p == '27':
                reverse = False
            elif p == '2':
                dim = True
            elif p == '22':
                dim = False
            i += 1
        pos = m.end()
    return out


def is_rule(line):
    text = SGR.sub('', line).strip()
    return len(text) > width * 0.8 and set(text) == {'─'}


rules = [n for n, line in enumerate(screen) if is_rule(line)]
if len(rules) < 2:
    sys.exit()
top, bottom = rules[-2], rules[-1]
rows = [styled(line)[2:] for line in screen[top + 1:bottom]]  # drop the "❯ " / "  " prefix
mode = SGR.sub('', screen[bottom + 1]) if bottom + 1 < len(screen) else ''
visual = '-- VISUAL' in mode

texts = [''.join(ch for ch, _, _ in row).rstrip() for row in rows]
if visual:
    parts = [''.join(ch for ch, rev, _ in row if rev) for row in rows]
    span = [n for n, part in enumerate(parts) if part]
    parts = [part if part.strip() else '' for part in parts]  # a selected blank line is drawn as one space
else:
    # an empty prompt shows a dimmed hint; the cursor's reverse-video cell is the only part not dimmed
    shown = [dim for row in rows for ch, rev, dim in row if ch.strip() and not rev]
    parts = [] if shown and all(shown) else texts
    span = [n for n, part in enumerate(parts) if part.strip()]
if not span:
    sys.exit()

# Claude wraps long lines at a space and drops it: a row continues on the next one when the next row's first
# word would not have fitted after it. Other rows, blank ones included, are separate lines.
copied = parts[span[0]]
for n in range(span[0] + 1, span[-1] + 1):
    next_word = texts[n].split(' ')[0]
    soft = texts[n - 1] and texts[n] and len(texts[n - 1]) + 1 + len(next_word) > width - 2
    copied += (' ' if soft else '\n') + parts[n]

if copied:
    subprocess.run(['pbcopy'], input=copied, text=True)
    what = 'selection' if visual else 'prompt'
    subprocess.run(['tmux', 'display-message', '-t', pane, '-d', '1500', f'Copied {what} ({len(copied)} characters)'])
