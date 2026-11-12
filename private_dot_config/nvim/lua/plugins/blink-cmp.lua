return {
  {
    'saghen/blink.cmp',
    event = { 'InsertEnter', 'CmdlineEnter' },
    version = '1.*',
    dependencies = {
      {
        'L3MON4D3/LuaSnip',
        version = '2.*',
        build = (function()
          if vim.fn.has 'win32' == 1 or vim.fn.executable 'make' == 0 then
            return
          end
          return 'make install_jsregexp'
        end)(),
        opts = {},
      },
      'folke/lazydev.nvim',
    },
    --- @module 'blink.cmp'
    --- @type blink.cmp.Config
    opts = {
      cmdline = {
        enabled = true,
        keymap = { preset = 'inherit' },
        completion = {
          menu = {
            auto_show = true,
          },
          ghost_text = { enabled = false },
        },
      },
      keymap = {
        preset = 'default',
        ['<up>'] = false,
        ['<down>'] = false,
      },

      appearance = {
        nerd_font_variant = 'mono',
      },

      completion = {
        accept = {
          auto_brackets = { enabled = true },
        },
        menu = {
          border = 'rounded',
          scrollbar = false,
          draw = {
            treesitter = { 'lsp' },
            columns = {
              { 'kind_icon' },
              { 'label',    'label_description', gap = 1 },
              { 'kind' },
            },
          },
        },
        documentation = {
          auto_show = true,
          auto_show_delay_ms = 200,
          window = {
            border = 'rounded',
            scrollbar = false,
          },
        },
        ghost_text = { enabled = false },
      },

      sources = {
        default = { 'lsp', 'path', 'snippets', 'lazydev', 'buffer' },
        per_filetype = {
          sql = { 'snippets', 'dadbod', 'buffer' },
        },
        providers = {
          lazydev = { module = 'lazydev.integrations.blink', score_offset = 100 },
          dadbod = { name = 'Dadbod', module = 'vim_dadbod_completion.blink' }, -- table and column names
        },
      },

      snippets = { preset = 'luasnip' },
      fuzzy = { implementation = 'prefer_rust_with_warning' },
      signature = {
        enabled = true,
        window = { border = 'rounded' },
      },
    },
  },
}
-- vim: ts=2 sts=2 sw=2 et
