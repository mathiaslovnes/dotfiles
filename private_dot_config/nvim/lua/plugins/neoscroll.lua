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

    -- Remap <C-d> and <C-u> using the new signature. Only the view moves: the cursor stays on its line of text
    -- (Vim's own moves the cursor along, so it keeps its place on the screen)
    vim.keymap.set({ 'n', 'v', 'x' }, '<C-d>', function()
      neoscroll.scroll(15, { move_cursor = false, duration = 83 })
    end)
    vim.keymap.set({ 'n', 'v', 'x' }, '<C-u>', function()
      neoscroll.scroll(-15, { move_cursor = false, duration = 83 })
    end)
  end,
}
