return {
  'gbprod/substitute.nvim',
  dependencies = { 'gbprod/yanky.nvim' },
  event = 'VeryLazy',
  config = function()
    require('substitute').setup {
      on_substitute = require('yanky.integration').substitute(),
      yank_substituted_text = false,
      preserve_cursor_position = false,
      highlight_substituted_text = {
        enabled = true,
        timer = 500,
      },
      exchange = {
        use_esc_to_cancel = true,
        preserve_cursor_position = false,
      },
    }

    -- Substitute operator (on gz: z and Z would swallow zz/zt/za/z=/ZZ)
    vim.keymap.set('n', 'gz', require('substitute').operator, { noremap = true, desc = 'Substitute' })
    vim.keymap.set('n', 'gzz', require('substitute').line, { noremap = true, desc = 'Substitute line' })
    vim.keymap.set('n', 'gZ', require('substitute').eol, { noremap = true, desc = 'Substitute to EOL' })
    vim.keymap.set('x', 'gz', require('substitute').visual, { noremap = true, desc = 'Substitute visual' })

    -- Exchange (replaces mini.operators exchange)
    vim.keymap.set('n', '<leader>x', require('substitute.exchange').operator, { noremap = true, desc = 'Exchange' })
    vim.keymap.set('n', '<leader>xx', require('substitute.exchange').line, { noremap = true, desc = 'Exchange line' })
    vim.keymap.set('x', '<leader>x', require('substitute.exchange').visual, { noremap = true, desc = 'Exchange visual' })
  end,
}
