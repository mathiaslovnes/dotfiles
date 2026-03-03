--  NOTE: Must happen before plugins are loaded (otherwise wrong leader will be used)
vim.g.mapleader = ' '
vim.g.maplocalleader = ' '

-- Fix vim-jukit highlighting
vim.g.jukit_highlight_markers = 0 -- Don't highlight markers
vim.g.jukit_enable_textcell_bg_hl = 0 -- Don't highlight text cell backgrounds
vim.g.jukit_notify_output = 1 -- Only show important messages

vim.opt.switchbuf = 'useopen'
-- vim.opt.switchbuf = { 'useopen', 'uselast', 'usetab' } -- Jump to existing in any tab

-- Set to true if you have a Nerd Font installed and selected in the terminal
vim.g.have_nerd_font = true

-- Setting options
require 'options'

-- Add keymaps after loading plugins so deletions overwrite it
-- Basic Keymaps
require 'keymaps'

-- Install `lazy.nvim` plugin manager
require 'lazy-bootstrap'

-- Configure and install plugins
require 'lazy-plugins'

-- Fix cell divider highlighting for vim-jukit
require 'jukit_dividers'

-- Load autocmds
require 'autocmds'
