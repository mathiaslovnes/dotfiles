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
  config = function()
    local harpoon = require 'harpoon'

    -- REQUIRED
    harpoon:setup()

    -- stylua: ignore start
   vim.keymap.set('n', '<leader>a', function() harpoon:list():add() end, { desc = "Add harpoon tag" })
   vim.keymap.set('n', '<leader>ha', function() harpoon.ui:toggle_quick_menu(harpoon:list())end, { desc = "Open harpoon menu" })
   vim.keymap.set('n', '<leader>1', function() harpoon:list():select(1) end, { desc = "Go to 1st harpoon tag" })
   vim.keymap.set('n', '<leader>2', function() harpoon:list():select(2) end, { desc = "Go to 2nd harpoon tag" })
   vim.keymap.set('n', '<leader>3', function() harpoon:list():select(3) end, { desc = "Go to 3rd harpoon tag" })
   vim.keymap.set('n', '<leader>4', function() harpoon:list():select(4) end, { desc = "Go to 4th harpoon tag" })
   vim.keymap.set('n', '<leader>q', function() harpoon:list():prev() end, { desc = "Go to previous harpoon tag" })
   vim.keymap.set('n', '<leader>e', function() harpoon:list():next() end, { desc = "Go to next harpoon tag" })
    -- stylua: ignore end
  end,
}
