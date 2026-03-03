-- ===================================================================
-- Autocmds
-- ===================================================================

-- Regenerates helptags on startup
vim.api.nvim_create_autocmd('VimEnter', {
  callback = function()
    vim.cmd 'silent! helptags ALL'
  end,
})

-- Remove nvim autohighlighting word under cursor - replaced by illuminate.nvim - faster
vim.api.nvim_create_autocmd('LspAttach', {
  callback = function(args)
    local client = vim.lsp.get_client_by_id(args.data.client_id)
    if client then
      client.server_capabilities.documentHighlightProvider = false
    end
  end,
})

-- === Colorscheme ===
vim.api.nvim_create_autocmd('ColorScheme', {
  callback = function()
    -- Highlight yanking/putting/substituting/exchanging
    vim.api.nvim_set_hl(0, 'YankyPut', { link = 'IncSearch' })
    vim.api.nvim_set_hl(0, 'YankyYanked', { link = 'IncSearch' })
    -- Changes python documentation string color from blue to green
    vim.api.nvim_set_hl(0, '@string.documentation.python', { fg = '#a6e3a1' })
  end,
})

-- Make popups' background transparent
-- vim.api.nvim_create_autocmd('ColorScheme', {
--   callback = function()
--     vim.api.nvim_set_hl(0, 'NormalFloat', { bg = 'NONE' })
--     vim.api.nvim_set_hl(0, 'FloatBorder', { bg = 'NONE' })
--     vim.api.nvim_set_hl(0, 'FloatTitle', { bg = 'NONE' })
--     vim.api.nvim_set_hl(0, 'TelescopeNormal', { bg = 'NONE' })
--     vim.api.nvim_set_hl(0, 'TelescopeBorder', { bg = 'NONE' })
--   end,
-- })
--
-- -- Also set immediately for the current session
-- vim.api.nvim_set_hl(0, 'NormalFloat', { bg = 'NONE' })
-- vim.api.nvim_set_hl(0, 'FloatBorder', { bg = 'NONE' })
-- vim.api.nvim_set_hl(0, 'FloatTitle', { bg = 'NONE' })
-- vim.api.nvim_set_hl(0, 'TelescopeNormal', { bg = 'NONE' })
-- vim.api.nvim_set_hl(0, 'TelescopeBorder', { bg = 'NONE' })

-- Make rainbow highlights bold
local function make_rainbows_bold()
  for i = 1, 6 do
    local rainbow = vim.api.nvim_get_hl(0, { name = 'rainbow' .. i })
    if rainbow and next(rainbow) ~= nil then
      rainbow.bold = true
      vim.api.nvim_set_hl(0, 'rainbow' .. i, rainbow)
    end
  end
end

-- === Python ===
-- Disable all concealment in Python files
vim.api.nvim_create_autocmd('FileType', {
  pattern = 'python',
  callback = function()
    vim.opt_local.conceallevel = 0
  end,
})

-- Force bold headers - runs on multiple events
vim.api.nvim_create_autocmd({ 'BufEnter', 'FileType', 'BufWritePost', 'TextChanged', 'InsertLeave' }, {
  pattern = 'python',
  callback = function()
    vim.schedule(make_rainbows_bold)
  end,
})

-- Run it immediately for already-open buffers
if vim.bo.filetype == 'python' then
  vim.schedule(make_rainbows_bold)
end
