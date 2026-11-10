return {
  { -- Collection of various small independent plugins/modules
    'echasnovski/mini.nvim',
    config = function()
      require('mini.icons').setup()
      -- The mock function makes mini.icons pretend to be nvim-web-devicons so any plugin that calls nvim-web-devicons gets mini.icons instead. You can verify it's working by running:
      require('mini.icons').mock_nvim_web_devicons()

      require('mini.operators').setup {
        -- Each entry configures one operator.
        -- `prefix` defines keys mapped during `setup()`: in Normal mode
        -- to operate on textobject and line, in Visual - on selection.

        -- Evaluate text and replace with output
        evaluate = {
          prefix = 'g=',

          -- Function which does the evaluation
          func = nil,
        },

        -- Exchange text regions
        exchange = {
          prefix = '', -- Replaced by substitute.nvim because of buggy x/y marker additions

          -- Whether to reindent new text to match previous indent
          reindent_linewise = true,
        },

        -- Multiply (duplicate) text
        multiply = {
          prefix = '<leader>m',

          -- Function which can modify text before multiplying
          func = nil,
        },

        -- Replace text with register
        replace = {
          prefix = '<leader>r',

          -- Whether to reindent new text to match previous indent
          reindent_linewise = true,
        },

        -- Sort text
        sort = {
          prefix = '<leader>os',

          -- Function which does the sort
          func = nil,
        },
      }

      require('mini.splitjoin').setup {
        -- Module mappings. Use `''` (empty string) to disable one.
        -- Created for both Normal and Visual modes.
        mappings = {
          toggle = '<leader>S',
          split = '',
          join = '',
        },
      }

      -- Figures out hich buffer to show in window(s) after its current buffer is removed is decided by the algorithm:
      -- If alternate buffer is listed, use it.
      -- If previous listed buffer is different, use it.
      -- Otherwise create a scratch one with nvim_create_buf(true, true) and use it.
      require('mini.bufremove').setup {
        -- Whether to disable showing non-error feedback
        silent = false,
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

        custom_textobjects = {
          -- jukit cell: `ic` body, `ac` body plus its opening marker. The marker search is anchored to
          -- the line start, so a marker line belongs to the cell it opens. In an empty cell only
          -- the `c` operator gets an object: a new blank body line (mini.ai can't cancel `c`, which would
          -- otherwise type into the marker line); d/y/v find nothing
          c = function(ai_type)
            local marker = [[^#\s*|%%--%%|]]
            local above = vim.fn.search(marker, 'bcnW') -- 0 in the first cell
            local below = vim.fn.search(marker, 'nW') -- 0 in the last cell
            local from = (ai_type == 'a' and above > 0) and above or above + 1
            local to = below == 0 and vim.fn.line '$' or below - 1
            if from > to then
              if vim.v.operator ~= 'c' then
                return nil
              end
              vim.fn.append(above, '')
              return { from = { line = above + 1, col = 1 }, to = { line = above + 1, col = 1 }, vis_mode = 'V' }
            end
            return {
              from = { line = from, col = 1 },
              to = { line = to, col = math.max(vim.fn.col { to, '$' } - 1, 1) },
              vis_mode = 'V',
            }
          end,
        },

        -- Module mappings. Use `''` (empty string) to disable one.
        mappings = {
          -- Main textobject prefixes
          around = 'a',
          inside = 'i',

          -- Next/last variants
          -- NOTE: These override built-in LSP selection mappings on Neovim>=0.12
          -- Map LSP selection manually to use it (see `:h MiniAi.config`)
          around_last = 'al',
          inside_last = 'il',
          around_next = 'an',
          inside_next = 'in',

          -- Move cursor to corresponding edge of `a` textobject (off: f/t do the same jumps)
          goto_left = '',
          goto_right = '',
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
          highlight_duration = 1000,

          -- Module mappings. Use `''` (empty string) to disable one.
          mappings = {
            add = 'sa', -- Add surrounding in Normal and Visual modes
            delete = 'sd', -- Delete surrounding
            highlight = 'sh', -- Highlight surrounding
            replace = 'sr', -- Replace surrounding

            suffix_last = 'l', -- Suffix to search with "prev" method
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
          search_method = 'cover_or_next',

          -- Whether to disable showing non-error feedback
          -- This also affects (purely informational) helper messages shown after
          -- idle time if user input is required.
          silent = false,
        }
      )

      require('mini.pairs').setup {
        modes = { insert = true, command = false, terminal = false }, -- Defaults: true, false, false
      }

      -- Only add the closing half before whitespace, at line end, or before a closing bracket that has its
      -- opener. neigh_pattern only sees one character on each side, so check it in MiniPairs.open,
      -- which every opening key goes through.
      local open_pair = MiniPairs.open
      local brackets = { [')'] = { '(', ')' }, [']'] = { '\\[', '\\]' }, ['}'] = { '{', '}' } }
      MiniPairs.open = function(pair, neigh_pattern)
        local line = vim.api.nvim_get_current_line()
        local col = vim.fn.col '.'
        local open_char = pair:sub(1, 1)
        -- A quote with an odd number of unescaped ones before it on the line closes the last of them
        local _, count_before = line:sub(1, col - 1):gsub('\\.', ''):gsub(vim.pesc(open_char), '')
        if open_char == pair:sub(2, 2) and count_before % 2 == 1 then
          return open_char
        end
        local right = line:sub(col, col)
        local bracket = brackets[right]
        local has_opener = bracket and vim.fn.searchpair(bracket[1], '', bracket[2], 'bnW', '', 0, 50) > 0
        if right == '' or right:match '%s' or has_opener then
          return open_pair(pair, neigh_pattern)
        end
        return open_char
      end

      require('mini.align').setup {
        -- Module mappings. Use `''` (empty string) to disable one.
        -- Modifiers changing alignment steps and/or options
        mappings = {
          start = '', -- ga/gA are treesitter's parameter jumps
          start_with_preview = '',

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

      -- ... and there is more!
      --  Check out: https://github.com/echasnovski/mini.nvim
    end,
  },
}
