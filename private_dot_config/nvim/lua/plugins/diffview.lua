return {
  'sindrets/diffview.nvim',
  cmd = { 'DiffviewOpen', 'DiffviewFileHistory' },
  keys = {
    { 'dvo', '<cmd>DiffviewOpen<CR>', desc = 'Diffview open' },
    { 'dvc', ':DiffviewClose<CR>', desc = 'Close Diffview' },
    { 'dvh', '<cmd>DiffviewFileHistory %<CR>', desc = 'Diffview file history' },
    { 'dvr', ':DiffviewRefresh<CR>', desc = 'Refresh Diffview' },
  },
  opts = {},
}
