-- [[ Setting options ]]
-- === Basic settings ===
local opt = vim.opt
opt.number = true
opt.relativenumber = true
opt.number = true
opt.clipboard = 'unnamedplus'
opt.hlsearch = true
opt.incsearch = true
opt.termguicolors = true
opt.tabstop = 2
opt.shiftwidth = 2
opt.expandtab = true
opt.smartindent = true
opt.autoindent = true
opt.textwidth = 120
opt.scrolloff = 15
opt.cursorline = false
opt.guicursor = 'n-v-c:block,i:ver25,r-cr:hor20'
opt.foldenable = false    -- don't fold automatically
opt.foldmethod = 'manual' -- only fold manually
opt.foldlevel = 99        -- open all folds

opt.wildmenu = true
opt.wildoptions = 'pum'
opt.pumheight = 15

-- These are global fold configuration options required for nvim-ufo
opt.foldcolumn = '1'    -- Show fold column (0 to disable)
opt.foldlevel = 99      -- Start with all folds open (required for ufo providers)
opt.foldlevelstart = 99 -- Keep all folds open on file open
opt.foldenable = true   -- Enable folding
opt.fillchars = { eob = ' ', fold = ' ', foldopen = '▼', foldsep = ' ', foldclose = '▶' }

-- Prevent vim-visual-multi artifacts from appearing in statusline
vim.g.VM_set_statusline = 0

-- This keeps it always 1 column wide regardless of signs appearing/disappearing, so it won't jump around.
-- opt.signcolumn = 'yes'
-- vim.o.signcolumn = 'yes'
opt.signcolumn = 'yes:1'

-- See `:help vim.o`
-- NOTE: You can change these options as you wish!
--  For more options, you can see `:help option-list`

-- Enable mouse mode, can be useful for resizing splits for example!
opt.mouse = 'a'

-- Don't show the mode, since it's already in the status line
-- vim.o.showmode = false

-- Sync clipboard between OS and Neovim.
--  Schedule the setting after `UiEnter` because it can increase startup-time.
--  Remove this option if you want your OS clipboard to remain independent.
--  See `:help 'clipboard'`
vim.schedule(function()
  vim.o.clipboard = 'unnamedplus'
end)

-- Enable break indent
vim.o.breakindent = true

-- Save undo history
vim.o.undofile = true

-- Case-insensitive searching UNLESS \C or one or more capital letters in the search term
vim.o.ignorecase = true
vim.o.smartcase = true

-- Decrease update time
vim.o.updatetime = 50

-- Decrease mapped sequence wait time
vim.o.timeoutlen = 300

-- Configure how new splits should be opened
vim.o.splitright = true
vim.o.splitbelow = true

-- Sets how neovim will display certain whitespace characters in the editor.
--  See `:help 'list'`
--  and `:help 'listchars'`
--
--  Notice listchars is set using `vim.opt` instead of `vim.o`.
--  It is very similar to `vim.o` but offers an interface for conveniently interacting with tables.
--   See `:help lua-options`
--   and `:help lua-options-guide`
vim.o.list = true
vim.opt.listchars = { tab = '» ', trail = '·', nbsp = '␣' }

-- Preview substitutions live, as you type!
vim.o.inccommand = 'split'

-- if performing an operation that would fail due to unsaved changes in the buffer (like `:q`),
-- instead raise a dialog asking if you wish to save the current file(s)
-- See `:help 'confirm'`
vim.o.confirm = true
