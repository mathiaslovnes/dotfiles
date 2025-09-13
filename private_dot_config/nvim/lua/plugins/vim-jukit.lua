return {
  'luk400/vim-jukit',
  ft = { 'python', 'ipynb' },
  config = function()
    vim.g.jukit_terminal = 'kitty' -- Optional: Set terminal for plotting
    vim.g.jukit_use_uberzug = 1
    vim.g.jukit_python_os_cmd = 'ipython'

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
  end,
}
