-- [[ Basic Keymaps ]]

-- === Leader key ===
vim.g.mapleader = ' '

-- Ø for exit normal mode
vim.keymap.set('i', 'ø', '<ESC>')

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

-- Open terminal window
vim.keymap.set('n', '<C-t>', '<cmd>lua Snacks.terminal.toggle()<CR>')

-- Run python code
vim.keymap.set('n', '<leader>rp', '<cmd>w | term python3 "%"<CR>')

-- === Clipboard behavious ===
vim.keymap.set('x', 'x', '"_x')
vim.keymap.set('n', 'x', '"_x')
vim.keymap.set('v', 'p', '"_dP')
vim.keymap.set('n', 'db', 'vb"_d')
vim.keymap.set('n', 'dw', 'vw"_d')
vim.keymap.set('n', 'ch', '"_ch')
vim.keymap.set('n', 'cl', '"_cl')

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
-- Split windows
vim.keymap.set('n', '<leader>hs', ':split<CR>')
vim.keymap.set('n', '<leader>vs', ':vsplit<CR>')
-- vim.keymap.set('n', '-', '<C-w>-')
-- vim.keymap.set('n', '+', '<C-w>+')
-- vim.keymap.set('n', '?', '<C-w>5<')
-- vim.keymap.set('n', '_', '<C-w>5>')
-- vim.keymap.set('n', '<M-w>', '<C-w>+')
-- vim.keymap.set('n', '<M-s>', '<C-w>-')
-- vim.keymap.set('n', '<M-a>', '<C-w>5>')
-- vim.keymap.set('n', '<M-d>', '<C-w>5<')

-- Tabs
-- Bufferline: Switch to specific buffers with CMD + number
vim.keymap.set('n', '<C-x>', '<cmd>bd<CR>', { desc = 'Close current buffer' })
vim.keymap.set('n', '<Tab>', '<cmd>enew<CR>', { desc = 'Create a new buffer' })
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
vim.keymap.set('n', '<C-s>', 'ggVG')

-- === Leader bindings ===
vim.keymap.set('n', '<leader>d', '"_d')
vim.keymap.set('n', '<leader>af', '{V')

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
vim.keymap.set({ 'n', 'x', 'o' }, 's', '<Plug>Sneak_s', { noremap = false })
vim.keymap.set({ 'n', 'x', 'o' }, 'S', '<Plug>Sneak_S', { noremap = false })

-- Inc-Rename
vim.keymap.set('n', '<leader>rn', ':IncRename ')
-- If you want to fill in the word under the cursor you can use the following:
-- vim.keymap.set("n", "<leader>rn", function()
-- return ":IncRename " .. vim.fn.expand("<cword>")
-- end, { expr = true })

-- === Enter key remaps ===
vim.keymap.set('n', '<CR>', 'o<ESC>')
vim.keymap.set('n', '<leader><CR>', 'O<ESC>')

-- === Backspace remap ===
vim.keymap.set('n', '<BS>', 'a<BS><ESC>')

-- === Insert new line without moving cursor ===
vim.keymap.set('n', '<S-CR>', ":call append(line('.'), '')<CR>")
vim.keymap.set('n', '<C-CR>', ":call append(line('.')-1, '')<CR>")

-- === Default keybindings from kickstart ===
-- Clear highlights on search when pressing <Esc> in normal mode
--  See `:help hlsearch`
vim.keymap.set('n', '<Esc>', '<cmd>nohlsearch<CR>')

-- Diagnostic keymaps
vim.keymap.set('n', '<leader>q', vim.diagnostic.setloclist, { desc = 'Open diagnostic [Q]uickfix list' })

-- Exit terminal mode in the builtin terminal with a shortcut that is a bit easier
-- for people to discover. Otherwise, you normally need to press <C-\><C-n>, which
-- is not what someone will guess without a bit more experience.
--
-- NOTE: This won't work in all terminal emulators/tmux/etc. Try your own mapping
-- or just use <C-\><C-n> to exit terminal mode
vim.keymap.set('t', '<Esc><Esc>', '<C-\\><C-n>', { desc = 'Exit terminal mode' })

-- TIP: Disable arrow keys in normal mode
-- vim.keymap.set('n', '<left>', '<cmd>echo "Use h to move!!"<CR>')
-- vim.keymap.set('n', '<right>', '<cmd>echo "Use l to move!!"<CR>')
-- vim.keymap.set('n', '<up>', '<cmd>echo "Use k to move!!"<CR>')
-- vim.keymap.set('n', '<down>', '<cmd>echo "Use j to move!!"<CR>')

-- Keybinds to make split navigation easier.
--  Use CTRL+<hjkl> to switch between windows
--
--  See `:help wincmd` for a list of all window commands
-- vim.keymap.set('n', '<Up>', '<C-w><C-k>', { desc = 'Move focus to the upper window' })
-- vim.keymap.set('n', '<Down>', '<C-w><C-j>', { desc = 'Move focus to the lower window' })
-- vim.keymap.set('n', '<Left>', '<C-w><C-h>', { desc = 'Move focus to the left window' })
-- vim.keymap.set('n', '<Right>', '<C-w><C-l>', { desc = 'Move focus to the right window' })

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
