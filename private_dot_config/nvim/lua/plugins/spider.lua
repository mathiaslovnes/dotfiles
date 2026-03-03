return {
  'chrisgrieser/nvim-spider',
  lazy = false,
  -- default values
  keys = {
    { 'w', "<cmd>lua require('spider').motion('w')<CR>", mode = { 'n', 'o', 'x' } },
    { 'e', "<cmd>lua require('spider').motion('e')<CR>", mode = { 'n', 'o', 'x' } },
    { 'b', "<cmd>lua require('spider').motion('b')<CR>", mode = { 'n', 'o', 'x' } },
    { 'ge', "<cmd>lua require('spider').motion('ge')<CR>", mode = { 'n', 'o', 'x' } },
  },
  config = function()
    require('spider').setup {
      skipInsignificantPunctuation = true,
      subwordMovement = true,
      consistentOperatorPending = false, -- see the README for details
      customPatterns = {}, -- see the README for details
    }
  end,
}

-- TEST:
-- -- positions vim's `w` will move to
-- if foo:find("%d") and foo == bar then print("[foo] has" .. bar) end
-- -- ^  ^^   ^  ^^  ^   ^   ^  ^   ^    ^    ^  ^  ^ ^  ^ ^  ^  ^ ^  -> 21
-- -- positions spider's `w` will move to
-- if foo:find("%d") and foo == bar then print("[foo] has" .. bar) end
-- -- ^   ^      ^   ^   ^   ^  ^   ^    ^       ^    ^    ^  ^    ^  -> 14
--
--
-- Subword text object
-- This plugin supports w, e, and b in operator-pending mode, but does not include a subword variant of iw.
-- For a version of iw that considers camelCase, check out the subword text object of nvim-various-textobjs.
-- https://github.com/chrisgrieser/nvim-various-textobjs
