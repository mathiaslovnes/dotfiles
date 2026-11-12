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


-- Treesitter highlighting and indent for every buffer with a parser, jukit notebooks included (their
-- text cells get markdown from after/queries/python/injections.scm instead of jukit's vim syntax)
vim.api.nvim_create_autocmd('FileType', {
  group = vim.api.nvim_create_augroup('treesitter-start', { clear = true }),
  callback = function(a)
    local lang = vim.treesitter.language.get_lang(a.match)
    if not lang or lang == 'latex' or lang == 'tmux' then
      return
    end
    if pcall(vim.treesitter.start, a.buf, lang) then
      -- without an indents query treesitter indents every line to column 0 (vim, diff, vimdoc)
      if vim.treesitter.query.get(lang, 'indents') then
        vim.bo[a.buf].indentexpr = "v:lua.require'nvim-treesitter'.indentexpr()"
      end
      if lang == 'markdown' then
        vim.bo[a.buf].syntax = 'ON' -- regex syntax too, as additional_vim_regex_highlighting did
      end
    end
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

-- === LaTeX ===
-- vimtex's word count, with texcount resolving \input paths from the folder TeX compiles in.
-- Overleaf compiles from the project root, which .texlabroot marks in Overleaf clones (texlab reads it too).
local function tex_word_count(range)
  local root = vim.fs.root(0, '.texlabroot')
  local arg = vim.g.vimtex_texcount_custom_arg or ''
  if root then
    vim.g.vimtex_texcount_custom_arg = arg .. ' ' .. vim.fn.shellescape('-dir=' .. root .. '/')
  end
  local ok, err = pcall(vim.fn['vimtex#misc#wordcount_display'], range and { range = range } or vim.empty_dict())
  vim.g.vimtex_texcount_custom_arg = arg
  if not ok then
    error(err)
  end
end

vim.api.nvim_create_autocmd('FileType', {
  pattern = 'tex',
  callback = function(a)
    vim.opt_local.conceallevel = 2 -- snacks.image hides the source behind rendered math only when conceal is on
    vim.opt_local.spell = true
    vim.opt_local.spelllang = 'en_us'
    vim.keymap.set('n', '<leader>wc', tex_word_count, { buffer = a.buf, desc = 'Word count (document)' })
    vim.keymap.set('x', '<leader>wc', function()
      local from, to = vim.fn.line 'v', vim.fn.line '.'
      vim.api.nvim_feedkeys(vim.keycode '<Esc>', 'nx', false)
      tex_word_count { math.min(from, to), math.max(from, to) }
    end, { buffer = a.buf, desc = 'Word count (selection)' })
  end,
})
