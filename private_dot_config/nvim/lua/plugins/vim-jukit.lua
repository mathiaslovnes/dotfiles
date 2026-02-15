return {
  'mathiaslovnes/vim-jukit',
  ft = { 'python', 'ipynb' },
  config = function()
    vim.g.jukit_terminal = 'tmux' -- Optional: Set terminal for plotting

    vim.g.jukit_mpl_style = vim.fn['jukit#util#plugin_path']() .. '/helpers/matplotlib-backend-kitty/backend.mplstyle'

    vim.g.jukit_savefig_dpi = 300
    -- IF KITTY OR TMUX IS USED:
    vim.g.jukit_inline_plotting = 0
    --    - Enable in-terminal-plotting. Only supported for kitty or tmux+iTerm2 -> BE SURE TO SPECIFY THE TERMINAL VIA `g:jukit_terminal`! (see variables in section 'Basic jukit options')
    vim.keymap.set('n', '<leader>j', '<cmd>call jukit#cells#jump_to_next_cell()<CR>')
    vim.keymap.set('n', '<leader>k', '<cmd>call jukit#cells#jump_to_previous_cell()<CR>')
    vim.keymap.set('n', '<leader>J', '<cmd>call jukit#splits#out_hist_scroll(1)<CR>')
    vim.keymap.set('n', '<leader>K', '<cmd>call jukit#splits#out_hist_scroll(0)<CR>')
    vim.keymap.set('n', '<leader><space>', '<cmd>call jukit#send#section(0)<CR>', { noremap = true, silent = true })
    vim.keymap.set('n', '!', '<cmd>call jukit#send#section(0)<CR>', { noremap = true, silent = true })

    vim.keymap.set('n', '_', '<cmd>call jukit#send#selection()<cr>')
    vim.keymap.set('n', '_', '<cmd><C-U>call jukit#send#selection()cr>')

    vim.keymap.set('n', '<leader>_pdf', "<cmd>call jukit#convert#save_nb_to_file(0,1,'pdf')<cr>")
    -- save to pdf -- rebind to dummy key
    vim.keymap.set('n', '<leader>_pos', ':<cmd>call jukit#ueberzug#set_default_pos()<CR>')
    -- set position and dimension of überzug window -- rebind to dummy key

    -- Whether to highlight cell markers
    vim.g.jukit_highlight_markers = 0

    -- Whether to highlight background of textcells
    vim.g.jukit_enable_textcell_bg_hl = 0
    -- vim.cmd("highlight jukit_textcell_bg_colors guibg=#131628 ctermbg=0")

    -- Enable markdown syntax highlighting in textcells
    vim.g.jukit_enable_textcell_syntax = 1

    -- Syntax file to use for textcells
    vim.g.jukit_text_syntax_file = vim.env.VIMRUNTIME .. '/syntax/markdown.vim'

    -- Extensions for which highlighting autocmds will be created
    vim.g.jukit_hl_ext_enabled = '*'

    vim.g.jukit_highlight_markers = 1
    -- Whether to highlight cell markers or not. You can specify the colors of cell markers by putting e.g. `highlight jukit_cellmarker_colors guifg=#1d615a guibg=#1d615a ctermbg=22 ctermfg=22` with your desired colors in your (neo)vim config. Make sure to define this highlight *after* loading a colorscheme in your (neo)vim config
    vim.g.jukit_enable_textcell_bg_hl = 1
    -- Whether to highlight background of textcells. You can specify the color by putting `highlight jukit_textcell_bg_colors guibg=#131628 ctermbg=0` with your desired colors in your (neo)vim config. Make sure to define this highlight group *after* loading a colorscheme in your (neo)vim config.

    vim.g.jukit_layout = {
      split = 'horizontal',
      p1 = 0.67, -- 50% for file_content, 50% for the vertical split
      val = {
        'file_content',
        {
          split = 'vertical',
          p1 = 0.5, -- 60% for output, 40% for output_history
          val = { 'output', 'output_history' },
        },
      },
    }
  end,
}
