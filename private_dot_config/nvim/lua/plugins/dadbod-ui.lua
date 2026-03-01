return {
  'kristijanhusak/vim-dadbod-ui',
  dependencies = {
    { 'tpope/vim-dadbod', lazy = true },
    { 'kristijanhusak/vim-dadbod-completion', ft = { 'sql', 'mysql', 'plsql' }, lazy = true }, -- Optional
  },
  cmd = {
    'DBUI',
    'DBUIToggle',
    'DBUIAddConnection',
    'DBUIFindBuffer',
  },
  keys = {
    { '<leader>db', '<cmd>DBUIToggle<cr>', desc = 'Toggle Database UI' },
    { '<leader>da', '<cmd>DBUIAddConnection<cr>', desc = 'Add Database Connection' },
    { '<leader>df', '<cmd>DBUIFindBuffer<cr>', desc = 'Find Database Buffer' },
  },
  init = function()
    -- Your DBUI configuration
    vim.g.db_ui_use_nerd_fonts = 1
  end,
}
