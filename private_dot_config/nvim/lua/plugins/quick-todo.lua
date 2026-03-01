return {
  'SyedAsimShah1/quick-todo.nvim',
  config = function()
    require('quick-todo').setup {
      keys = {
        open = '<leader>td',
      },
      window = {
        height = 0.7,
        width = 0.75,
        winblend = 0,
        border = 'rounded',
      },
    }
  end,
}
