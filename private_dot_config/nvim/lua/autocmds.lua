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

-- Claude Code also edits while you stay in its pane, so check every second too. Only buffers without unsaved
-- changes: those reload silently (autoread), while a changed one would interrupt typing with a prompt
vim.uv.new_timer():start(1000, 1000, vim.schedule_wrap(function()
  if vim.fn.mode():match '^[cr]' or vim.fn.getcmdwintype() ~= '' then
    return
  end
  for _, buf in ipairs(vim.api.nvim_list_bufs()) do
    if vim.api.nvim_buf_is_loaded(buf) and vim.bo[buf].buftype == '' and not vim.bo[buf].modified
      and vim.api.nvim_buf_get_name(buf) ~= '' then
      vim.cmd('silent! checktime ' .. buf)
    end
  end
end))

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
-- Overleaf compiles from the project root, so \input and \usepackage paths are relative to it, while vimtex
-- uses the main file's folder. In Overleaf clones a .texlabroot file marks the root (texlab reads it too):
-- point vimtex's file lookups (kpsewhich, through TEXINPUTS) and texcount there for the current buffer.
-- Before FileType too, since vimtex caches failed lookups when it starts in a buffer.
local texinputs = vim.env.TEXINPUTS
vim.api.nvim_create_autocmd({ 'BufReadPre', 'BufNewFile', 'BufEnter' }, {
  pattern = '*.tex',
  callback = function(a)
    local root = vim.fs.root(a.buf, '.texlabroot')
    vim.env.TEXINPUTS = root and root .. ':' .. (texinputs or '') or texinputs
    vim.g.vimtex_texcount_custom_arg = root and vim.fn.shellescape('-dir=' .. root .. '/') or ''
  end,
})

vim.api.nvim_create_autocmd('FileType', {
  pattern = 'tex',
  callback = function(a)
    vim.opt_local.conceallevel = 2 -- snacks.image hides the source behind rendered math only when conceal is on
    vim.opt_local.spell = true
    vim.opt_local.spelllang = 'en_us'
    vim.keymap.set('n', '<leader>wc', '<Cmd>VimtexCountWords!<CR>', { buffer = a.buf, desc = 'Word count per file' })
    vim.keymap.set('x', '<leader>wc', ':VimtexCountWords<CR>', { buffer = a.buf, desc = 'Word count (selection)' })
  end,
})

-- latexmk only rebuilds when a file's contents change, so a save without edits gets no compile message:
-- while vimtex's compiler is watching, report the last build's result instead
vim.api.nvim_create_autocmd('BufWritePre', {
  pattern = '*.tex',
  callback = function(a)
    vim.b[a.buf].tex_save_unchanged = not vim.bo[a.buf].modified
  end,
})
vim.api.nvim_create_autocmd('BufWritePost', {
  pattern = '*.tex',
  callback = function(a)
    if not vim.b[a.buf].tex_save_unchanged then
      return
    end
    vim.api.nvim_buf_call(a.buf, function()
      local ok, running = pcall(vim.fn.eval, 'b:vimtex.compiler.is_running()')
      if not ok or running == 0 then
        return
      end
      local status = vim.fn.eval 'b:vimtex.compiler.status' -- 1 building, 2 succeeded, 3 failed
      if status == 2 then
        vim.notify('No changes: PDF is up to date', vim.log.levels.INFO, { title = 'VimTeX' })
      elseif status == 3 then
        vim.notify('No changes: last build failed (<Space>le lists the errors)', vim.log.levels.WARN, { title = 'VimTeX' })
      end
    end)
  end,
})
