return {
  'mg979/vim-visual-multi',
  branch = 'master',
  init = function()
    -- optional: configure keys before plugin loads
    vim.g.VM_maps = {
      ['Find Under'] = '<C-n>',
      ['Find Subword Under'] = '<C-n>',
    }
  end,
}
