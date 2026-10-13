return {
  {
    'hat0uma/csvview.nvim',
    ft = 'csv',
    cmd = { 'CsvViewEnable', 'CsvViewDisable', 'CsvViewToggle' },
    keys = {
      { '<leader>cv', '<cmd>CsvViewToggle delimiter=, display_mode=border header_lnum=1<CR>', desc = 'Toggle CSV view' },
    },
    opts = {
      parser = { comments = { '#', '//' } },
      view = { display_mode = 'border' },
      keymaps = {
        textobject_field_inner = { 'if', mode = { 'o', 'x' } },
        textobject_field_outer = { 'af', mode = { 'o', 'x' } },
        jump_next_field_end = { '<Tab>', mode = { 'n', 'v' } },
        jump_prev_field_end = { '<S-Tab>', mode = { 'n', 'v' } },
        jump_next_row = { '<Enter>', mode = { 'n', 'v' } },
        jump_prev_row = { '<S-Enter>', mode = { 'n', 'v' } },
      },
    },
    config = function(_, opts)
      require('csvview').setup(opts)
      vim.api.nvim_create_autocmd('FileType', {
        pattern = 'csv',
        callback = function()
          vim.cmd 'CsvViewEnable delimiter=, display_mode=border header_lnum=1'
        end,
      })
    end,
  },
}
