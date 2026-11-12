return {
  'folke/noice.nvim',
  event = 'VeryLazy',
  opts = {
    presets = { inc_rename = true },
    cmdline = {
      enabled = true,
      view = 'cmdline_popup',
    },
    views = {
      cmdline_popup = {
        position = {
          row = '50%',
          col = '50%',
        },
        size = {
          width = 60,
          height = 'auto',
        },
        border = {
          style = 'rounded',
          padding = { 0, 1 },
        },
        win_options = {
          winhighlight = 'NormalFloat:NormalFloat,FloatBorder:FloatBorder',
        },
      },
    },
  },
}
