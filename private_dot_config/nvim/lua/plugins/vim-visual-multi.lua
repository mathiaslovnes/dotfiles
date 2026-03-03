return {
  'mg979/vim-visual-multi',
  branch = 'master',
  init = function()
    vim.g.VM_leader = '-'

    vim.g.VM_maps = {
      -- word selection
      ['Find Under'] = '<C-n>',
      ['Find Subword Under'] = '<C-n>',

      ['Goto Next'] = '<C-f>',
      ['Goto Prev'] = '<C-b>',

      -- -- vertical cursor column
      ['Add Cursor Down'] = '<DOWN>',
      ['Add Cursor Up'] = '<UP>',

      -- find next/prev occurrence (n/N → n/p)
      ['Find Next'] = 'n',
      ['Find Prev'] = 'N',

      -- skip current match and go to next/prev
      ['Skip Region'] = 's',

      -- remove current cursor/region
      ['Remove Region'] = 'S',

      -- select all occurrences at once
      ['Select All'] = '-A',

      -- add single cursor at position
      ['Add Cursor At Pos'] = '--',

      -- switch cursor/extend mode
      ['Switch Mode'] = '<Tab>',

      -- exit VM
      ['Exit'] = '<Esc>',
    }
  end,
}
