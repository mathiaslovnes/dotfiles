return {
  'danymat/neogen',
  config = true,
  -- Uncomment next line if you want to follow only stable versions
  -- version = "*"
  config = function()
    require('neogen').setup {
      enabled = true, --if you want to disable Neogen
      input_after_comment = true, -- (default: true) automatic jump (with insert mode) on inserted annotation
      snippet_engine = 'luasnip', -- allows for jumping between annotations with luasnip binds
    }

    vim.keymap.set('n', '<leader>dg', function()
      require('neogen').generate()
    end, { desc = 'Generate docstring with neogen' })
  end,
}
