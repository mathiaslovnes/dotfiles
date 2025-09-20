-- [[ Basic Keymaps ]]

-- === Leader key ===
vim.g.mapleader = ' '

-- Accelerated J & K motions
vim.api.nvim_set_keymap('n', 'j', '<Plug>(accelerated_jk_gj)', {})
vim.api.nvim_set_keymap('n', 'k', '<Plug>(accelerated_jk_gk)', {})

-- Change colorscheme
vim.keymap.set('n', '<leader>cs', '<cmd>Telescope colorscheme<CR>')

-- === Line movement bindings ===
vim.keymap.set('n', 'J', ':m .+1<CR>==')
vim.keymap.set('n', 'K', ':m .-2<CR>==')
vim.keymap.set('v', 'J', ":m '>+1<CR>gv=gv")
vim.keymap.set('v', 'K', ":m '<-2<CR>gv=gv")

-- === Clipboard behavious ===
vim.keymap.set('x', 'x', '"_x')
vim.keymap.set('n', 'x', '"_x')
vim.keymap.set('v', 'p', '"_dP')
vim.keymap.set('n', 'db', 'vb"_d')
vim.keymap.set('n', 'dw', 'vw"_d')
vim.keymap.set('n', 'ch', '"_ch')
vim.keymap.set('n', 'cl', '"_cl')
vim.keymap.set('n', '<leader>d', '"_d')
vim.keymap.set('v', '<leader>d', '"_d')
vim.keymap.set('n', '<leader>dd', '"_dd')
vim.keymap.set('v', '<leader>dd', '"_dd')

-- Rebind for effective replacing / pasting
vim.keymap.set('n', '<leader>p', 'viwp')
vim.keymap.set('n', '<leader>P', 'viWp')

-- Scrolling speed
vim.keymap.set('n', '<ScrollWheelUp>', '<C-Y>') -- Scroll up 1 line
vim.keymap.set('n', '<ScrollWheelDown>', '<C-E>') -- Scroll down 1 line

-- Toggle line wrapping
vim.keymap.set('n', '<leader>lw', '<cmd>set wrap!<CR>')

-- Stay in visual mode when indenting
vim.keymap.set('v', '<', '<gv')
vim.keymap.set('v', '>', '>gv')

-- Shift + backspace to delete prev word
vim.keymap.set('i', '<M-BS>', '<C-w>')

-- === Split navigation ===
vim.keymap.set('n', '<C-w><C-h>', '<C-w>h')
vim.keymap.set('n', '<C-w><C-j>', '<C-w>j')
vim.keymap.set('n', '<C-w><C-k>', '<C-w>k')
vim.keymap.set('n', '<C-w><C-l>', '<C-w>l')

-- Adjust window size
vim.keymap.set('n', '<C-w><C-s>', '<C-w>-')
vim.keymap.set('n', '<C-w><C-w>', '<C-w>+')
vim.keymap.set('n', '<C-w><C-a>', '<C-w>5>')
vim.keymap.set('n', '<C-w>>C-d>', '<C-w>5<')
vim.keymap.set('n', '<leader>=', '<cmd>wincmd=<CR>')

-- Split windows
vim.keymap.set('n', '<leader>hs', ':split<CR>')
vim.keymap.set('n', '<leader>vs', ':vsplit<CR>')

vim.keymap.set('n', '<leader>zz', function()
  local win = vim.api.nvim_get_current_win()
  local wwidth = vim.api.nvim_win_get_width(win)
  local wheight = vim.api.nvim_win_get_height(win)

  local tab_width = vim.o.columns
  local tab_height = vim.o.lines - vim.o.cmdheight

  local focused = wwidth >= tab_width * 0.9 and wheight >= tab_height * 0.9
  if focused then
    vim.cmd 'wincmd =' --equalize all win size
  else
    vim.cmd 'wincmd |'
    vim.cmd 'wincmd _'
  end
end)

-- Tabs
-- Bufferline: Switch to specific buffers with CMD + number
vim.keymap.set('n', '<C-t>', '<Nop>', { noremap = true, silent = true, desc = 'Unbind C-b' })
vim.keymap.set('n', 'Q', '<cmd>bd<CR>', { desc = 'Close current buffer' })
-- vim.keymap.set('n', '<Tab>', '<cmd>enew<CR>', { desc = 'Create a new buffer' })
vim.keymap.set('n', '<C-1>', '<cmd>BufferLineGoToBuffer 1<CR>', { desc = 'Go to buffer 1' })
vim.keymap.set('n', '<C-2>', '<cmd>BufferLineGoToBuffer 2<CR>', { desc = 'Go to buffer 2' })
vim.keymap.set('n', '<C-3>', '<cmd>BufferLineGoToBuffer 3<CR>', { desc = 'Go to buffer 3' })
vim.keymap.set('n', '<C-5>', '<cmd>BufferLineGoToBuffer 5<CR>', { desc = 'Go to buffer 5' })
vim.keymap.set('n', '<C-6>', '<cmd>BufferLineGoToBuffer 6<CR>', { desc = 'Go to buffer 6' })
vim.keymap.set('n', '<C-7>', '<cmd>BufferLineGoToBuffer 7<CR>', { desc = 'Go to buffer 7' })
vim.keymap.set('n', '<C-8>', '<cmd>BufferLineGoToBuffer 8<CR>', { desc = 'Go to buffer 8' })
vim.keymap.set('n', '<C-9>', '<cmd>BufferLineGoToBuffer 9<CR>', { desc = 'Go to buffer 9' })
vim.keymap.set('n', '<C-e>', '<cmd>BufferLineCycleNext<CR>', { desc = 'Next buffer' })
vim.keymap.set('n', '<C-q>', '<cmd>BufferLineCyclePrev<CR>', { desc = 'Previous buffer' })

