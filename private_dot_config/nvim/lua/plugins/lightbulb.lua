return {
  'kosayoda/nvim-lightbulb',
  config = function()
    require('nvim-lightbulb').setup {
      autocmd = { enabled = true, updatetime = -1 },

      -- Filter out 'Change to parameter' diagnostics suggesions
      filter = function(client_name, action)
        return not (action.title and action.title:lower():find 'change to parameter')
      end,
    }
  end,
}
