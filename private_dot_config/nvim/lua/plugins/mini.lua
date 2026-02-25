return {
  { -- Collection of various small independent plugins/modules
    'echasnovski/mini.nvim',
    config = function()
      require('mini.icons').setup()
      -- The mock function makes mini.icons pretend to be nvim-web-devicons so any plugin that calls nvim-web-devicons gets mini.icons instead. You can verify it's working by running:
      require('mini.icons').mock_nvim_web_devicons()

      -- Trim trailing whitespace
      require('mini.trailspace').setup {
        -- Useful to not show trailing whitespace where it usually doesn't matter.
        -- Highlight only in normal buffers (ones with empty 'buftype'). This is
        only_in_normal_buffers = true,

        vim.keymap.set('n', '<leader>tst', '<cmd>MiniTrailspace.trim()<CR>', { desc = '[T]rail[s]pace.[t]rim()' }),
      }

      -- Better Around/Inside textobjects
      --
      -- Examples:
      --  - va)  - [V]isually select [A]round [)]paren
      --  - yinq - [Y]ank [I]nside [N]ext [Q]uote
      --  - ci'  - [C]hange [I]nside [']quote
      require('mini.ai').setup {
        -- Table with textobject id as fields, textobject specification as values.
        -- Also use this to disable builtin textobjects. See |MiniAi.config|.

        custom_textobjects = nil,

        -- Module mappings. Use `''` (empty string) to disable one.
        mappings = {
          -- Main textobject prefixes
          around = 'a',
          inside = 'i',

          -- Next/last variants
          -- NOTE: These override built-in LSP selection mappings on Neovim>=0.12
          -- Map LSP selection manually to use it (see `:h MiniAi.config`)
          around_last = 'A',
          inside_last = 'I',
          -- around_next = 'an',
          -- inside_next = 'in', -- No need - by default it goes to the next one

          -- Move cursor to corresponding edge of `a` textobject
          goto_left = 'g[',
          goto_right = 'g]',
        },

        -- Number of lines within which textobject is searched
        n_lines = 500,

        -- How to search for object (first inside current line, then inside
        -- neighborhood). One of 'cover', 'cover_or_next', 'cover_or_prev',
        -- 'cover_or_nearest', 'next', 'previous', 'nearest'.
        search_method = 'cover_or_next',

        -- Whether to disable showing non-error feedback
        -- This also affects (purely informational) helper messages shown after
        -- idle time if user input is required.
        silent = false,
      }

      require('mini.comment').setup {
        -- Options which control module behavior
        options = {
          -- Function to compute custom 'commentstring' (optional)
          custom_commentstring = nil,

          -- Whether to ignore blank lines when commenting
          ignore_blank_line = false,

          -- Whether to ignore blank lines in actions and textobject
          start_of_line = false,

          -- Whether to force single space inner padding for comment parts
          pad_comment_parts = true,
        },

        -- Module mappings. Use `''` (empty string) to disable one.
        mappings = {
          -- Toggle comment (like `gcip` - comment inner paragraph) for both
          -- Normal and Visual modes
          comment = '<C-c>',

          -- Toggle comment on current line
          comment_line = '<C-c>',

          -- Toggle comment on visual selection
          comment_visual = '<C-c>',

          -- Define 'comment' textobject (like `dgc` - delete whole comment block)
          -- Works also in Visual mode if mapping differs from `comment_visual`
          textobject = '<C-c>',
        },

        -- Hook functions to be executed at certain stage of commenting
        hooks = {
          -- Before successful commenting. Does nothing by default.
          pre = function() end,
          -- After successful commenting. Does nothing by default.
          post = function() end,
        },
      }

      -- Add/delete/replace surroundings (brackets, quotes, etc.)
      --
      -- - saiw) - [S]urround [A]dd [I]nner [W]ord [)]Paren
      -- - sd'   - [S]urround [D]elete [']quotes
      -- - sr)'  - [S]urround [R]eplace [)] [']
      require('mini.surround').setup(
        -- No need to copy this inside `setup()`. Will be used automatically.
        {
          -- Add custom surroundings to be used on top of builtin ones. For more
          -- information with examples, see `:h MiniSurround.config`.
          custom_surroundings = nil,

          -- Duration (in ms) of highlight when calling `MiniSurround.highlight()`
          highlight_duration = 500,

          -- Module mappings. Use `''` (empty string) to disable one.
          mappings = {
            add = 'sa', -- Add surrounding in Normal and Visual modes
            delete = 'sd', -- Delete surrounding
            find = 'sf', -- Find surrounding (to the right)
            find_left = 'sF', -- Find surrounding (to the left)
            highlight = 'sh', -- Highlight surrounding
            replace = 'sr', -- Replace surrounding

            suffix_last = 'p', -- Suffix to search with "prev" method
            suffix_next = 'n', -- Suffix to search with "next" method
          },

          -- Number of lines within which surrounding is searched
          n_lines = 50,

          -- Whether to respect selection type:
          -- - Place surroundings on separate lines in linewise mode.
          -- - Place surroundings on each line in blockwise mode.
          respect_selection_type = false,

          -- How to search for surrounding (first inside current line, then inside
          -- neighborhood). One of 'cover', 'cover_or_next', 'cover_or_prev',
          -- 'cover_or_nearest', 'next', 'prev', 'nearest'. For more details,
          -- see `:h MiniSurround.config`.
          search_method = 'cover',

          -- Whether to disable showing non-error feedback
          -- This also affects (purely informational) helper messages shown after
          -- idle time if user input is required.
          silent = false,
        }
      )

      require('mini.pairs').setup {
        modes = { insert = true, command = true, terminal = true }, -- Defaults: true, false, false
      }

      require('mini.align').setup {
        -- Module mappings. Use `''` (empty string) to disable one.
        -- Modifiers changing alignment steps and/or options
        mappings = {
          start = 'ga',
          start_with_preview = 'gA',

          -- -- Main option modifiers
          -- ['s'] = --<function: enter split pattern>,
          -- ['j'] = --<function: choose justify side>,
          -- ['m'] = --<function: enter merge delimiter>,
          --
          -- -- Modifiers adding pre-steps
          -- ['f'] = --<function: filter parts by entering Lua expression>,
          -- ['i'] = --<function: ignore some split matches>,
          -- ['p'] = --<function: pair parts>,
          -- ['t'] = --<function: trim parts>,
          --
          -- -- Delete some last pre-step
          -- ['<BS>'] = --<function: delete some last pre-step>,
          --
          -- -- Special configurations for common splits
          -- ['='] = --<function: enhanced setup for '='>,
          -- [','] = --<function: enhanced setup for ','>,
          -- ['|'] = --<function: enhanced setup for '|'>,
          -- [' '] = --<function: enhanced setup for ' '>,
        },

        -- Default options controlling alignment process
        options = {
          split_pattern = '',
          justify_side = 'left',
          merge_delimiter = '',
        },

        -- Default steps performing alignment (if `nil`, default is used)
        steps = {
          pre_split = {},
          split = nil,
          pre_justify = {},
          justify = nil,
          pre_merge = {},
          merge = nil,
        },

        -- Whether to disable showing non-error feedback
        -- This also affects (purely informational) helper messages shown after
        -- idle time if user input is required.
        silent = false,
      }

      -- Simple and easy statusline.
      --  You could remove this setup call if you don't like it,
      --  and try some other statusline plugin
      local statusline = require 'mini.statusline'
      -- set use_icons to true if you have a Nerd Font
      statusline.setup { use_icons = vim.g.have_nerd_font }

      -- You can configure sections in the statusline by overriding their
      -- default behavior. For example, here we set the section for
      -- cursor location to LINE:COLUMN
      ---@diagnostic disable-next-line: duplicate-set-field
      statusline.section_location = function()
        return '%2l:%-2v'
      end

      -- ... and there is more!
      --  Check out: https://github.com/echasnovski/mini.nvim
    end,
  },
}
