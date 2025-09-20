return {
  {
    'hat0uma/csvview.nvim',
    opts = {
      parser = { comments = { '#', '//' } },
      keymaps = {
        textobject_field_inner = { 'if', mode = { 'o', 'x' } },
        textobject_field_outer = { 'af', mode = { 'o', 'x' } },
        jump_next_field_end = { '<Tab>', mode = { 'n', 'v' } },
        jump_prev_field_end = { '<S-Tab>', mode = { 'n', 'v' } },
        jump_next_row = { '<Enter>', mode = { 'n', 'v' } },
        jump_prev_row = { '<S-Enter>', mode = { 'n', 'v' } },
      },
    },
    cmd = { 'CsvViewEnable', 'CsvViewDisable', 'CsvViewToggle' },
    ft = { 'csv' }, -- lazy-load only for csv files
    config = function(_, opts)
      require('csvview').setup(opts)
      -- autocmd is actually optional if you use ft lazy-loading, but if you want:
      vim.api.nvim_create_autocmd('FileType', {
        pattern = 'csv',
        callback = function()
          require('csvview').enable()
        end,
      })
    end,
  },
}
