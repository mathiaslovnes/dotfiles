---@diagnostic disable: undefined-global
-- [[ Deleted keymaps ]]
vim.keymap.set('n', 'gf', '<Nop>', { noremap = true }) -- Remove "Go to file under cursor"
vim.keymap.set('n', 'gcc', '<Nop>', { noremap = true, silent = true, nowait = true }) -- Remove "Comment line"
vim.keymap.set('n', 'gc', '<Nop>', { noremap = true, silent = true, nowait = true }) -- Remove "Comment line"

-- [[ Basic Keymaps ]]

-- === Leader key ===
vim.g.mapleader = ' '

-- === Div ===
-- Open file/link under cursor with 'gx'
vim.keymap.set('n', 'gu', function()
  vim.ui.open(vim.fn.expand '<cfile>')
end, { desc = 'Open file or URL under cursor' })

-- Open lazy
vim.keymap.set('n', '<leader>L', '<cmd>Lazy<CR>')

-- Copy current working directory
vim.keymap.set('n', '<leader>cwd', '<cmd>let @+ = getcwd()<CR>')

-- Accelerated J & K motions
vim.api.nvim_set_keymap('n', 'j', '<Plug>(accelerated_jk_gj)', {})
vim.api.nvim_set_keymap('n', 'k', '<Plug>(accelerated_jk_gk)', {})

-- Show documentation on hover
vim.keymap.set('n', 'gh', vim.lsp.buf.hover, { desc = 'Show hover documentation' })

-- Change colorscheme
vim.keymap.set('n', '<leader>cs', '<cmd>Telescope colorscheme<CR>')

-- === Line movement bindings ===
vim.keymap.set('n', 'J', ':m .+1<CR>==')
vim.keymap.set('n', 'K', ':m .-2<CR>==')
vim.keymap.set('v', 'J', "<Esc><cmd>'<,'>m '>+1<CR>gv=gv", { silent = true })
vim.keymap.set('v', 'K', "<Esc><cmd>'<,'>m '<-2<CR>gv=gv", { silent = true })

-- === Clipboard behaviour ===
vim.keymap.set('x', 'x', '"_x')
vim.keymap.set('n', 'x', '"_x')
vim.keymap.set('v', 'p', '"_dp')
vim.keymap.set('v', 'P', '"_dP')
vim.keymap.set('n', 'db', 'vb"_d')
vim.keymap.set('n', 'ch', '"_ch')
vim.keymap.set('n', 'cl', '"_cl')
vim.keymap.set('n', '<leader>d', '"_d')
vim.keymap.set('v', '<leader>d', '"_d')
vim.keymap.set('n', '<leader>dd', '"_dd')
vim.keymap.set('v', '<leader>dd', '"_dd')

-- Rebind for effective replacing / pasting
vim.keymap.set('n', '<leader>p', 'viw"_dP', { desc = 'viw"_dP', noremap = true, nowait = true })
vim.keymap.set('n', '<leader>P', 'viW"_dP', { desc = 'viW"_dP', noremap = true, nowait = true })

-- Toggle line wrapping
vim.keymap.set('n', '<leader>lw', '<cmd>set wrap!<CR>')

-- Make comment below/above
vim.keymap.set('n', '<leader>co', 'o<esc>Vcx<esc><cmd>normal gcc<cr>fxa<bs>', { desc = 'Add Comment Below' })
vim.keymap.set('n', '<leader>cO', 'O<esc>Vcx<esc><cmd>normal gcc<cr>fxa<bs>', { desc = 'Add Comment Above' })

-- === Indenting ===
-- Stay in visual mode when indenting
vim.keymap.set('v', '<', '<gv')
vim.keymap.set('v', '>', '>gv')

-- Visual mode indenting/unindenting
vim.keymap.set('v', '<Tab>', '>gv', { noremap = true, silent = true })
vim.keymap.set('v', '<BS>', '<gv', { noremap = true, silent = true })

-- Shift/ctrl + backspace to delete prev word
vim.keymap.set('i', '<M-BS>', '<C-w>')
vim.keymap.set('i', '<C-BS>', '<C-w>')
vim.keymap.set('c', '<M-BS>', '<C-w>') -- cmd mode
vim.keymap.set('c', '<C-BS>', '<C-w>') -- cmd mode

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
-- Equalize all window size
vim.keymap.set('n', '<leader>=', '<cmd>wincmd=<CR>')
-- Toggle equaling all window sizes
-- vim.keymap.set('n', '<leader>zz', function()
--   local win = vim.api.nvim_get_current_win()
--   local wwidth = vim.api.nvim_win_get_width(win)
--   local wheight = vim.api.nvim_win_get_height(win)
--
--   local tab_width = vim.o.columns
--   local tab_height = vim.o.lines - vim.o.cmdheight
--
--   local focused = wwidth >= tab_width * 0.9 and wheight >= tab_height * 0.9
--   if focused then
--     vim.cmd 'wincmd =' --equalize all win size
--   else
--     vim.cmd 'wincmd |'
--     vim.cmd 'wincmd _'
--   end
-- end)

