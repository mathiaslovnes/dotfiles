return {
  'norcalli/nvim-colorizer.lua',
  config = function()
    require('colorizer').setup({
      '*', -- highlight all files by default
    }, {
      RGB = true, -- #RGB hex codes
      RRGGBB = true, -- #RRGGBB hex codes
      RRGGBBAA = true, -- #RRGGBBAA hex codes
      names = true, -- "Blue" etc.
      RRGGBB_ICC = true,
      rgb_fn = true, -- CSS rgb() and rgba()
      hsl_fn = true, -- CSS hsl() and hsla()
      css = true, -- Enable all CSS features
      css_fn = true, -- Enable all CSS *functions*
    })

    vim.api.nvim_create_autocmd({ 'BufEnter', 'BufRead' }, {
      pattern = '*',
      callback = function()
        require('colorizer').attach_to_buffer(0)
      end,
    })
  end,
}
