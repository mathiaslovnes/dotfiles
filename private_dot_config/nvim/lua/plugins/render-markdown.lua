return {
  'MeanderingProgrammer/render-markdown.nvim',
  ft = { 'markdown', 'python' }, -- its file_types
  dependencies = {
    'nvim-treesitter/nvim-treesitter',
    'nvim-tree/nvim-web-devicons',
  },
  opts = {
    file_types = { 'markdown', 'python' }, -- enable for markdown + python

    heading = {
      enabled = true,
      render_modes = false,
      atx = true,
      setext = true,
      sign = true,
      icons = { '󰲡 ', '󰲣 ', '󰲥 ', '󰲧 ', '󰲩 ', '󰲫 ' },
      border_prefix = false,
      above = '▄',
      below = '▀',

      -- disable background highlights
      backgrounds = {},
    },

    pipe_table = {
      -- Pads cells with math by the width snacks.image draws it at, not its LaTeX source (table_math.lua). Wrapping
      -- tables wider than the window is off: it redraws any row whose width differs from its source text as raw text
      wrap = false,
      cell_offset = function(ctx)
        return require('table_math').cell_offset(ctx)
      end,
    },
  },
}