-- Split windows
vim.keymap.set('n', '<leader>hs', '<cmd>split<CR>')
vim.keymap.set('n', '<leader>vs', '<cmd>vsplit<CR>')

-- Close split
vim.keymap.set('n', '<leader>cs', '<cmd>close<CR>', { desc = '[C]lose [S]plit' })

-- Buffers
-- vim.keymap.set('n', 'Q', function()
--   require('mini.bufremove').delete(0, false)
-- end, { desc = 'Delete buffer' })
vim.keymap.set('n', 'Q', function()
  local buf = vim.api.nvim_get_current_buf()
  if vim.bo[buf].modified then
    local choice = vim.fn.confirm('Save changes?', '&Yes\n&No\n&Cancel')
    if choice == 1 then -- Yes
      vim.cmd 'write'
      require('mini.bufremove').delete(buf)
    elseif choice == 2 then -- No
      require('mini.bufremove').delete(buf, true) -- force
    end
    -- choice == 3 (Cancel): do nothing
  else
    require('mini.bufremove').delete(buf)
  end
end, { desc = 'Delete buffer (prompt to save)' })

-- vim.keymap.set('n', 'Q', '<cmd>bd<CR>', { desc = 'Close current buffer' })
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
vim.keymap.set({ 'n', 'x' }, '<M-a>', 'ggVG')

-- === Movement and scrolling ==
vim.keymap.set('n', '<C-u>', '<C-u>zz')
vim.keymap.set('n', '<C-d>', '<C-d>zz')
vim.keymap.set('n', 'n', 'nzzzv')
vim.keymap.set('n', 'N', 'Nzzzv')
vim.keymap.set('n', 'G', 'Gzz')
vim.keymap.set('n', 'gg', 'ggzz')

-- === Cursor and line remaps ===
vim.keymap.set('n', 'U', '~')
vim.keymap.set('n', 'H', '^')
vim.keymap.set('v', 'H', '^')
vim.keymap.set('n', 'L', '$')
vim.keymap.set('v', 'L', '$')

-- === Enter key remaps ===-
-- vim.keymap.set('n', '<CR>', 'o<ESC>')
-- vim.keymap.set('n', '<leader><CR>', 'O<ESC>')
vim.keymap.set('n', '<CR>', "<cmd>silent call append(line('.'), '')<CR>")
vim.keymap.set('n', '<leader><CR>', "<cmd>silent call append(line('.')-1, '')<CR>")

-- === Backspace remap ===
vim.keymap.set('n', '<BS>', 'i<BS><right><ESC>')
vim.keymap.set('n', '<M-BS>', 'a<C-w><ESC>')

-- === Insert new line without moving cursor ===

-- ==== Plugin-specific bindings ===
-- CsvView
vim.keymap.set('n', '<leader>cv', '<cmd>CsvViewToggle delimiter=, display_mode=border header_lnum=1<CR>')

-- Git diffview
vim.keymap.set('n', '<leader>gdo', ':DiffviewOpen<CR>', { desc = 'Open Diffview' })
vim.keymap.set('n', '<leader>gdc', ':DiffviewClose<CR>', { desc = 'Close Diffview' })
vim.keymap.set('n', '<leader>gdh', ':DiffviewFileHistory %<CR>', { desc = 'File History' })
vim.keymap.set('n', '<leader>gdr', ':DiffviewRefresh<CR>', { desc = 'Refresh Diffview' })

-- Yazi
vim.keymap.set('n', '<leader>y', '<cmd>Yazi<CR>')

-- Inc-Rename
vim.keymap.set('n', '<leader>rn', function()
  return ':IncRename ' .. vim.fn.expand '<cword>'
end, { expr = true })

-- === Default keybindings from kickstart ===
-- Clear highlights on search when pressing <Esc> in normal mode
--  See `:help hlsearch`
vim.keymap.set('n', '<Esc>', '<cmd>nohlsearch<CR>')

-- Diagnostic keymaps
vim.keymap.set('n', '<leader>qf', vim.diagnostic.setloclist, { desc = 'Open diagnostic [Q]uick[f]ix list' })

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
