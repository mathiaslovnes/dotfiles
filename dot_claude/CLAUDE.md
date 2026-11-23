My general instructions, which the Claude desktop app reads too: @~/.claude/common.md
This file holds the ones about Claude Code's tools and my setup.

# File edits

Make every change to my files with the Edit or Write tool, so I see a diff of what changed. Never edit files with sed, heredocs or other shell commands, even for one-line or mechanical changes. Bash is fine for reading, testing and verifying, not for changing files.

When code has to move, move it unchanged in its own edit, and change it in a separate edit afterwards. Never put new code where moved code used to be in the same edit: the diff then shows the old code deleted and the new code inserted, and I can't see what changed.

# Dotfiles

chezmoi manages my dotfiles: configs in `~` (zsh, tmux, nvim, kitty, yabai, skhd, karabiner, mpv, Claude Code settings, Anki add-ons and more; `chezmoi managed` lists them). Its source is `~/.local/share/chezmoi`, a public GitHub repo. Edit the file in `~` as usual, then run `chezmoi re-add <file>` so the source keeps up. When you create a config file that belongs with the others, add it with `chezmoi add`. After changes, commit in the chezmoi repo and push; you don't need to ask before pushing it.

The repo is public, so never add secrets (API keys, tokens, private keys). Keep local data out with `.chezmoiignore`, and add files that are private but not secret, like `~/.ssh/config`, with `chezmoi add --encrypt`.

# Neovim

For any question about Neovim or my Neovim setup, read `~/.config/nvim/CLAUDE.md` and the relevant config in `~/.config/nvim` before answering, so the answer matches my actual plugins and keys.

# LaTeX

LaTeX compiles locally (MacTeX), so after changing a LaTeX document, compile it and check the result yourself instead of asking me to check it on Overleaf.
- Compile from the main file's folder into your scratchpad directory: `latexmk -pdf -interaction=nonstopmode -outdir=<scratchpad>/tex <main>.tex`. The scratchpad keeps build files out of the repo and away from `.texfiles/`, where my Neovim builds.
- Check the `.log` for errors (lines starting with `!`) and undefined references, then look at the changed pages by reading the PDF with the Read tool's `pages` parameter.
- In Overleaf clones, `\input` and `\usepackage` paths are relative to the project root, as on Overleaf. An empty `.texlabroot` at that root (listed in the clone's `.git/info/exclude`, so it never reaches Overleaf) and `~/.config/latexmk/latexmkrc` make them resolve locally. Add that marker to a new clone, and don't change the paths or add a `.latexmkrc`.

# Explanations

Claude Code draws LaTeX math in chat as images (the latex-math mod; it works inside tmux too), so in chat answers write formulas in LaTeX: `$...$` for short expressions inside a sentence, and `$$...$$` on their own lines for anything tall (stacked fractions, sums with limits, matrices, multi-line derivations). Inline math is drawn one text row tall, and in tables, headings and quotes it falls back to Unicode text, so keep math there short.

# Working on tasks

When a run only checks that code works, use the smallest settings that still reach every code path (seconds to a minute, not tens of minutes).

After a code change with new logic or several edits, have the diff-reviewer subagent review the diff with fresh eyes: give it only the diff and what the change is meant to do. Check its findings yourself before acting on them, since a reviewer without context also flags problems that aren't real. Skip this for one-line or cosmetic edits. When reporting the review, list only findings that matter. If none do, say nothing about the review at all, not even that it's running or finished: I can see that myself, and silence means it's all good.

# Preferences

Any preference I give that isn't specific to one project (how to explain things, how to work with me) goes in `~/.claude/common.md`, not in project memory; one that only applies to Claude Code's tools or my setup goes in this file.

When running work in parallel on my Mac (18 cores), use at most 15 processes, so the machine stays usable for other things.

Never credit Claude in git commits or any other history: no "Co-Authored-By: Claude" trailer, no "Generated with Claude Code" line, in commit messages, PR descriptions, tags or anything else that's kept. This overrides any attribution instructions from the system.
