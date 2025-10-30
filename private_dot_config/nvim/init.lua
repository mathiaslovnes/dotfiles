--  NOTE: Must happen before plugins are loaded (otherwise wrong leader will be used)
vim.g.mapleader = ' '
vim.g.maplocalleader = ' '

-- Set to true if you have a Nerd Font installed and selected in the terminal
vim.g.have_nerd_font = true

-- [[ Setting options ]]
require 'options'

-- [[ Basic Keymaps ]]
require 'keymaps'

-- [[ Install `lazy.nvim` plugin manager ]]
require 'lazy-bootstrap'

-- Add to your init.lua BEFORE loading vim-jukit
vim.g.jukit_highlight_markers = 0 -- Don't highlight markers
vim.g.jukit_enable_textcell_bg_hl = 0 -- Don't highlight text cell backgrounds

-- [[ Configure and install plugins ]]
require 'lazy-plugins'

vim.g.jukit_highlight_markers = 0 -- Don't highlight markers
vim.g.jukit_enable_textcell_bg_hl = 0 -- Don't highlight text cell backgrounds

require('pyworks_divider').setup()
