-- lua/user/keybindings.lua

-- === Leader key ===
vim.g.mapleader = ' '

-- === Line movement bindings ===
vim.keymap.set('n', 'J', ':m .+1<CR>==')
vim.keymap.set('n', 'K', ':m .-2<CR>==')
vim.keymap.set('v', 'J', ":m '>+1<CR>gv=gv")
vim.keymap.set('v', 'K', ":m '<-2<CR>gv=gv")

-- === Leader bindings ===
vim.keymap.set('n', '<leader><space>', ':nohlsearch<CR>')
vim.keymap.set('n', '<leader>d', '"_d')
vim.keymap.set('x', 'p', '"_dP')
vim.keymap.set('n', '<leader>af', '{V')
vim.keymap.set('n', '<leader>w', '<C-w>w')

-- === Movement and scrolling ===
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

-- === Split navigation ===
vim.keymap.set('n', '<C-h>', '<C-w>h')
vim.keymap.set('n', '<C-j>', '<C-w>j')
vim.keymap.set('n', '<C-k>', '<C-w>k')
vim.keymap.set('n', '<C-l>', '<C-w>l')

-- === Visual mode indents ===
vim.keymap.set('v', '<', '<gv')
vim.keymap.set('v', '>', '>gv')

-- === Enter key remaps ===
vim.keymap.set('n', '<CR>', 'o<ESC>')
vim.keymap.set('n', '<leader><CR>', 'O<ESC>')

-- === Backspace remap ===
vim.keymap.set('n', '<BS>', 'a<BS><ESC>')
vim.keymap.set('n', '<C-x>', 'a<BS><ESC>')

-- === Insert new line without moving cursor ===
vim.keymap.set('n', '<S-CR>', ":call append(line('.'), '')<CR>")
vim.keymap.set('n', '<C-CR>', ":call append(line('.')-1, '')<CR>")
