return {

  'tummetott/unimpaired.nvim',
  event = 'VeryLazy',
  opts = {
    default_keymaps = false,
    keymaps = {

      blank_above = {
        mapping = '<leader>ø',
        dot_repeat = true,
      },
      blank_below = {
        mapping = '<leader>Ø',
        dot_repeat = true,
      },
    },
  },
}
