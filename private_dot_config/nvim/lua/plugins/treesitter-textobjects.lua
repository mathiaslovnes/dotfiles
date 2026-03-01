return {
  'nvim-treesitter/nvim-treesitter-textobjects',
  branch = 'main',
  init = function()
    -- Disable entire built-in ftplugin mappings to avoid conflicts.
    -- See https://github.com/neovim/neovim/tree/master/runtime/ftplugin for built-in ftplugins.
    vim.g.no_plugin_maps = true

    -- Or, disable per filetype (add as you like)
    -- vim.g.no_python_maps = true
    -- vim.g.no_ruby_maps = true
    -- vim.g.no_rust_maps = true
    -- vim.g.no_go_maps = true
  end,
  config = function()
    -- configuration
    require('nvim-treesitter-textobjects').setup {

      -- config for moving
      move = {
        -- whether to set jumps in the jumplist
        set_jumps = true,
      },

      -- config for selecting
      select = {
        -- Automatically jump forward to textobj, similar to targets.vim
        lookahead = true,
        -- You can choose the select mode (default is charwise 'v')
        --
        -- Can also be a function which gets passed a table with the keys
        -- * query_string: eg '@function.inner'
        -- * method: eg 'v' or 'o'
        -- and should return the mode ('v', 'V', or '<c-v>') or a table
        -- mapping query_strings to modes.
        selection_modes = {
          ['@parameter.outer'] = 'v', -- charwise
          ['@function.outer'] = 'V', -- linewise
          -- ['@class.outer'] = '<c-v>', -- blockwise
        },
        -- If you set this to `true` (default is `false`) then any textobject is
        -- extended to include preceding or succeeding whitespace. Succeeding
        -- whitespace has priority in order to act similarly to eg the built-in
        -- `ap`.
        --
        -- Can also be a function which gets passed a table with the keys
        -- * query_string: eg '@function.inner'
        -- * selection_mode: eg 'v'
        -- and should return true of false
        include_surrounding_whitespace = false,
      },
    }

    ---@diagnostic disable: undefined-global
    ---------------- KEYMAPS FOR MOVING ----------------
    -- You can use the capture groups defined in `textobjects.scm`
    -- class (s for structure)
    vim.keymap.set({ 'n', 'x', 'o' }, 'gs', function()
      require('nvim-treesitter-textobjects.move').goto_next('@class.outer', 'textobjects')
    end)
    vim.keymap.set({ 'n', 'x', 'o' }, 'gS', function()
      require('nvim-treesitter-textobjects.move').goto_previous('@class.outer', 'textobjects')
    end)

    -- function (f)
    vim.keymap.set({ 'n', 'x', 'o' }, 'gf', function()
      require('nvim-treesitter-textobjects.move').goto_next('@function.outer', 'textobjects')
    end)
    vim.keymap.set({ 'n', 'x', 'o' }, 'gF', function()
      require('nvim-treesitter-textobjects.move').goto_previous('@function.outer', 'textobjects')
    end)

    -- conditional (c)
    vim.api.nvim_create_autocmd('VimEnter', {
      callback = function()
        pcall(vim.keymap.del, 'n', 'gcc')
        pcall(vim.keymap.del, 'n', 'gc')
        pcall(vim.keymap.del, 'x', 'gc')

        vim.keymap.set({ 'n', 'x', 'o' }, 'gc', function()
          require('nvim-treesitter-textobjects.move').goto_next('@conditional.outer', 'textobjects')
        end, { noremap = true, nowait = true })
      end,
    })
    vim.keymap.set({ 'n', 'x', 'o' }, 'gC', function()
      require('nvim-treesitter-textobjects.move').goto_previous('@conditional.outer', 'textobjects')
    end)

    -- loop (l)
    vim.keymap.set({ 'n', 'x', 'o' }, 'gl', function()
      require('nvim-treesitter-textobjects.move').goto_next('@loop.outer', 'textobjects')
    end)
    vim.keymap.set({ 'n', 'x', 'o' }, 'gL', function()
      require('nvim-treesitter-textobjects.move').goto_previous('@loop.outer', 'textobjects')
    end)

    -- parameter (a for argument)
    vim.keymap.set({ 'n', 'x', 'o' }, 'ga', function()
      require('nvim-treesitter-textobjects.move').goto_next('@parameter.outer', 'textobjects')
    end)
    vim.keymap.set({ 'n', 'x', 'o' }, 'gA', function()
      require('nvim-treesitter-textobjects.move').goto_previous('@parameter.outer', 'textobjects')
    end)

    -- call (e for execute)
    vim.keymap.set({ 'n', 'x', 'o' }, 'ge', function()
      require('nvim-treesitter-textobjects.move').goto_next('@call.outer', 'textobjects')
    end)
    vim.keymap.set({ 'n', 'x', 'o' }, 'gE', function()
      require('nvim-treesitter-textobjects.move').goto_previous('@call.outer', 'textobjects')
    end)

    -- return (r)
    vim.keymap.set({ 'n', 'x', 'o' }, 'gr', function()
      require('nvim-treesitter-textobjects.move').goto_next('@return.outer', 'textobjects')
    end)
    vim.keymap.set({ 'n', 'x', 'o' }, 'gR', function()
      require('nvim-treesitter-textobjects.move').goto_previous('@return.outer', 'textobjects')
    end)

    -- comment (t for text)
    vim.keymap.set({ 'n', 'x', 'o' }, 'gt', function()
      require('nvim-treesitter-textobjects.move').goto_next('@comment.outer', 'textobjects')
    end)
    vim.keymap.set({ 'n', 'x', 'o' }, 'gT', function()
      require('nvim-treesitter-textobjects.move').goto_previous('@comment.outer', 'textobjects')
    end)

    -- regex (x)
    vim.keymap.set({ 'n', 'x', 'o' }, 'gx', function()
      require('nvim-treesitter-textobjects.move').goto_next('@regex.outer', 'textobjects')
    end)
    vim.keymap.set({ 'n', 'x', 'o' }, 'gX', function()
      require('nvim-treesitter-textobjects.move').goto_previous('@regex.outer', 'textobjects')
    end)

    -- number (n)
    vim.keymap.set({ 'n', 'x', 'o' }, 'gn', function()
      require('nvim-treesitter-textobjects.move').goto_next('@number.outer', 'textobjects')
    end)
    vim.keymap.set({ 'n', 'x', 'o' }, 'gN', function()
      require('nvim-treesitter-textobjects.move').goto_previous('@number.outer', 'textobjects')
    end)

    ---------------- KEYMAPS FOR SELECTING ----------------
    -- You can use the capture groups defined in `textobjects.scm`
    -- class (s for structure)
    vim.keymap.set({ 'x', 'o' }, 'as', function()
      require('nvim-treesitter-textobjects.select').select_textobject('@class.outer', 'textobjects')
    end)
    vim.keymap.set({ 'x', 'o' }, 'is', function()
      require('nvim-treesitter-textobjects.select').select_textobject('@class.inner', 'textobjects')
    end)

    -- function (f)
    vim.keymap.set({ 'x', 'o' }, 'af', function()
      require('nvim-treesitter-textobjects.select').select_textobject('@function.outer', 'textobjects')
    end)
    vim.keymap.set({ 'x', 'o' }, 'if', function()
      require('nvim-treesitter-textobjects.select').select_textobject('@function.inner', 'textobjects')
    end)

    -- conditional (c)
    vim.keymap.set({ 'x', 'o' }, 'ac', function()
      require('nvim-treesitter-textobjects.select').select_textobject('@conditional.outer', 'textobjects')
    end)
    vim.keymap.set({ 'x', 'o' }, 'ic', function()
      require('nvim-treesitter-textobjects.select').select_textobject('@conditional.inner', 'textobjects')
    end)

    -- loop (l)
    vim.keymap.set({ 'x', 'o' }, 'al', function()
      require('nvim-treesitter-textobjects.select').select_textobject('@loop.outer', 'textobjects')
    end)
    vim.keymap.set({ 'x', 'o' }, 'il', function()
      require('nvim-treesitter-textobjects.select').select_textobject('@loop.inner', 'textobjects')
    end)

    -- parameter (a for argument)
    vim.keymap.set({ 'x', 'o' }, 'aa', function()
      require('nvim-treesitter-textobjects.select').select_textobject('@parameter.outer', 'textobjects')
    end)
    vim.keymap.set({ 'x', 'o' }, 'ia', function()
      require('nvim-treesitter-textobjects.select').select_textobject('@parameter.inner', 'textobjects')
    end)

    -- call (e for execute)
    vim.keymap.set({ 'x', 'o' }, 'ae', function()
      require('nvim-treesitter-textobjects.select').select_textobject('@call.outer', 'textobjects')
    end)
    vim.keymap.set({ 'x', 'o' }, 'ie', function()
      require('nvim-treesitter-textobjects.select').select_textobject('@call.inner', 'textobjects')
    end)

    -- return (r)
    vim.keymap.set({ 'x', 'o' }, 'ar', function()
      require('nvim-treesitter-textobjects.select').select_textobject('@return.outer', 'textobjects')
    end)
    vim.keymap.set({ 'x', 'o' }, 'ir', function()
      require('nvim-treesitter-textobjects.select').select_textobject('@return.inner', 'textobjects')
    end)

    -- comments (t for text)
    vim.keymap.set({ 'x', 'o' }, 'at', function()
      require('nvim-treesitter-textobjects.select').select_textobject('@comment.outer', 'textobjects')
    end)
    vim.keymap.set({ 'x', 'o' }, 'it', function()
      require('nvim-treesitter-textobjects.select').select_textobject('@comment.inner', 'textobjects')
    end)

    -- regex (x)
    vim.keymap.set({ 'x', 'o' }, 'ax', function()
      require('nvim-treesitter-textobjects.select').select_textobject('@regex.outer', 'textobjects')
    end)
    vim.keymap.set({ 'x', 'o' }, 'ix', function()
      require('nvim-treesitter-textobjects.select').select_textobject('@regex.inner', 'textobjects')
    end)

    -- numbers (n)
    vim.keymap.set({ 'x', 'o' }, 'an', function()
      require('nvim-treesitter-textobjects.select').select_textobject('@number.inner', 'textobjects')
    end)

    -- -- You can also pass a list to group multiple queries.
    -- vim.keymap.set({ 'n', 'x', 'o' }, ']o', function()
    --   require('nvim-treesitter-textobjects.move').goto_next_start({ '@loop.inner', '@loop.outer' }, 'textobjects')
    -- end)

    ---------------- KEYMAPS FOR SWAPPING ----------------
    -- === With <leader> ===
    -- swap (w - n/p for next/previous)
    vim.keymap.set('n', '<leader>wn', function()
      require('nvim-treesitter-textobjects.swap').swap_next '@parameter.inner'
    end)
    vim.keymap.set('n', '<leader>wp', function()
      require('nvim-treesitter-textobjects.swap').swap_previous '@parameter.inner'
    end)
    -- swap (w for next, W for previous)
    vim.keymap.set('n', '<leader>w', function()
      require('nvim-treesitter-textobjects.swap').swap_next '@parameter.inner'
    end)
    vim.keymap.set('n', '<leader>W', function()
      require('nvim-treesitter-textobjects.swap').swap_previous '@parameter.inner'
    end)
    -- === With g ===
    -- swap (w - n/p for next/previous)
    vim.keymap.set('n', 'gwn', function()
      require('nvim-treesitter-textobjects.swap').swap_next '@parameter.inner'
    end)
    vim.keymap.set('n', 'gwp', function()
      require('nvim-treesitter-textobjects.swap').swap_previous '@parameter.inner'
    end)
    -- swap (w for next, W for previous)
    vim.keymap.set('n', 'gw', function()
      require('nvim-treesitter-textobjects.swap').swap_next '@parameter.inner'
    end)
    vim.keymap.set('n', 'gW', function()
      require('nvim-treesitter-textobjects.swap').swap_previous '@parameter.inner'
    end)

    -- Repeat movement with ; and ,
    -- ensure ; goes forward and , goes backward regardless of the last direction
    local ts_repeat_move = require 'nvim-treesitter-textobjects.repeatable_move'
    vim.keymap.set({ 'n', 'x', 'o' }, ';', ts_repeat_move.repeat_last_move_next)
    vim.keymap.set({ 'n', 'x', 'o' }, ',', ts_repeat_move.repeat_last_move_previous)

    -- vim way: ; goes to the direction you were moving.
    -- vim.keymap.set({ "n", "x", "o" }, ";", ts_repeat_move.repeat_last_move)
    -- vim.keymap.set({ "n", "x", "o" }, ",", ts_repeat_move.repeat_last_move_opposite)
  end,
}
