-- ===================================================================
-- Highlight overrides
-- ===================================================================
-- Re-applied on every colorscheme load, so they work with any colorscheme and survive
-- reloads like the <leader>bg transparency toggle. Must be required before lazy-plugins,
-- otherwise the autocmd is registered after the colorscheme's first load and misses it.

local function apply()
  -- Flash yanked/put text like a search match
  vim.api.nvim_set_hl(0, 'YankyPut', { link = 'IncSearch' })
  vim.api.nvim_set_hl(0, 'YankyYanked', { link = 'IncSearch' })
  -- Flash substituted/exchanged text like a search match
  vim.api.nvim_set_hl(0, 'SubstituteSubstituted', { link = 'IncSearch' })
  vim.api.nvim_set_hl(0, 'SubstituteExchange', { link = 'IncSearch' })
  -- Python docstrings in the colorscheme's string color (green) instead of its docstring color
  vim.api.nvim_set_hl(0, '@string.documentation.python', { link = '@string' })
  -- Markdown text and code blocks green
  vim.api.nvim_set_hl(0, '@text.markdown', { fg = '#a6e3a1' })
  vim.api.nvim_set_hl(0, '@none.markdown', { fg = '#a6e3a1' })
  vim.api.nvim_set_hl(0, '@markup.markdown', { fg = '#a6e3a1' })
  vim.api.nvim_set_hl(0, 'RenderMarkdownCode', { fg = '#a6e3a1', bg = '#1e1e2e' })
  -- Debugger breakpoint signs
  vim.api.nvim_set_hl(0, 'DapBreak', { fg = '#e51400' })
  vim.api.nvim_set_hl(0, 'DapStop', { fg = '#ffcc00' })
  -- Jupyter cell dividers
  vim.api.nvim_set_hl(0, 'PyworksDivider', { fg = '#FFFFFF', bold = true })
end

vim.api.nvim_create_autocmd('ColorScheme', { callback = apply })
apply() -- Also covers running without any colorscheme
