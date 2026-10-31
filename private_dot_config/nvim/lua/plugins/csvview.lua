return {
  {
    'hat0uma/csvview.nvim',
    ft = 'csv',
    cmd = { 'CsvViewEnable', 'CsvViewDisable', 'CsvViewToggle' },
    keys = {
      { '<leader>cv', '<cmd>CsvViewToggle delimiter=, display_mode=border header_lnum=1<CR>', desc = 'Toggle CSV view' },
    },
    -- snacks.nvim's bigfile gives files over 1.5 MB (or with lines over 1000 characters on average) the
    -- filetype "bigfile" instead of csv, so the FileType autocmd in config never fires and this plugin
    -- never loads. snacks then sets the buffer's syntax to the real filetype, so turn the view on there.
    -- init runs at startup, before the plugin is loaded.
    init = function()
      vim.api.nvim_create_autocmd('Syntax', {
        group = vim.api.nvim_create_augroup('csvview-bigfile', { clear = true }),
        pattern = 'csv',
        callback = function(args)
          -- Only once per buffer: turning the view off sets the syntax back to csv, which would turn it on again
          if vim.bo[args.buf].filetype ~= 'bigfile' or vim.b[args.buf].csvview_bigfile then
            return
          end
          vim.b[args.buf].csvview_bigfile = true
          vim.api.nvim_buf_call(args.buf, function()
            vim.cmd 'CsvViewEnable delimiter=, display_mode=border header_lnum=1'
          end)
        end,
      })
    end,
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
