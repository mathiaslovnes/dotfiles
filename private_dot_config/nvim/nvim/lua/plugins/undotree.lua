return {
  'mbbill/undotree',
  cmd = 'UndotreeToggle', -- Lazy-load only when you call the command
  keys = {
    { '<leader>ut', '<cmd>UndotreeToggle<CR>', desc = 'Toggle UndoTree' },
  },
}
