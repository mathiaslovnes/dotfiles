return {
  'MeanderingProgrammer/render-markdown.nvim',
  dependencies = {
    'nvim-treesitter/nvim-treesitter',
    'nvim-tree/nvim-web-devicons',
  },
  opts = {
    file_types = { 'markdown', 'python' },                                            -- enable for markdown + python

    vim.api.nvim_set_hl(0, 'RenderMarkdownCode', { fg = '#a6e3a1', bg = '#1e1e2e' }), -- Use your background color

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
