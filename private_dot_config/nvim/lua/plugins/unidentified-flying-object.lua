return {
  {
    -- stylua: ignore start
    'kevinhwang91/nvim-ufo',
    dependencies = { 'kevinhwang91/promise-async' },
    event = 'BufRead',
    keys = {
      -- whole-buffer fold commands; zo/zc/zO/zC stay Vim's per-fold ones
      {'zR', function() require('ufo').openAllFolds() end, desc = 'Open all folds',},
      {'zM', function() require('ufo').closeAllFolds() end, desc = 'Close all folds',},
      {'zr', function() require('ufo').openFoldsExceptKinds() end, desc = 'Open all folds except excluded kinds',},
      {'zm', function() require('ufo').closeFoldsWith() end, desc = 'Close folds deeper than [count] (all without count)',},
      {
        'zp',
        function()
          local winid = require('ufo').peekFoldedLinesUnderCursor()
          if winid then
            -- Prevent UFO from displaying line-hierarchies in column-numberline
            vim.schedule(function()
              if vim.api.nvim_win_is_valid(winid) then
                vim.wo[winid].number = false
                vim.wo[winid].relativenumber = false
              end
            end)
          else
            vim.lsp.buf.hover()
          end
        end,
        desc = 'Peek folded lines or hover',
      },
    },
    config = function()
      require('ufo').setup()
    end,
    -- stylua: ignore end
  },
}