-- Mark entire file
vim.keymap.set({ 'n', 'x' }, '<C-s>', 'ggVG')

-- === Movement and scrolling ==
vim.keymap.set('n', '<C-u>', '<C-u>zz')
vim.keymap.set('n', '<C-d>', '<C-d>zz')
vim.keymap.set('n', 'n', 'nzzzv')
vim.keymap.set('n', 'N', 'Nzzzv')
vim.keymap.set('n', 'G', 'Gzz')
vim.keymap.set('n', 'gg', 'ggzz')

-- === Cursor and line remaps ===
vim.keymap.set('n', 'U', '~')
vim.keymap.set('n', '<C-j>', '5j')
vim.keymap.set('n', '<C-k>', '5k')
vim.keymap.set('n', 'H', '^')
vim.keymap.set('n', 'L', '$')

-- === Visual mode indents ===
vim.keymap.set('v', '<', '<gv')
vim.keymap.set('v', '>', '>gv')

-- === Enter key remaps ===-
vim.keymap.set('n', '<CR>', 'o<ESC>')
vim.keymap.set('n', '<leader><CR>', 'O<ESC>')

-- === Backspace remap ===
vim.keymap.set('n', '<BS>', 'i<BS><right><ESC>')
vim.keymap.set('n', '<M-BS>', 'a<C-w><ESC>')

-- === Insert new line without moving cursor ===
vim.keymap.set('n', '<S-CR>', ":call append(line('.'), '')<CR>")
vim.keymap.set('n', '<C-CR>', ":call append(line('.')-1, '')<CR>")

-- vim.keymap.set('n', ']<Space>', 'x', { noremap = false }) -- Triggers the plugin's mapping for below
-- vim.keymap.set('n', '[<Space>', 'X',  { noremap = false }) -- Triggers the plugin's mapping for above

-- ==== Plugin-specific bindings ===

-- CsvView
vim.keymap.set('n', '<leader>cv', '<cmd>CsvViewToggle delimiter=, display_mode=border header_lnum=1<CR>')

-- LazyGit
vim.keymap.set('n', '<leader>g', '<cmd>LazyGit<CR>')

-- Git diffview
vim.keymap.set('n', '<leader>gdo', ':DiffviewOpen<CR>', { desc = 'Open Diffview' })
vim.keymap.set('n', '<leader>gdc', ':DiffviewClose<CR>', { desc = 'Close Diffview' })
vim.keymap.set('n', '<leader>gdh', ':DiffviewFileHistory %<CR>', { desc = 'File History' })
vim.keymap.set('n', '<leader>gdr', ':DiffviewRefresh<CR>', { desc = 'Refresh Diffview' })

-- Sneak
vim.keymap.set('n', 'f', '<Plug>Sneak_f')
vim.keymap.set('n', 'F', '<Plug>Sneak_F')
vim.keymap.set('n', 't', '<Plug>Sneak_t')
vim.keymap.set('n', 'T', '<Plug>Sneak_T')
vim.keymap.set({ 'n', 'x', 'o' }, 'ø', '<Plug>Sneak_s', { noremap = false })
vim.keymap.set({ 'n', 'x', 'o' }, 'Ø', '<Plug>Sneak_S', { noremap = false })

-- Yazi
vim.keymap.set('n', '<leader>y', '<cmd>Yazi<CR>')

-- Inc-Rename
vim.keymap.set('n', '<leader>rn', ':IncRename ')

-- === Default keybindings from kickstart ===
-- Clear highlights on search when pressing <Esc> in normal mode
--  See `:help hlsearch`
vim.keymap.set('n', '<Esc>', '<cmd>nohlsearch<CR>')

-- Diagnostic keymaps
vim.keymap.set('n', '<leader>q', vim.diagnostic.setloclist, { desc = 'Open diagnostic [Q]uickfix list' })

-- Exit terminal mode in the builtin terminal with a shortcut that is a bit easier
-- for people to discover. Otherwise, you normally need to press <C-\><C-n>, which
-- is not what someone will guess without a bit more experience.
-- NOTE: This won't work in all terminal emulators/tmux/etc. Try your own mapping
-- or just use <C-\><C-n> to exit terminal mode
vim.keymap.set('t', '<Esc><Esc>', '<C-\\><C-n>', { desc = 'Exit terminal mode' })

-- [[ Basic Autocommands ]]
--  See `:help lua-guide-autocommands`

-- Highlight when yanking (copying) text
--  Try it with `yap` in normal mode
--  See `:help vim.hl.on_yank()`
vim.api.nvim_create_autocmd('TextYankPost', {
  desc = 'Highlight when yanking (copying) text',
  group = vim.api.nvim_create_augroup('kickstart-highlight-yank', { clear = true }),
  callback = function()
    vim.hl.on_yank()
  end,
})

-- vim: ts=2 sts=2 sw=2 et
