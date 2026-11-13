return {
  'nvim-treesitter/nvim-treesitter-textobjects',
  branch = 'main',
  init = function()
    -- Python's ftplugin maps ]m/]] itself; keep other filetypes' maps (git-rebase <C-a>, :Man q)
    vim.g.no_python_maps = true
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
          ['@function.outer'] = 'V',  -- linewise
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
    -- ] + letter jumps to the next node, [ + letter to the previous one (typed + and -, keymaps.lua), with the
    -- letter of the node's select below. Class is ]]/[[, since ]s/[s jump between misspellings (spell is on in tex).
    local move = require 'nvim-treesitter-textobjects.move'
    local function jumps(next_key, prev_key, query, name)
      vim.keymap.set({ 'n', 'x', 'o' }, next_key, function()
        move.goto_next(query, 'textobjects')
      end, { desc = 'Next ' .. name })
      vim.keymap.set({ 'n', 'x', 'o' }, prev_key, function()
        move.goto_previous(query, 'textobjects')
      end, { desc = 'Previous ' .. name })
    end
    jumps(']]', '[[', '@class.outer', 'class')
    jumps(']f', '[f', '@function.outer', 'function')
    jumps(']i', '[i', '@conditional.outer', 'conditional')
    jumps(']o', '[o', '@loop.outer', 'loop')
    jumps(']a', '[a', '@parameter.outer', 'parameter')
    jumps(']r', '[r', '@return.outer', 'return')
    jumps(']t', '[t', '@comment.outer', 'comment')
    jumps(']x', '[x', '@regex.outer', 'regex')

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

    -- conditional (i for if; ac/ic select a jukit cell, mini.lua)
    vim.keymap.set({ 'x', 'o' }, 'ai', function()
      require('nvim-treesitter-textobjects.select').select_textobject('@conditional.outer', 'textobjects')
    end)
    vim.keymap.set({ 'x', 'o' }, 'ii', function()
      require('nvim-treesitter-textobjects.select').select_textobject('@conditional.inner', 'textobjects')
    end)

    -- loop (o)
    vim.keymap.set({ 'x', 'o' }, 'ao', function()
      require('nvim-treesitter-textobjects.select').select_textobject('@loop.outer', 'textobjects')
    end)
    vim.keymap.set({ 'x', 'o' }, 'io', function()
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

    -- -- You can also pass a list to group multiple queries.
    -- vim.keymap.set({ 'n', 'x', 'o' }, ']o', function()
    --   require('nvim-treesitter-textobjects.move').goto_next_start({ '@loop.inner', '@loop.outer' }, 'textobjects')
    -- end)

    ---------------- KEYMAPS FOR SWAPPING ----------------
    -- move the parameter under the cursor right/left
    vim.keymap.set('n', '<leader>>', function()
      require('nvim-treesitter-textobjects.swap').swap_next '@parameter.inner'
    end, { desc = 'Swap parameter with the next one' })
    vim.keymap.set('n', '<leader><', function()
      require('nvim-treesitter-textobjects.swap').swap_previous '@parameter.inner'
    end, { desc = 'Swap parameter with the previous one' })
    -- ; and , are left to flash, which repeats f/t with them
  end,
}
