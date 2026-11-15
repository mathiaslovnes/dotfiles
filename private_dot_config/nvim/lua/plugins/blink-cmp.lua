-- Whether the cursor is in a jukit text cell (r"""°°° … °°°""" in a .py notebook): the nearest cell marker
-- above it opens one
local function in_text_cell()
  if vim.bo.filetype ~= 'python' then
    return false
  end
  local row = vim.fn.search([[^r\?"""°°°\|^°°°"""\|^#\s*|%%--%%|]], 'bcnW', math.max(1, vim.fn.line '.' - 1000))
  return row > 0 and vim.fn.getline(row):match '^r?"""°°°' ~= nil
end

return {
  {
    'saghen/blink.cmp',
    event = { 'InsertEnter', 'CmdlineEnter' },
    version = '1.*',
    init = function()
      -- Ctrl-Space in a jukit text cell, where blink is off (enabled below), turns it on until its menu closes,
      -- insert mode ends or, when no menu opened, the word ends. blink's own Ctrl-Space map falls back to this
      -- one while blink is off.
      vim.keymap.set('i', '<C-Space>', function()
        vim.b.completion_asked = true
        require('blink.cmp').show()
      end, { desc = 'Completion menu in a jukit text cell' })
      vim.api.nvim_create_autocmd('InsertLeave', {
        callback = function()
          vim.b.completion_asked = nil
        end,
      })
      vim.api.nvim_create_autocmd('User', {
        pattern = 'BlinkCmpMenuClose',
        callback = function()
          vim.b.completion_asked = nil
        end,
      })
      vim.api.nvim_create_autocmd('InsertCharPre', {
        callback = function()
          if vim.b.completion_asked and vim.fn.match(vim.v.char, [[\k]]) < 0 and not require('blink.cmp').is_menu_visible() then
            vim.b.completion_asked = nil
          end
        end,
      })
    end,
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
      -- Off in jukit text cells: while writing text, the suggestions cost CPU on every key. Ctrl-Space still
      -- opens them there (init above).
      enabled = function()
        return vim.b.completion_asked or not in_text_cell()
      end,
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
