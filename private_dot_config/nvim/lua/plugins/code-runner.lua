return {
  {
    'CRAG666/code_runner.nvim',
    dependencies = { 'nvim-lua/plenary.nvim', 'preservim/vimux', 'CRAG666/betterTerm.nvim' },
    config = function()
      require('code_runner').setup {
        -- choose default mode (valid term, tab, float, better_term, toggle, vimux)
        mode = 'vimux',
        -- add hot reload (Experimental)
        hot_reload = false,
        -- Focus on runner window(only works on term and tab mode)
        focus = true,
        -- startinsert (see ':h inserting-ex')
        startinsert = false,
        insert_prefix = '',
        term = {
          --  Position to open the terminal, this option is ignored if mode ~= term
          position = 'bot',
          -- window size, this option is ignored if mode == tab
          size = 24,
        },
        float = {
          close_key = '<ESC>',
          -- Window border (see ':h nvim_open_win')
          border = 'none',

          -- Num from `0 - 1` for measurements
          height = 0.8,
          width = 0.8,
          x = 0.5,
          y = 0.5,

          -- Highlight group for floating window/border (see ':h winhl')
          border_hl = 'FloatBorder',
          float_hl = 'Normal',

          -- Transparency (see ':h winblend')
          blend = 0,
        },
        better_term = { -- Toggle mode replacement
          clean = false, -- Clean terminal before launch
          number = 10, -- Use nil for dynamic number and set init
          init = nil,
        },
        filetype_path = '',
        -- Save :w before running a file
        before_run_filetype = function()
          vim.cmd 'w'
        end,
        filetype = {
          javascript = 'node',
          java = {
            'cd $dir &&',
            'javac $fileName &&',
            'java $fileNameWithoutExt',
          },
          c = {
            'cd $dir &&',
            'gcc $fileName',
            '-o $fileNameWithoutExt &&',
            '$dir/$fileNameWithoutExt',
          },
          cpp = {
            'cd $dir &&',
            'g++ $fileName',
            '-o $fileNameWithoutExt &&',
            '$dir/$fileNameWithoutExt',
          },
          --ppython = 'python -u',
          python = false,
          sh = 'bash',
          ruby = 'ruby',
          rust = {
            'cd $dir &&',
            'rustc $fileName &&',
            '$dir/$fileNameWithoutExt',
          },
        },
        project_path = '',
        project = {},
        prefix = '',
      }

      -- Keybindings
      -- Set ! for running code in all file-types except python - handled by vim-jukit
      vim.api.nvim_create_autocmd({ 'BufEnter', 'BufWinEnter' }, {
        pattern = '*',
        callback = function()
          if vim.bo.filetype ~= 'python' then
            vim.keymap.set('n', '!', ':RunCode<CR>', { noremap = true, silent = false, buffer = true })
          end
        end,
      })
      -- Run the current file
      -- vim.keymap.set('n', '<leader>rF', ':RunFile<CR>', { noremap = true, silent = false })
      -- Close the output window
      -- vim.keymap.set('n', '<leader>rc', ':RunClose<CR>', { noremap = true, silent = false })
      -- vim.keymap.set('n', '<leader>rft', ':RunFile tab<CR>', { noremap = true, silent = false })
      -- vim.keymap.set('n', '<leader>rp', ':RunProject<CR>', { noremap = true, silent = false })
      -- vim.keymap.set('n', '<leader>crf', ':CRFiletype<CR>', { noremap = true, silent = false })
      -- vim.keymap.set('n', '<leader>crp', ':CRProjects<CR>', { noremap = true, silent = false })
    end,
  },
}
