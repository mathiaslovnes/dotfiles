return {
  'uga-rosa/ccc.nvim',
  config = function()
    local ccc = require 'ccc'
    local mapping = ccc.mapping
    ccc.setup {
      -- Default highlighters
      highlighters = {
        'hex',
        'short_hex',
        'css',
      },
      -- Keybindings in the picker
      mappings = {
        ['<Esc>'] = mapping.quit,
        ['q'] = mapping.quit,
        ['<CR>'] = mapping.complete,
      },
    }
    -- Optional: Set a keybinding to toggle the picker
    vim.keymap.set('n', '<leader>cp', '<cmd>CccPick<CR>', { noremap = true, silent = true })
  end,
}
