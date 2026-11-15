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

    -- jukit notebooks: conceal stays on in insert and visual mode too, so the hidden r"""°°° / °°°""" lines
    -- (jukit_dividers.lua) don't reappear there and shift the lines below them
    overrides = {
      filetype = { python = { win_options = { conceallevel = { default = 3 } } } },
    },
  },
}
