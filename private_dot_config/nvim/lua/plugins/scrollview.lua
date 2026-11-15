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
      -- {'all'} enables all sign groups; this is all of them except spell, which checked the line on every
      -- keystroke in insert mode, even with 'spell' off
      signs_on_startup = {
        'changelist',
        'conflicts',
        'cursor',
        'diagnostics',
        'folds',
        'indent',
        'keywords',
        'latestchange',
        'loclist',
        'marks',
        'quickfix',
        'search',
        'textwidth',
        'trail',
      },

      -- Diagnostic severities to show (leave empty for all)
      -- Example: {vim.diagnostic.severity.ERROR} for errors only
      diagnostics_severities = {},
    }
  end,
}
