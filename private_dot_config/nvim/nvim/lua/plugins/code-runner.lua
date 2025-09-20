return {
  {
    'CRAG666/code_runner.nvim',
    dependencies = { 'nvim-lua/plenary.nvim', 'preservim/vimux' },
    config = function()
      require('code_runner').setup {
        -- Paste the configuration table directly here
        mode = 'vimux', -- Use vimux for tmux pane output
        hot_reload = false,
        focus = true,
        startinsert = false,
        insert_prefix = '',
        term = {
          position = 'bot',
          size = 12,
        },
        float = {
          close_key = '<ESC>',
          border = 'none',
          height = 0.8,
          width = 0.8,
          x = 0.5,
          y = 0.5,
          border_hl = 'FloatBorder',
          float_hl = 'Normal',
          blend = 0,
        },
        -- Add filetype to support common languages
        filetype = {
          python = 'ipython ',
          javascript = 'node ',
          sh = 'bash ',
          ruby = 'ruby ',
        },
      }
      vim.keymap.set('n', '<leader>rc', ':RunCode<CR>', { noremap = true, silent = true })
    end,
  },
}
