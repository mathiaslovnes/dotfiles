---@diagnostic disable: undefined-global

-- ===================================================================
-- Leader & Globals
-- ===================================================================

vim.g.mapleader = ' '

-- ===================================================================
-- Navigation & Motions
-- ===================================================================

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

-- Center
vim.keymap.set('n', 'S', 'zz')

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

-- Blank line above / below, with a count and . repeat (Neovim's built-in [<Space> and ]<Space>)
vim.keymap.set('n', '<leader>ø', '[<Space>', { remap = true, desc = 'Blank line above' })
vim.keymap.set('n', '<leader>Ø', ']<Space>', { remap = true, desc = 'Blank line below' })

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

-- <Tab>/<BS>/<S-Tab> always shift by 2 columns, even where the filetype's shiftwidth is wider (Python, Rust, ...)
local function shift_by_two(op)
  return function()
    local sw = vim.bo.shiftwidth
    vim.bo.shiftwidth = 2
    vim.cmd('normal! ' .. vim.v.count1 .. op .. 'gv')
    vim.bo.shiftwidth = sw
  end
end
vim.keymap.set('v', '<Tab>', shift_by_two '>', { silent = true })
vim.keymap.set('v', '<BS>', shift_by_two '<', { silent = true })
vim.keymap.set('v', '<S-Tab>', shift_by_two '<', { silent = true })

-- Make comment below/above
vim.keymap.set('n', '<leader>co', 'oX<esc><cmd>lua MiniComment.toggle_lines(vim.fn.line("."), vim.fn.line("."))<cr>fXxa',
  { desc = 'Add Comment Below' })
vim.keymap.set('n', '<leader>cO', 'OX<esc><cmd>lua MiniComment.toggle_lines(vim.fn.line("."), vim.fn.line("."))<cr>fXxa',
  { desc = 'Add Comment Above' })

-- ===================================================================
-- Clipboard & Yanking
-- ===================================================================

-- Delete without yanking
vim.keymap.set({ 'n', 'v' }, 'x', '"_x')
vim.keymap.set('n', 'ch', '"_ch')
vim.keymap.set('n', 'cl', '"_cl')

vim.keymap.set({ 'n', 'x' }, '<leader>D', '"_d') -- not <leader>d: debugger, dadbod and neogen maps start with it

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
    elseif choice == 2 then                       -- No
      require('mini.bufremove').delete(buf, true) -- force
    end
    -- choice == 3 (Cancel): do nothing
  else
    require('mini.bufremove').delete(buf)
  end
end, { desc = 'Delete buffer (prompt to save)' })

-- Cmd+1..9: go to buffer N (kitty sends Cmd+N as Alt+N)
for i = 1, 9 do
  vim.keymap.set('n', '<M-' .. i .. '>', '<cmd>BufferLineGoToBuffer ' .. i .. '<cr>', { desc = 'Go to buffer ' .. i })
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

-- Open link under cursor (gx/gX jump between regexes, treesitter-textobjects)
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
