return {
  {
    'rainbowhxch/accelerated-jk.nvim',
    config = function()
      require('accelerated-jk').setup {
        mode = 'time_driven',
        enable_deceleration = false,
        acceleration_motions = { 'h', 'j', 'k', 'l' },
        acceleration_limit = 100,
        acceleration_table = { 1, 3, 7, 11, 17 },
        -- when 'enable_deceleration = true', 'deceleration_table = { {200, 3}, {300, 7}, {450, 11}, {600, 15}, {750, 21}, {900, 9999} }'
        deceleration_table = { { 150, 9999 } },
      }
      -- (after setup, which maps j/k to real-line moves) No count: accelerated screen-line move, in normal
      -- and visual mode. With a count: real lines, so 12j lands on relative line 12; in normal mode,
      -- jumps over 5 go in the jumplist.
      for _, key in ipairs { 'j', 'k' } do
        vim.keymap.set({ 'n', 'x' }, key, function()
          local count = vim.v.count
          if count == 0 then
            return require('accelerated-jk').move_to('g' .. key)
          end
          if count > 5 and vim.fn.mode() == 'n' then
            vim.cmd "normal! m'"
          end
          vim.cmd('normal! ' .. count .. key)
        end, { desc = 'Screen line, or real lines with a count' })
      end
    end,
  },
}
