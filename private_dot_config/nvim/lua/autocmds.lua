-- ===================================================================
-- Autocmds
-- ===================================================================


-- Remove jdtls LSP progress notification on every keystroke
local original_progress = vim.lsp.handlers["$/progress"]

vim.lsp.handlers["$/progress"] = function(err, result, ctx, config)
  local client = vim.lsp.get_client_by_id(ctx.client_id)
  if client and client.name == "jdtls" then
    local msg = result.value and (result.value.message or "")
    if msg:match("Validate") or msg:match("Publish Diagnostics") then
      return
    end
  end
  if original_progress then
    return original_progress(err, result, ctx, config)
  end
end


-- Reload files changed on disk (Claude Code edits) when moving back into their window
vim.api.nvim_create_autocmd({ 'FocusGained', 'TermClose', 'TermLeave', 'WinEnter', 'BufEnter' }, {
  group = vim.api.nvim_create_augroup('checktime', { clear = true }),
  callback = function()
    if vim.o.buftype ~= 'nofile' and vim.fn.getcmdwintype() == '' then
      vim.cmd 'checktime'
    end
  end,
})

-- No hard-wrapping while typing past textwidth (filetype plugins like markdown add 't' back per buffer)
vim.api.nvim_create_autocmd('FileType', {
  callback = function()
    vim.opt_local.formatoptions:remove 't'
  end,
})

-- The command-line window (q:, <C-f>) runs a line with <CR>, not the global o<Esc> map
vim.api.nvim_create_autocmd('CmdwinEnter', {
  callback = function(a)
    vim.keymap.set('n', '<CR>', '<CR>', { buffer = a.buf, remap = false })
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

-- === Python ===
-- Disable all concealment in Python files
vim.api.nvim_create_autocmd('FileType', {
  pattern = 'python',
  callback = function()
    vim.opt_local.conceallevel = 0
  end,
})
