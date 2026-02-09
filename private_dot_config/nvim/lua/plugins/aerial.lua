return {
  'stevearc/aerial.nvim',
  opts = {},
  -- Optional dependencies
  dependencies = {
    'nvim-treesitter/nvim-treesitter',
    'nvim-tree/nvim-web-devicons',
  },

  vim.keymap.set('n', '<leader>sa', '<cmd>AerialToggle left<CR>', { desc = 'Search file with Aerial' }),
}
