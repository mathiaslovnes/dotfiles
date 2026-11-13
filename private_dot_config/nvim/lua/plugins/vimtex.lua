-- Pick the main document, like Overleaf's "Main document" setting. Candidates are the files with \documentclass
-- from the current file's folder up to the project root. The choice is saved as an empty <main>.tex.latexmain
-- marker, which vimtex reads before guessing (*.latexmain is in ~/.gitignore_global).
local function choose_main()
  local dir = vim.fn.expand '%:p:h'
  local root = vim.fs.root(0, { '.texlabroot', '.git' }) or dir
  local dirs, mains = {}, {}
  for d in vim.fs.parents(dir .. '/x') do
    dirs[#dirs + 1] = d
    for _, f in ipairs(vim.fn.glob(d .. '/*.tex', false, true)) do
      for _, line in ipairs(vim.fn.readfile(f, '', 50)) do
        if line:match '^%s*\\documentclass' then
          mains[#mains + 1] = f
          break
        end
      end
    end
    if d == root then
      break
    end
  end
  if #mains == 0 then
    return vim.notify('No file with \\documentclass above ' .. dir, vim.log.levels.WARN, { title = 'VimTeX' })
  end

  local current = vim.fn.eval 'get(get(b:, "vimtex", {}), "tex", "")'
  vim.ui.select(mains, {
    prompt = 'Main document',
    format_item = function(f)
      return vim.fn.fnamemodify(f, ':h:t') .. '/' .. vim.fn.fnamemodify(f, ':t') .. (f == current and '  (current)' or '')
    end,
  }, function(main)
    if not main then
      return
    end
    for _, d in ipairs(dirs) do
      for _, marker in ipairs(vim.fn.glob(d .. '/*.latexmain', false, true)) do
        os.remove(marker)
      end
    end
    vim.fn.writefile({}, main .. '.latexmain')

    -- re-detect the main file in the open LaTeX buffers it covers
    local main_dir = vim.fs.dirname(main) .. '/'
    for _, buf in ipairs(vim.api.nvim_list_bufs()) do
      if vim.api.nvim_buf_is_loaded(buf) and vim.bo[buf].filetype == 'tex' and vim.startswith(vim.api.nvim_buf_get_name(buf), main_dir) then
        vim.api.nvim_buf_call(buf, function()
          if vim.fn.eval 'get(get(b:, "vimtex", {}), "tex", "")' ~= main then
            vim.cmd 'VimtexReloadState'
          end
        end)
      end
    end
    vim.notify('Main document: ' .. vim.fn.fnamemodify(main, ':t'), vim.log.levels.INFO, { title = 'VimTeX' })
  end)
end

return {
  'lervag/vimtex',
  lazy = false, -- we don't want to lazy load VimTeX
  -- tag = "v2.15", -- uncomment to pin to a specific release
  init = function()
    -- VimTeX configuration goes here, e.g.
    vim.g.vimtex_view_method = 'skim'
    vim.g.vimtex_view_skim_sync = 1 -- Skim jumps to the cursor after every successful build
    vim.g.vimtex_view_skim_reading_bar = 1 -- and highlights that line

    vim.g.vimtex_compiler_latexmk = {
      aux_dir = '.texfiles', -- create a directory called aux that will contain all the auxiliary files
      out_dir = '.texfiles',
    }

    -- Own keys, mapped before vimtex sets its defaults so it skips the ones they replace (ll, lS, lT, lm)
    vim.api.nvim_create_autocmd('User', {
      pattern = 'VimtexEventInitPre',
      callback = function()
        local function map(lhs, rhs, desc)
          vim.keymap.set('n', '<localleader>' .. lhs, rhs, { buffer = 0, remap = true, desc = desc })
        end
        map('ls', '<plug>(vimtex-compile)', 'LaTeX: start/stop compiling on save')
        map('lb', '<plug>(vimtex-compile-ss)', 'LaTeX: build once')
        map('lt', '<plug>(vimtex-toc-toggle)', 'LaTeX: toggle table of contents')
        map('lm', choose_main, 'LaTeX: choose main document')
      end,
    })
  end,
}
