--[[

  Next, run AND READ `:help`.
    This will open up a help window with some basic information
    about reading, navigating and searching the builtin help documentation.

    This should be the first place you go to look when you're stuck or confused
    with something. It's one of my favorite Neovim features.

    MOST IMPORTANTLY, we provide a keymap "<space>sh" to [s]earch the [h]elp documentation,
    which is very useful when you're not exactly sure of what you're looking for.

  I have left several `:help X` comments throughout the init.lua
    These are hints about where to find more information about the relevant settings,
    plugins or Neovim features used in Kickstart.

   NOTE: Look for lines like this

    Throughout the file. These are for you, the reader, to help you understand what is happening.
    Feel free to delete them once you know what you're doing, but they should serve as a guide
    for when you are first encountering a few different constructs in your Neovim config.

If you experience any errors while trying to install kickstart, run `:checkhealth` for more info.

I hope you enjoy your Neovim journey,
- TJ

P.S. You can delete this when you're done too. It's your config now! :)
--]]

-- Set <space> as the leader key
-- See `:help mapleader`
--  NOTE: Must happen before plugins are loaded (otherwise wrong leader will be used)
vim.g.mapleader = ' '
vim.g.maplocalleader = ' '

-- Set to true if you have a Nerd Font installed and selected in the terminal
vim.g.have_nerd_font = true

-- [[ Setting options ]]
require 'options'

-- [[ Basic Keymaps ]]
require 'keymaps'

-- [[ Install `lazy.nvim` plugin manager ]]
require 'lazy-bootstrap'

-- [[ Configure and install plugins ]]
require 'lazy-plugins'

-- The line beneath this is called `modeline`. See `:help modeline`
-- vim: ts=2 sts=2 sw=2 et

local ns = vim.api.nvim_create_namespace 'pyworks_divider'

-- Define custom highlight group for light blue, bold divider
vim.api.nvim_set_hl(0, 'PyworksDivider', { fg = '#FFFFFF', bold = true })

-- Treesitter query for Python comments
local query_str = [[
  (comment) @divider
]]
local query = vim.treesitter.query.parse('python', query_str)

local function update_dividers(buf)
  -- Clear old extmarks
  vim.api.nvim_buf_clear_namespace(buf, ns, 0, -1)

  -- Get window width for dynamic divider length (minus padding)
  local win_width = vim.api.nvim_win_get_width(0) - 5
  local divider = string.rep('━', math.max(10, win_width)) -- Thicker line character

  -- Get the latest parse tree
  local ok, parser = pcall(vim.treesitter.get_parser, buf, 'python')
  if not ok then
    return
  end

  local tree = parser:parse()[1]

  -- Iterate over comment nodes
  for _, node, _ in query:iter_captures(tree:root(), buf, 0, -1) do
    local start_row, _, _, _ = node:range()
    local text = vim.treesitter.get_node_text(node, buf)
    if text and text:match '^#|' then
      vim.api.nvim_buf_set_extmark(buf, ns, start_row, 0, {
        virt_text = { { divider, 'PyworksDivider' } },
        virt_text_pos = 'overlay',
      })
    end
  end
end

-- Auto-attach on Python filetype and handle window resize
vim.api.nvim_create_autocmd({ 'FileType', 'WinResized' }, {
  pattern = { 'python', '*' },
  callback = function(args)
    local buf = args.buf
    if vim.bo[buf].filetype ~= 'python' then
      return
    end
    vim.api.nvim_buf_attach(buf, false, {
      on_lines = function()
        update_dividers(buf)
      end,
    })
    update_dividers(buf)
  end,
})
