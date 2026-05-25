return { -- You can easily change to a different colorscheme.
  -- Change the name of the colorscheme plugin below, and then
  -- change the command in the config to whatever the name of that colorscheme is.
  --
  -- If you want to see what colorschemes are already installed, you can use `:Telescope colorscheme`.
  'catppuccin/nvim',
  name = 'catppuccin',
  priority = 1000, -- Make sure to load this before all the other start plugins.
  config = function()
    ---@diagnostic disable-next-line: missing-fields
    require('catppuccin').setup {
      custom_highlights = function(colors)
        return {
          ["@string.documentation.python"] = { fg = colors.green },
          YankyPut = { link = "IncSearch" },
          YankyYanked = { link = "IncSearch" },
        }
      end,
      flavour = 'mocha', -- latte, frappe, macchiato, mocha
      background = {     -- :h background
        light = 'latte',
        dark = 'mocha',
      },
      transparent_background = true, -- disables setting the background color.
      float = {
        transparent = false,         -- enable transparent floating windows
        solid = false,               -- use solid styling for floating windows, see |winborder|
      },
      show_end_of_buffer = true,     -- shows the '~' characters after the end of buffers
      term_colors = false,           -- sets terminal colors (e.g. `g:terminal_color_0`)
      dim_inactive = {
        enabled = false,             -- dims the background color of inactive window
        shade = 'dark',
        percentage = 0.15,           -- percentage of the shade to apply to the inactive window
      },
      no_italic = false,             -- Force no italic
      no_bold = false,               -- Force no bold
      no_underline = false,          -- Force no underline
      styles = {                     -- Handles the styles of general hi groups (see `:h highlight-args`):
        comments = {},               -- Change the style of comments
        conditionals = {},
        loops = {},
        functions = {},
        keywords = {},
        strings = {},
        variables = {},
        numbers = {},
        booleans = {},
        properties = {},
        types = {},
        operators = {},
        -- miscs = {}, -- Uncomment to turn off hard-coded styles
      },
      color_overrides = {},
      custom_highlights = {},
      default_integrations = true,
      auto_integrations = false,
      integrations = {
        blink_cmp = true,
        cmp = true,
        gitsigns = true,
        nvimtree = true,
        treesitter = true,
        notify = false,
        markdown = true,
        render_markdown = true,
        mini = {
          enabled = true,
          indentscope_color = '',
        },
        -- For more plugins integrations please scroll down (https://github.com/catppuccin/nvim#integrations)
      },
    }

    vim.api.nvim_set_hl(0, '@text.markdown', { fg = '#a6e3a1' })
    vim.api.nvim_set_hl(0, '@none.markdown', { fg = '#a6e3a1' })
    vim.api.nvim_set_hl(0, '@markup.markdown', { fg = '#a6e3a1' })

    -- Toggle transparency function
    local bg_transparent = true
    local toggle_transparency = function()
      bg_transparent = not bg_transparent
      require('catppuccin').setup {
        transparent_background = bg_transparent,
      }
      vim.cmd.colorscheme 'catppuccin'
    end

    -- Keymap to toggle transparency
    vim.keymap.set('n', '<leader>bg', toggle_transparency,
      { desc = 'Toggle Background Transparency', noremap = true, silent = true })

    -- Load the colorscheme
    vim.cmd.colorscheme 'catppuccin'
  end,
}
