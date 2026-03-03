
# Reminders
- Trying mini's split-join instead of treesj - try and remove treesj if keep

# General nvim tips & tricks

- <C-f> to enter into vim mode while in the cmdline
- Yanky plugin creates a paste register you can search (leader-Y) or scroll through (<C-N> & <C-P> for next and prev entry in register)

- <leader>bg to toggle background
- <leader>c{o/O} for adding comment below and above
- <leader>ut for undo-tree
- 'gi' goes to last place I was in insert, gI go to implementation
- gd go to definition, gD go to declaration
- Use ctrl-c to exit overlay buffers instead of esc-esc or esc-q
- Use marks: A-Z work across files (use harpoon instead), a-z are buffer-local only
- use ctrl-v/x/t to open buffers from telescope search in vertical, horizontal or in new tab, respectively
- gv selects previous selection
- Gi drops you at the last position you were in insert mode
- <C-o> and <C-i>
- Use marks - lower-case for line, upper-case for file (cheatsheet)
- Surround - { leaves a space, } does not
- gd to jump to def
- Ctrl-v for visual block mode

# Available Keybindings
- '-'
- '+'
- capital s
- Ctrl-b
- Ctrl-n
- Ctrl-m
- Ctrl-hjkl
- tab, shift-tab (cmd-esc)

# Plugins

## Snacks
- <leader>si to select icons (/emojis)

## Zoxide
- Use :Z to use zoxide to jump to directories while staying within the current buffer

## Yazi
- Ctrl-v to open vertical split
- Ctrl-x to open horizontal split

## Treesj
- <leader>m to merge lines
- <leader>jo to join lines
- <leader>S to split ( lines ) alskjfdlsakjdf

## Mini
- Use vil({' to go to prev (last) specified surrounding
- Use viq or vaq mark inside or around next quotes
- Use vib or (vab )mark inside or around next bracket

## Surround
Add surrounding: sa<motion><char>
  saiw)     - Surround word with ()
  sa2w]     - Surround 2 words with []

Delete surrounding: sd<char>
  sd)       - Delete () surrounding
  sd"       - Delete "" surrounding
  sd]       - Delete [] surrounding

Replace surrounding: sr<old><new>
  sr)"      - Replace () with ""
  sr}]      - Replace {} with []

Interactive (Visual mode):
  Select text, then:
  sa<char>  - Add surrounding to selection
  sr<char>  - Replace selection's surrounding

Suffix modifiers (find nearest):
  san)      - Add () next occurrence
  sap)      - Add () previous occurrence
  srn)"     - Replace next () with ""

Highlight surrounding: sh<char>
sh)       - Highlight () surrounding

Misc:
  sai(     - Surround inside parentheses with []

- Lots of these binds are dot-repeatable
- Can even use f for surrounding a selected piece of text in a function

## Treesitter text objects


## Keybindings to remember

## Harpoon
- <leader>a — Mark current file
- <leader>1/2/3/4 — Jump to marked files
- <leader>q/e Jump to prev/next files
- <leader>ha — Open harpoon menu to see all marks
- Delete marks using vim motions and :wq in the harpoon menu

## Treesj
Neovim plugin for splitting/joining blocks of code like arrays, hashes, statements, objects, dictionaries, etc:
- keys = { '<leader>m', '<leader>jo', '<leader>sp' }, -- [M]erge, [Jo]in, [Sp]lit



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



# To DO
- \[<Space> and \]<Space> add lines before and after cursor - obsidian
