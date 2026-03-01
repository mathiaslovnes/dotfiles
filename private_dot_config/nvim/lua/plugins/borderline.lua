return {
  'mikesmithgh/borderline.nvim',
  lazy = true,
  event = 'VeryLazy',
  config = function()
    require('borderline').setup {
      border = 'rounded',
    }
  end,
}
