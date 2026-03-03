---@diagnostic disable: undefined-global

-- ===================================================================
-- Leader & Globals
-- ===================================================================

vim.g.mapleader = ' '

-- ===================================================================
-- Navigation & Motions
-- ===================================================================

-- Accelerated J & K motions
vim.api.nvim_set_keymap('n', 'j', '<Plug>(accelerated_jk_gj)', {})
vim.api.nvim_set_keymap('n', 'k', '<Plug>(accelerated_jk_gk)', {})

-- Beginning / end of line
vim.keymap.set('n', 'H', '^')
vim.keymap.set('v', 'H', '^')
vim.keymap.set('n', 'L', '$')
vim.keymap.set('v', 'L', '$')

-- Center cursor after jumps
vim.keymap.set('n', '<C-d>', '<C-d>zz')
vim.keymap.set('n', 'n', 'nzzzv')
vim.keymap.set('n', 'N', 'Nzzzv')
vim.keymap.set('n', 'G', 'Gzz')
vim.keymap.set('n', 'gg', 'ggzz')

-- ===================================================================
-- Editing
-- ===================================================================

-- Backspace remaps
vim.keymap.set('n', '<BS>', 'i<BS><right><ESC>')
vim.keymap.set('n', '<M-BS>', 'a<C-w><ESC>')
vim.keymap.set('i', '<M-BS>', '<C-w>')
vim.keymap.set('i', '<C-BS>', '<C-w>')
vim.keymap.set('c', '<M-BS>', '<C-w>') -- cmd mode
vim.keymap.set('c', '<C-BS>', '<C-w>') -- cmd mode

-- Insert new lines without entering insert mode
vim.keymap.set('n', '<CR>', 'o<ESC>')
vim.keymap.set('n', '<leader><CR>', 'O<ESC>')
-- Insert new line without moving cursor
-- vim.keymap.set('n', '<CR>', "<cmd>silent call append(line('.'), '')<CR>")
-- vim.keymap.set('n', '<leader><CR>', "<cmd>silent call append(line('.')-1, '')<CR>")

-- Move lines up/down
vim.keymap.set('n', 'J', '<cmd>m .+1<CR>==', { silent = true })
vim.keymap.set('n', 'K', '<cmd>m .-2<CR>==', { silent = true })
vim.keymap.set('v', 'J', "<Esc><cmd>'<,'>m '>+1<CR>gv=gv", { silent = true })
vim.keymap.set('v', 'K', "<Esc><cmd>'<,'>m '<-2<CR>gv=gv", { silent = true })

-- Toggle case
vim.keymap.set('n', 'U', '~')

-- Visual mode indenting/unindenting
vim.keymap.set('v', '<', '<gv')
vim.keymap.set('v', '>', '>gv')
vim.keymap.set('v', '<Tab>', '>gv', { noremap = true, silent = true })
vim.keymap.set('v', '<BS>', '<gv', { noremap = true, silent = true })

-- Make comment below/above
vim.keymap.set('n', '<leader>co', 'oX<esc><cmd>lua MiniComment.toggle_lines(vim.fn.line("."), vim.fn.line("."))<cr>fXxa', { desc = 'Add Comment Below' })
vim.keymap.set('n', '<leader>cO', 'OX<esc><cmd>lua MiniComment.toggle_lines(vim.fn.line("."), vim.fn.line("."))<cr>fXxa', { desc = 'Add Comment Above' })

-- ===================================================================
-- Clipboard & Yanking
-- ===================================================================

-- Delete without yanking
vim.keymap.set({ 'n', 'v' }, 'x', '"_x')
vim.keymap.set('n', 'ch', '"_ch')
vim.keymap.set('n', 'cl', '"_cl')

vim.keymap.set({ 'n', 'v' }, 'p', '"_d<Plug>(YankyPutAfter)')
vim.keymap.set({ 'n', 'v' }, 'P', '"_d<Plug>(YankyPutBefore)')
vim.keymap.set({ 'n', 'v' }, '<leader>d', '"_d')

-- Yank to end/beginning of line
vim.keymap.set('n', 'yL', 'y$', { nowait = true, desc = 'Yank to end of line' })
vim.keymap.set('n', 'yH', 'y0', { nowait = true, desc = 'Yank to beginning of line' })

-- ===================================================================
-- Buffers & Windows
-- ===================================================================

-- Delete buffer (prompt to save if modified)
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

-- Switch to specific buffers by index (cmd+123...)
for i = 1, 9 do
  vim.keymap.set('n', '\x1b' .. i, '<cmd>BufferLineGoToBuffer ' .. i .. '<cr>')
end

-- Cycle through buffers
vim.keymap.set('n', '<C-q>', '<cmd>BufferLineCyclePrev<CR>', { desc = 'Previous buffer' })
vim.keymap.set('n', '<C-e>', '<cmd>BufferLineCycleNext<CR>', { desc = 'Next buffer' })

-- Split windows
vim.keymap.set('n', '<leader>hs', '<cmd>split<CR>', { desc = 'Horizontal split' })
vim.keymap.set('n', '<leader>vs', '<cmd>vsplit<CR>', { desc = 'Vertical split' })
vim.keymap.set('n', '<leader>cs', '<cmd>close<CR>', { desc = '[C]lose [S]plit' })
vim.keymap.set('n', '<leader>=', '<cmd>wincmd=<CR>', { desc = 'Equalize window sizes' })

-- ===================================================================
-- Misc
-- ===================================================================

-- Mark entire file
vim.keymap.set({ 'n', 'x' }, '<M-a>', 'ggVG')
-- vim.keymap.set({ 'n', 'x' }, '<C-s>', 'ggVG')

-- Open link under cursor with 'gx'
vim.keymap.set('n', 'gu', function()
  vim.ui.open(vim.fn.expand '<cfile>')
end, { desc = 'Open file or URL under cursor' })

-- Open file under cursor
vim.keymap.set('n', '<leader>gf', 'gF', { noremap = true, desc = 'Go to file under cursor' })

-- Open lazy
vim.keymap.set('n', '<leader>L', '<cmd>Lazy<CR>')

-- Open messages
vim.keymap.set('n', '<leader>M', '<cmd>messages<CR>')

-- Folds
vim.keymap.set('n', 'zf', 'za')

-- Toggle line wrapping
vim.keymap.set('n', '<leader>lw', '<cmd>set wrap!<CR>')

-- Copy current working directory
vim.keymap.set('n', '<leader>cwd', '<cmd>let @+ = getcwd()<CR>')

-- Clear highlights on search when pressing <Esc> in normal mode
vim.keymap.set('n', '<Esc>', '<cmd>nohlsearch<CR>')

-- Exit terminal mode
vim.keymap.set('t', '<Esc><Esc>', '<C-\\><C-n>', { desc = 'Exit terminal mode' })
