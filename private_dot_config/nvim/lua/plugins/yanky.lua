return {
  'gbprod/yanky.nvim',
  config = function(_, opts)
    require('yanky').setup(opts)
    vim.api.nvim_set_hl(0, 'YankyPut', { link = 'IncSearch' })
    vim.api.nvim_set_hl(0, 'YankyYanked', { link = 'IncSearch' })
  end,
  opts = {
    ring = {
      history_length = 100,
      storage = 'shada',
      storage_path = vim.fn.stdpath 'data' .. '/databases/yanky.db',
      sync_with_numbered_registers = true,
      cancel_event = 'update',
      ignore_registers = { '_' },
      update_register_on_cycle = false,
      permanent_wrapper = nil,
    },
    picker = {
      select = {
        action = nil,
      },
      telescope = {
        use_default_mappings = true,
        mappings = nil,
      },
    },
    system_clipboard = {
      sync_with_ring = true,
      clipboard_register = nil,
    },
    highlight = {
      on_put = true,
      on_yank = true,
      timer = 150,
    },
    preserve_cursor_position = {
      enabled = true,
    },
    textobj = {
      enabled = false,
    },
  },
  dependencies = { 'folke/snacks.nvim' },
  keys = {
    { 'y', '<Plug>(YankyYank)', mode = { 'n', 'x' } },
    { 'p', '<Plug>(YankyPutAfter)', mode = { 'n', 'x' } },
    { 'P', '<Plug>(YankyPutBefore)', mode = { 'n', 'x' } },
    { '<leader>P', '<Plug>(YankyNextEntry)' },
    { '<leader>p', '<Plug>(YankyPreviousEntry)' },
    {
      '<leader>Y',
      function()
        Snacks.picker.yanky()
      end,
      mode = { 'n', 'x' },
      desc = 'Open Yank History',
    },
  },
}
