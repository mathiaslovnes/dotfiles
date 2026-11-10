-- This is the file that is actually read
return {
  'ThePrimeagen/harpoon',
  branch = 'harpoon2',
  dependencies = { 'nvim-lua/plenary.nvim', 'nvim-telescope/telescope.nvim' },
  opts = {
    settings = {
      save_on_toggle = true,
      sync_on_ui_close = true,
      key = function()
        return vim.loop.cwd()
      end,
    },
  },
  -- stylua: ignore start
  keys = {
    { '<leader>a', function() require('harpoon'):list():add() end, desc = 'Add harpoon tag' },
    { '<leader>ha', function() local h = require 'harpoon' h.ui:toggle_quick_menu(h:list()) end, desc = 'Open harpoon menu' },
    { '<leader>1', function() require('harpoon'):list():select(1) end, desc = 'Go to 1st harpoon tag' },
    { '<leader>2', function() require('harpoon'):list():select(2) end, desc = 'Go to 2nd harpoon tag' },
    { '<leader>3', function() require('harpoon'):list():select(3) end, desc = 'Go to 3rd harpoon tag' },
    { '<leader>4', function() require('harpoon'):list():select(4) end, desc = 'Go to 4th harpoon tag' },
    { '<leader>q', function() require('harpoon'):list():prev() end, desc = 'Go to previous harpoon tag' },
    { '<leader>e', function() require('harpoon'):list():next() end, desc = 'Go to next harpoon tag' },
  },
  -- stylua: ignore end
  config = function(_, opts)
    require('harpoon'):setup(opts)
  end,
}
