return {
  'linux-cultist/venv-selector.nvim',
  dependencies = {
    'neovim/nvim-lspconfig',
    { 'nvim-telescope/telescope.nvim', branch = '0.1.x', dependencies = { 'nvim-lua/plenary.nvim' } }, -- optional: you can also use fzf-lua, snacks, mini-pick instead.
  },
  ft = 'python', -- Load when opening Python files
  keys = {
    { '<leader>ve', '<cmd>VenvSelect<cr>' }, -- Open picker on keymap
  },
  opts = { -- this can be an empty lua table - just showing below for clarity.
    search = {}, -- if you add your own searches, they go here.
    options = {

      on_venv_activate_callback = nil, -- callback function for after a venv activates
      enable_default_searches = true, -- switches all default searches on/off
      enable_cached_venvs = true, -- use cached venvs that are activated automatically when a python file is registered with the LSP.
      cached_venv_automatic_activation = true, -- if set to false, the VenvSelectCached command becomes available to manually activate them.
      activate_venv_in_terminal = true, -- activate the selected python interpreter in terminal windows opened from neovim
      set_environment_variables = true, -- sets VIRTUAL_ENV or CONDA_PREFIX environment variables
      notify_user_on_venv_activation = false, -- notifies user on activation of the virtual env
      search_timeout = 5, -- if a search takes longer than this many seconds, stop it and alert the user
      debug = false, -- enables you to run the VenvSelectLog command to view debug logs
      require_lsp_activation = true, -- require activation of an lsp before setting env variables

      -- picker options
      on_telescope_result_callback = nil, -- callback function for modifying telescope results
      picker_filter_type = 'substring', -- when you type something in pickers, filter by "substring" or "character"
      selected_venv_marker_color = '#00FF00', -- the color of the selected venv marker
      selected_venv_marker_icon = '✔', -- the icon to use for marking the selected venv
      picker_icons = {}, -- override default icons for venv types (e.g., { poetry = "📝", hatch = "🔨", default = "🐍" })
      picker_columns = { 'marker', 'search_icon', 'search_name', 'search_result' }, -- column order in pickers (omit columns to hide them)
      picker = 'auto', -- the picker to use. Valid options are "telescope", "fzf-lua", "snacks", "native", "mini-pick" or "auto"
      statusline_func = { nvchad = nil, lualine = nil }, -- if a function is defined here for a statusline, it can be used to customize the statusline.
    }, -- if you add plugin options, they go here.
  },
}
