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

    -- Own keys, mapped before vimtex sets its defaults so it skips the ones they replace (ll, lS, lT)
    vim.api.nvim_create_autocmd('User', {
      pattern = 'VimtexEventInitPre',
      callback = function()
        local function map(lhs, rhs, desc)
          vim.keymap.set('n', '<localleader>' .. lhs, rhs, { buffer = 0, remap = true, desc = desc })
        end
        map('ls', '<plug>(vimtex-compile)', 'LaTeX: start/stop compiling on save')
        map('lb', '<plug>(vimtex-compile-ss)', 'LaTeX: build once')
        map('lt', '<plug>(vimtex-toc-toggle)', 'LaTeX: toggle table of contents')
      end,
    })
  end,
}
