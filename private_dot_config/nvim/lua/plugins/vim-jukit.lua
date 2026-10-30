return {
  'mathiaslovnes/vim-jukit',
  lazy = false,
  config = function()
    vim.g.jukit_terminal = 'tmux' -- Optional: Set terminal for plotting

    vim.g.jukit_mpl_style = vim.fn['jukit#util#plugin_path']() .. '/helpers/matplotlib-backend-kitty/backend.mplstyle'

    vim.g.jukit_savefig_dpi = 300
    -- IF KITTY OR TMUX IS USED:
    vim.g.jukit_inline_plotting = 0
    --    - Enable in-terminal-plotting. Only supported for kitty or tmux+iTerm2 -> BE SURE TO SPECIFY THE TERMINAL VIA `g:jukit_terminal`! (see variables in section 'Basic jukit options')
    vim.keymap.set("n", "<leader>nbc", ':call jukit#convert#notebook_convert("jupyter-notebook")<cr>') -- NoteBook Convert
    vim.keymap.set('n', '<leader>j', '<cmd>call jukit#cells#jump_to_next_cell()<CR>')
    vim.keymap.set('n', '<leader>k', '<cmd>call jukit#cells#jump_to_previous_cell()<CR>')

    -- Up/Down arrows jump between cells in Python files that contain jukit cells; plain arrows otherwise.
    -- Buffer-local so they take precedence over hardtime's global arrow mappings.
    vim.api.nvim_create_autocmd('FileType', {
      group = vim.api.nvim_create_augroup('jukit-arrow-cells', { clear = true }),
      pattern = 'python',
      callback = function(args)
        local function has_cells()
          return vim.fn.search('|%%--%%|', 'nw') ~= 0
        end
        vim.keymap.set({ 'n', 'x' }, '<Up>', function()
          return has_cells() and '<cmd>call jukit#cells#jump_to_previous_cell()<CR>' or '<Up>'
        end, { buffer = args.buf, expr = true, desc = 'Previous jukit cell' })
        vim.keymap.set({ 'n', 'x' }, '<Down>', function()
          return has_cells() and '<cmd>call jukit#cells#jump_to_next_cell()<CR>' or '<Down>'
        end, { buffer = args.buf, expr = true, desc = 'Next jukit cell' })
      end,
    })
    -- Replaces jukit's own <leader>cd (jukit skips its default map when one already calls jukit#cells#delete).
    -- Its delete fixes the ids of the wrong marker unless the cursor is in column 1, and in a file without
    -- cells it deletes everything, so jump to column 1 first and do nothing when there are no cells.
    vim.keymap.set('n', '<leader>cd', "<cmd>if search('|%%--%%|', 'nw') | call cursor(line('.'), 1) | call jukit#cells#delete() | endif<CR>", { desc = 'Delete jukit cell' })

    -- Run the current cell and every cell below it ("cells below"). jukit has no command for this, so this
    -- sends the code the way jukit#send#all does, but starting at the current cell instead of line 1.
    -- --md_cell_start makes jukit skip markdown cells, and -s saves each cell's output to the history.
    vim.keymap.set('n', '<leader>cb', function()
      if vim.fn['jukit#splits#split_exists']('output') == 0 then
        vim.notify('[vim-jukit] No split window found', vim.log.levels.WARN)
        return
      end
      -- jukit reads the cell ids from the markers in the sent code, so with no marker below
      -- (the last cell) just run this one cell
      if vim.fn.search('|%%--%%|', 'nW') == 0 then
        vim.fn['jukit#send#section'](0)
        return
      end
      local first = vim.fn.search('|%%--%%|', 'nbW') + 1 -- line after the marker above (1 in the first cell)
      local code = table.concat(vim.fn.getline(first, '$'), '\n')
      local md_start = vim.fn.escape(vim.fn['jukit#util#get_lang_info']()[1], '"')
      local param = vim.g.jukit_ipy_opts
      if vim.g.jukit_save_output == 1 then
        param = param .. ' -s'
      end
      param = param .. ' --md_cell_start=' .. md_start
      if vim.g.jukit_show_prompt == 1 then
        param = param .. ' -p'
      end
      vim.fn['jukit#util#ipython_info_write'] { cmd_opts = param, cmd = code }
      vim.fn['jukit#tmux#cmd#send_text'](vim.g.jukit_output_title, '%jukit_run_split')
    end, { desc = 'Run jukit cells from here to the end' })

    vim.keymap.set('n', '<leader>J', '<cmd>call jukit#splits#out_hist_scroll(1)<CR>')
    vim.keymap.set('n', '<leader>K', '<cmd>call jukit#splits#out_hist_scroll(0)<CR>')
    vim.keymap.set('n', '<leader><space>', '<cmd>call jukit#send#section(0)<CR>', { noremap = true, silent = true })
    vim.keymap.set('n', '!', '<cmd>call jukit#send#section(0)<CR>', { noremap = true, silent = true })

    vim.keymap.set('n', '_', '<cmd>call jukit#send#selection()<cr>')
    vim.keymap.set('n', '_', '<cmd><C-U>call jukit#send#selection()cr>')

    -- save to pdf -- rebind to dummy key
    vim.keymap.set('n', '<leader>_pdf', "<cmd>call jukit#convert#save_nb_to_file(0,1,'pdf')<cr>")
    -- set position and dimension of überzug window -- rebind to dummy key
    vim.keymap.set('n', '<leader>_pos', ':<cmd>call jukit#ueberzug#set_default_pos()<CR>')

    -- Enable markdown syntax highlighting in textcells
    vim.g.jukit_enable_textcell_syntax = 1

    -- Syntax file to use for textcells
    vim.g.jukit_text_syntax_file = vim.env.VIMRUNTIME .. '/syntax/markdown.vim'

    -- jukit adds the markdown highlighting for text cells on BufReadPost. When a file changes on disk (e.g.
    -- Claude Code edits it), nvim reloads it and fires FileType again *after* BufReadPost, which reloads the
    -- Python syntax and wipes jukit's region (:e fires them the other way round). So add it back afterwards.
    vim.api.nvim_create_autocmd('FileChangedShellPost', {
      group = vim.api.nvim_create_augroup('jukit-textcell-reload', { clear = true }),
      callback = function(args)
        vim.api.nvim_buf_call(args.buf, function()
          local ok, res = pcall(vim.api.nvim_exec2, 'syntax list textcell', { output = true })
          if not ok or res.output:find 'start=' then
            return -- jukit never ran, or the region survived (the file wasn't reloaded)
          end
          -- The function that adds the region is local to jukit's autoload/jukit.vim (s:textcell_syn_match),
          -- so call it through that script's id: <SNR>{id}_textcell_syn_match
          local script = vim.fn.getscriptinfo({ name = [[vim-jukit/autoload/jukit\.vim$]] })[1]
          if script then
            vim.fn[('<SNR>%d_textcell_syn_match'):format(script.sid)]()
          end
        end)
      end,
    })

    -- Extensions for which highlighting autocmds will be created
    vim.g.jukit_hl_ext_enabled = '*'

    vim.g.python3_host_prog = vim.fn.expand("~/.venvs/nvim/bin/python")

    -- Applied by lua/jukit_tmux_layout.lua: the jukit column goes to the far right of the tmux window
    -- and every column gets the same width
    vim.g.jukit_layout = {
      split = 'horizontal',
      p1 = 0.67, -- unused: columns are spread evenly instead
      val = {
        'file_content',
        {
          split = 'vertical',
          p1 = 0.5, -- 50% height for output, 50% for output_history
          val = { 'output', 'output_history' },
        },
      },
    }
  end,
}
