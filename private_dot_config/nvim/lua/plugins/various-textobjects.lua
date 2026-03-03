return {
  'chrisgrieser/nvim-various-textobjs',
  config = function()
    require('various-textobjs').setup {
      useDefaultKeymaps = false,
      forwardLooking = {
        -- Number of lines to seek forwards for a text object. See the overview
        -- table in the README for which text object uses which value.
        small = 5,
        big = 30,
      },
    }

    -- stylua: ignore start
    vim.keymap.set({ 'o', 'x' }, 'U', function() require('various-textobjs').url() end, { desc = 'URL textobj' })
    vim.keymap.set({ 'o', 'x' }, 'as', function()require('various-textobjs').subword 'outer'end, { desc = 'Outer subword' })
    vim.keymap.set({ 'o', 'x' }, 'is', function()require('various-textobjs').subword 'inner'end, { desc = 'Inner subword' })
    -- stylua: ignore end
  end,
}
