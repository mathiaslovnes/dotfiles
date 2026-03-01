return {
  'L3MON4D3/LuaSnip',
  version = 'v2.*',
  build = 'make install_jsregexp',
  dependencies = { 'rafamadriz/friendly-snippets' },

  config = function()
    local ls = require 'luasnip'

    -- Freidnly-snippets
    require('luasnip.loaders.from_vscode').load {
      exclude = { '' }, -- Exclude languages you don't want
    }
    local s = ls.snippet
    local i = ls.insert_node
    local rep = require('luasnip.extras').rep
    local fmt = require('luasnip.extras.fmt').fmt

    -- 1. Keymaps (Inside config)
    vim.keymap.set({ 'i' }, '<C-X>', function()
      ls.expand()
    end, { silent = true })
    vim.keymap.set({ 'i', 's' }, '<C-F>', function()
      ls.jump(1)
    end, { silent = true })
    vim.keymap.set({ 'i', 's' }, '<C-B>', function()
      ls.jump(-1)
    end, { silent = true })

    -- 2. Add Snippets
    ls.add_snippets('tex', {
      -- Snippet 1: Base Template
      s(
        'basetext',
        fmt(
          [[
      \documentclass{{article}}
      \usepackage{{graphicx}}

      \begin{{document}}
      {}
      \end{{document}}
      ]],
          { i(1) }
        )
      ), -- Note the comma here!

      -- Snippet 2: Itemize
      s(
        'item',
        fmt(
          [[
      \begin{{itemize}}
        \item {}
      \end{{itemize}}
      ]],
          { i(1) }
        )
      ),

      -- Snippet 3: Adding Figure
      s(
        'fig',
        fmt(
          [[
    \begin{{figure}}[ht!]
      \centering
      \includegraphics[width=0.8\textwidth]{{{}}}
      \caption{{{}}}
      \label{{fig:{}}}
    \end{{figure}}
  ]],
          { i(1, 'filename'), i(2, 'caption'), i(3, 'label') }
        )
      ),

      -- Snippet 4: Adding Environment
      s(
        'env',
        fmt(
          [[
    \begin{{{}}}
      {}
    \end{{{}}}
  ]],
          { i(1), i(0), rep(1) }
        ) -- rep(1) repeats whatever you type in the first box
      ),
    })
  end,
}
