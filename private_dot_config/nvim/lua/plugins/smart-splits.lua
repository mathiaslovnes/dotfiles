return {

  'mrjones2014/smart-splits.nvim',
  lazy = false, -- the tmux backend marks the pane as Neovim (@pane-is-vim) on load; until then tmux keeps Ctrl/Alt+hjkl
  dependencies = {
    { 'smart-splits-nvim/backend-tmux', main = 'smart-splits-backend-tmux' },
  },

  config = function()
    -- moving between splits, on into the neighboring tmux pane at Neovim's edge
    -- (Karabiner makes Ctrl+H/J/K/L arrows; these Ctrl keys come from tmux's prefix arrows, see tmux.conf)
    vim.keymap.set('n', '<C-h>', require('smart-splits').move_cursor_left)
    vim.keymap.set('n', '<C-j>', require('smart-splits').move_cursor_down)
    vim.keymap.set('n', '<C-k>', require('smart-splits').move_cursor_up)
    vim.keymap.set('n', '<C-l>', require('smart-splits').move_cursor_right)
    -- resizing splits
    -- these keymaps will also accept a range,
    -- for example `10<M-h>` will `resize_left` by `(10 * resize.amount)`
    vim.keymap.set('n', '<M-h>', require('smart-splits').resize_left)
    vim.keymap.set('n', '<M-j>', require('smart-splits').resize_down)
    vim.keymap.set('n', '<M-k>', require('smart-splits').resize_up)
    vim.keymap.set('n', '<M-l>', require('smart-splits').resize_right)
    -- swapping buffers between windows,
    vim.keymap.set('n', '<leader><leader>h', require('smart-splits').swap_buf_left)
    vim.keymap.set('n', '<leader><leader>j', require('smart-splits').swap_buf_down)
    vim.keymap.set('n', '<leader><leader>k', require('smart-splits').swap_buf_up)
    vim.keymap.set('n', '<leader><leader>l', require('smart-splits').swap_buf_right)

    -- only what differs from v3's defaults
    require('smart-splits').setup {
      move = { at_edge = 'stop' }, -- same as tmux's @smart-splits_at_edge
      resize = { amount = 2 }, -- same step as tmux's @smart-splits_resize_step_size
      mux = { backend = 'smart-splits-backend-tmux' },
    }
  end,
}
