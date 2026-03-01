return {
  'dstein64/nvim-scrollview',
  config = function()
    require('scrollview').setup {
      -- Excluded filetypes (list)
      excluded_filetypes = { 'nerdtree' },

      -- Only show scrollbar in the current window
      current_only = true,

      -- Base position for scrollbar ('buffer', 'window')
      base = 'window',

      -- Column position for the scrollbar (when base = 'buffer')
      column = nil,

      -- Which sign groups are enabled on startup
      -- Default is {'diagnostics', 'search'} (and 'marks' for nvim>=0.10)
      -- Set to {'all'} to enable all sign groups
      signs_on_startup = { 'all' },

      -- Diagnostic severities to show (leave empty for all)
      -- Example: {vim.diagnostic.severity.ERROR} for errors only
      diagnostics_severities = {},
    }
  end,
}
