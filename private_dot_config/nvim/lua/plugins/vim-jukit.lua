return {
  'luk400/vim-jukit',
  ft = { 'python', 'ipynb' },
  config = function()
    vim.g.jukit_terminal = 'tmux' -- Optional: Set terminal for plotting
    vim.g.jukit_use_uberzug = 1
    vim.g.jukit_python_os_cmd = 'ipython'
    vim.g.jukit_output_new_os_window = 0
    vim.g.jukit_outhist_new_os_window = 0
    vim.g.jukit_matplotlib_backend = 'module://matplotlib-backend-kitty'
    vim.g.jukit_mpl_block = 0
    -- Highlight cell markers
    -- vim.g.jukit_highlight_markers = 1
    -- You can define the colors after loading your colorscheme:
    -- vim.cmd 'highlight jukit_cellmarker_colors guifg=#0000ff guibg=NONE'
    -- Highlight background of textcells
    vim.g.jukit_enable_textcell_bg_hl = 1
    -- You can define the background color like this:
    -- vim.cmd 'highlight jukit_textcell_bg_colors guibg=#131628 ctermbg=0'
    vim.g.jukit_text_syntax_file = '' -- empty disables legacy syntax

    -- Enable markdown syntax highlighting in textcells
    vim.g.jukit_enable_textcell_syntax = 1

    -- Enable highlighting for all extensions
    vim.g.jukit_hl_ext_enabled = '*'

    vim.g.jukit_ueberzug_pos = { 0.0, 0.0, 1.0, 1.0 } -- Lua table syntax (no [])
    vim.g.jukit_ueberzug_pos_noout = { 0.0, 0.0, 1.0, 1.0 }

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
