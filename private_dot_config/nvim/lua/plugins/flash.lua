return {
  'folke/flash.nvim',
  event = 'VeryLazy',
  ---@type Flash.Config
  opts = {
    labels = 'asdfghjklqwertyuiopzxcvbnm',
    search = {
      multi_window = true,
      forward = true,
      wrap = true,
      mode = 'exact',
      incremental = false,
      exclude = {
        'notify',
        'cmp_menu',
        'noice',
        'flash_prompt',
        function(win)
          return not vim.api.nvim_win_get_config(win).focusable
        end,
      },
      trigger = '',
      max_length = false,
    },
    jump = {
      jumplist = true,
      pos = 'start',
      history = false,
      register = false,
      nohlsearch = false,
      autojump = false,
      inclusive = nil,
      offset = nil,
    },
    label = {
      uppercase = true,
      exclude = '',
      current = true,
      after = true,
      before = false,
      style = 'overlay',
      reuse = 'lowercase',
      distance = true,
      min_pattern_length = 0,
      rainbow = {
        enabled = false,
        shade = 5,
      },
    },
    highlight = {
      backdrop = true,
      matches = true,
      priority = 5000,
      groups = {
        match = 'FlashMatch',
        current = 'FlashCurrent',
        backdrop = 'FlashBackdrop',
        label = 'FlashLabel',
      },
    },
    modes = {
      char = {
        enabled = true,
        keys = { 'f', 'F', 't', 'T', ';', ',' },
        char_actions = function(motion)
          return {
            ['f'] = 'right',
            ['F'] = 'left',
            ['t'] = 'right',
            ['T'] = 'left',
          }
        end,
        -- Disable f/t labels if you want:
        -- jump_labels = false,
      },
    },
  },

  -- stylua: ignore
  keys = {
    { "ø", mode = { "n", "x", "o" }, function() require("flash").jump() end, desc = "Flash" },
    { "Ø", mode = { "n", "x", "o" }, function() require("flash").treesitter() end, desc = "Flash Treesitter" },
    { "r", mode = "o", function() require("flash").remote() end, desc = "Remote Flash" },
    { "R", mode = { "o", "x" }, function() require("flash").treesitter_search() end, desc = "Treesitter Search" },
    { "<C-ø>", mode = { "c" }, function() require("flash").toggle() end, desc = "Toggle Flash Search" },
  },

  -- Clear highlights on <ESC>
  vim.keymap.set('n', '<Esc>', function()
    vim.cmd 'nohlsearch'
    for _, buf in ipairs(vim.api.nvim_list_bufs()) do
      for name, ns_id in pairs(vim.api.nvim_get_namespaces()) do
        if name:find 'flash' then
          vim.api.nvim_buf_clear_namespace(buf, ns_id, 0, -1)
        end
      end
    end
  end),
}
