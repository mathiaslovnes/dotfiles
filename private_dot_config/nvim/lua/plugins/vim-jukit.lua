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

    -- save to pdf -- rebind to dummy key
    vim.keymap.set('n', '<leader>_pdf', "<cmd>call jukit#convert#save_nb_to_file(0,1,'pdf')<cr>")
    -- set position and dimension of überzug window -- rebind to dummy key
    vim.keymap.set('n', '<leader>_pos', ':<cmd>call jukit#ueberzug#set_default_pos()<CR>')

    -- Enable markdown syntax highlighting in textcells
    vim.g.jukit_enable_textcell_syntax = 1

    -- Syntax file to use for textcells
    vim.g.jukit_text_syntax_file = vim.env.VIMRUNTIME .. '/syntax/markdown.vim'

    -- Extensions for which highlighting autocmds will be created
    vim.g.jukit_hl_ext_enabled = '*'

    vim.g.python3_host_prog = vim.fn.exepath("python3")

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
