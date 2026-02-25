return {
  'Wansmer/treesj',
  dependencies = { 'nvim-treesitter/nvim-treesitter' },
  config = function()
    require('treesj').setup {
      use_default_keymaps = false,
      check_syntax_error = true,
      max_join_length = 120,
      cursor_behavior = 'hold',
      notify = true,
      dot_repeat = true,
      on_error = nil,
    }

    vim.keymap.set('n', '<leader>m', require('treesj').toggle, { desc = 'TreeSJ [M]erge toggle' })
    vim.keymap.set('n', '<leader>jo', require('treesj').join, { desc = 'TreeSJ [Jo]in' })
    vim.keymap.set('n', '<leader>S', require('treesj').split, { desc = 'TreeSJ [S]plit' })
  end,
}
