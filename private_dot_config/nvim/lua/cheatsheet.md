# Keybindings / motions

# Ideas

# General nvim tips & tricks
- use ctrl-v/x/t to open buffers from telescope search in vertical, horizontal or in new tab, respectively
- Gv selects previous selection
- Cc instead of ddO
- Gi drops you at the last position you were in insert mode
- <C-o> and <C-i>
- Use marks - lower-case for line, upper-case for file (cheatsheet)
- Surround - { leaves a space, } does not
- gd to jump to def
- Ctrl-v for visual block mode, for example:
if you have a vertical list of numbers, select them all, and hit g-ctrl-a/x to increment/decrement
them proportional to their line height
Or, if you want to add '-' to the beginning of multiple lines, select the beginning/end, add what
you want by hitting I, hit escape and then it will apply to all lines

## Available Keybindings
- '-'
- '+'
- capital s
- capital x
- Ctrl-o
- Ctrl-b
- Ctrl-n
- Ctrl-m
- Ctrl-hjkl



## Use Aerial for navigating files 

**Purposes**: Shows a symbol outline / code structure for your file.
**Features**:
- Lists functions, classes, variables, and other symbols in a sidebar or floating window.
- Works with treesitter, LSP, or ctags to detect symbols.
- Lets you jump directly to a symbol by selecting it.
- Can show symbols nested hierarchically, like modules → functions → inner functions.
- Very similar to VSCode’s “Outline” panel but in Neovim.
**Bind**: <leader>n - for 'navigating' - Note: uses snacks integration - change the bottom of
aerial.lua for the side-panel view




## telescope
- ctrl v for vertical split
- ctrl x for horizontal split

## Neo-tree
- backspace to view parent dir
- "." for making selected dir the root dir


## Zoxide
use z to navigate directories



# To DO

- [<Space> and ]<Space> add lines before and after cursor - obsidian
- https://youtu.be/ZqPpBfiX9ws?si=JK3NCy8goRqJ1-kY Lsp python venv
