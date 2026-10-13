return {
  'MeanderingProgrammer/render-markdown.nvim',
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
  },
}
