return {
  'nvim-neotest/neotest',
  dependencies = {
    'nvim-neotest/nvim-nio',
    'nvim-lua/plenary.nvim',
    'antoinemadec/FixCursorHold.nvim',
    'nvim-treesitter/nvim-treesitter',
    -- Adapters
    'nvim-neotest/neotest-python',
    'nvim-neotest/neotest-jest',
    'marilari88/neotest-vitest',
    'rcasia/neotest-java',
  },
  config = function()
    require('neotest').setup {
      adapters = {
        require 'neotest-python' {
          dap = { justMyCode = false },
        },
        require 'neotest-jest',
        require 'neotest-vitest',
        require 'neotest-java' {
          -- ignore_wrapper = false, -- set true if you want to skip gradlew/mvnw
        },
      },
    }
  end,
  -- stylua: ignore start
  keys = {
    {'<leader>tr', function() require('neotest').run.run() end, desc = 'Run nearest test',},
    {'<leader>tf', function() require('neotest').run.run(vim.fn.expand '%') end, desc = 'Run current file',},
    {'<leader>ts', function() require('neotest').summary.toggle() end, desc = 'Toggle summary',},
    {'<leader>to', function() require('neotest').output_panel.toggle() end, desc = 'Toggle output panel',},
    {'<leader>tS', function() require('neotest').run.stop() end, desc = 'Stop test',},
    {'<leader>tw', function() require('neotest').watch.toggle(vim.fn.expand '%') end, desc = 'Watch file',},
    -- Jump between failed tests
    {'<leader>tp', function() require('neotest').jump.prev { status = 'failed' } end, desc = 'Prev failed test',},
    {'<leader>tn', function() require('neotest').jump.next { status = 'failed' } end, desc = 'Next failed test',},
  },
  -- stylua: ignore end
}
