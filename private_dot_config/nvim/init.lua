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

-- Add BEFORE loading vim-jukit
vim.g.jukit_highlight_markers = 0 -- Don't highlight markers
vim.g.jukit_enable_textcell_bg_hl = 0 -- Don't highlight text cell backgrounds
vim.g.jukit_notify_output = 1 -- Only show important messages

-- [[ Configure and install plugins ]]
require 'lazy-plugins'

-- Add AFTER loading colorscheme
-- Changes pythong documentation string color from blue to green
vim.api.nvim_set_hl(0, '@string.documentation.python', { fg = '#a6e3a1' })

require('pyworks_divider').setup()

vim.api.nvim_create_autocmd('FileType', {
  pattern = 'python',
  callback = function()
    vim.opt_local.conceallevel = 0 -- Disable all concealment in Python files
  end,
})

-- Function to make rainbow highlights bold
local function make_rainbows_bold()
  for i = 1, 6 do
    local rainbow = vim.api.nvim_get_hl(0, { name = 'rainbow' .. i })
    if rainbow and next(rainbow) ~= nil then
      rainbow.bold = true
      vim.api.nvim_set_hl(0, 'rainbow' .. i, rainbow)
    end
  end
end

-- Force bold headers - runs on multiple events
vim.api.nvim_create_autocmd({ 'BufEnter', 'FileType', 'BufWritePost', 'TextChanged', 'InsertLeave' }, {
  pattern = 'python',
  callback = function()
    vim.schedule(make_rainbows_bold)
  end,
})

-- Run it immediately for already-open buffers
if vim.bo.filetype == 'python' then
  vim.schedule(make_rainbows_bold)
end
