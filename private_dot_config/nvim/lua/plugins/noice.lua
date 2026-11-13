return {
  'folke/noice.nvim',
  event = 'VeryLazy',
  opts = {
    presets = { inc_rename = true },
    routes = {
      -- pyright reports each quick analysis pass as an untitled progress task, which stacked up as "✔ pyright" lines
      {
        filter = {
          event = 'lsp',
          kind = 'progress',
          cond = function(message)
            local progress = message.opts.progress or {}
            return progress.client == 'pyright' and (progress.title or '') == ''
          end,
        },
        opts = { skip = true },
      },
    },
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
