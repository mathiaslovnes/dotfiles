return {
  {
    'rainbowhxch/accelerated-jk.nvim',
    config = function()
      require('accelerated-jk').setup {
        mode = 'time_driven',
        enable_deceleration = false,
        acceleration_motions = {},
        acceleration_limit = 150,
        acceleration_table = { 2, 3, 5, 7, 9, 12, 15, 20 },
        -- when 'enable_deceleration = true', 'deceleration_table = { {200, 3}, {300, 7}, {450, 11}, {600, 15}, {750, 21}, {900, 9999} }'
        deceleration_table = { { 150, 9999 } },
      }
    end,
  },
}
