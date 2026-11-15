return {
  'karb94/neoscroll.nvim',
  opts = {},
  config = function()
    local neoscroll = require 'neoscroll'

    neoscroll.setup {
      mappings = {
        '<C-u>',
        '<C-d>',
      },
      hide_cursor = true,
      stop_eof = true,
      respect_scrolloff = true,
      cursor_scrolls_alone = true,
      duration_multiplier = 0.25,
      easing = 'linear',
      pre_hook = nil,
      post_hook = nil,
      performance_mode = false,
      ignored_events = { 'WinScrolled', 'CursorMoved' },
    }

    -- Remap <C-d> and <C-u> using the new signature: a third of the window height (Vim's own is half)
    vim.keymap.set({ 'n', 'v', 'x' }, '<C-d>', function()
      neoscroll.scroll(math.floor(vim.api.nvim_win_get_height(0) / 3), { move_cursor = true, duration = 83 })
    end)
    vim.keymap.set({ 'n', 'v', 'x' }, '<C-u>', function()
      neoscroll.scroll(-math.floor(vim.api.nvim_win_get_height(0) / 3), { move_cursor = true, duration = 83 })
    end)
  end,
}
