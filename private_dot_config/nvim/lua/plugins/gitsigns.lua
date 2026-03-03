-- Alternatively, use `config = function() ... end` for full control over the configuration.
-- If you prefer to call `setup` explicitly, use:
--    {
--        'lewis6991/gitsigns.nvim',
--        config = function()
--            require('gitsigns').setup({
--                -- Your gitsigns configuration here
--            })
--        end,
--    }
--
-- Here is a more advanced example where we pass configuration
-- options to `gitsigns.nvim`.
--
-- See `:help gitsigns` to understand what the configuration keys do
return {
  { -- Adds git related signs to the gutter, as well as utilities for managing changes
    'lewis6991/gitsigns.nvim',
    opts = {
      signs = {
        add = { text = '+' },
        change = { text = '~' },
        delete = { text = '_' },
        topdelete = { text = '‾' },
        changedelete = { text = '~' },
      },
      on_attach = function(bufnr)
        local gitsigns = require 'gitsigns'

        local function map(mode, l, r, opts)
          opts = opts or {}
          opts.buffer = bufnr
          vim.keymap.set(mode, l, r, opts)
        end

        -- Navigation
        map('n', '<leader>gc', function()
          if vim.wo.diff then
            vim.cmd.normal { '<leader>gc', bang = true }
          else
            gitsigns.nav_hunk 'next'
          end
        end, { desc = 'Jump to next [G]it [C]hange' })

        map('n', '<leader>gC', function()
          if vim.wo.diff then
            vim.cmd.normal { '<leader>gC', bang = true }
          else
            gitsigns.nav_hunk 'prev'
          end
        end, { desc = 'Jump to previous [G]it [C]hange' })

        -- Actions
        -- visual mode
        map('v', '<leader>hs', function()
          gitsigns.stage_hunk { vim.fn.line '.', vim.fn.line 'v' }
        end, { desc = '[H]unk [S]tage' })

        map('v', '<leader>hr', function()
          gitsigns.reset_hunk { vim.fn.line '.', vim.fn.line 'v' }
        end, { desc = '[H]unk [R]eset' })

        -- normal mode
        map('n', '<leader>hs', gitsigns.stage_hunk, { desc = 'Toggle [H]unk [S]tage' })
        map('n', '<leader>hp', gitsigns.preview_hunk, { desc = '[H]unk [P]review' })
        map('n', '<leader>hi', gitsigns.preview_hunk_inline, { desc = '[H]unk Preview [I]nline' })
        -- map('n', '<leader>gS', gitsigns.stage_buffer, { desc = '[G]it [S]tage buffer' })
        map('n', '<leader>gR', gitsigns.reset_buffer, { desc = '[G]it [R]eset buffer' })
        map('n', '<leader>gb', gitsigns.blame_line, { desc = '[G]it [B]lame line' })
        map('n', '<leader>gd', gitsigns.diffthis, { desc = '[G]it [D]iff (against index)' })
        -- diffthis() → working file vs index (what would be committed)
        -- diffthis('@') → working file vs HEAD (last commit)
        -- diffthis('~') → working file vs HEAD~1 (commit before last)
        map('n', '<leader>gD', function()
          gitsigns.diffthis '@'
        end, { desc = '[G]it [D]iff (against last commit)' })

        -- Toggles
        map('n', '<leader>tb', gitsigns.toggle_current_line_blame, { desc = '[T]oggle git show [b]lame line' })
        -- Shows deleted lines as virtual text in your buffer
        map('n', '<leader>tD', gitsigns.toggle_deleted, { desc = '[T]oggle git show [D]eleted' })

        -- Text object for hunks — lets you do things like vih (select inside hunk)
        map({ 'o', 'x' }, 'ih', gitsigns.select_hunk)
      end,
    },
  },
}
-- vim: ts=2 sts=2 sw=2 et
