local M = {}

local ns_divider = vim.api.nvim_create_namespace 'pyworks_divider'
local ns_jukit = vim.api.nvim_create_namespace 'jukit_markers'

-- Divider highlight group
vim.api.nvim_set_hl(0, 'PyworksDivider', { fg = '#FFFFFF', bold = true })
-- Jukit marker highlight group (invisible)
vim.api.nvim_set_hl(0, 'JukitMarker', { fg = 'NONE', bg = 'NONE' })

-- Queries
local query_divider = vim.treesitter.query.parse(
  'python',
  [[
  (comment) @divider
]]
)
local query_jukit = vim.treesitter.query.parse(
  'python',
  [[
  (string) @jukit_marker
]]
)

local function update_dividers(buf)
  vim.api.nvim_buf_clear_namespace(buf, ns_divider, 0, -1)
  local win_width = vim.api.nvim_win_get_width(0) - 5
  local divider = string.rep('━', math.max(10, win_width))

  local ok, parser = pcall(vim.treesitter.get_parser, buf, 'python')
  if not ok then
    return
  end
  local tree = parser:parse()[1]

  for _, node in query_divider:iter_captures(tree:root(), buf, 0, -1) do
    local start_row = select(1, node:range())
    local text = vim.treesitter.get_node_text(node, buf)
    if text and text:match '^#|' then
      vim.api.nvim_buf_set_extmark(buf, ns_divider, start_row, 0, {
        virt_text = { { divider, 'PyworksDivider' } },
        virt_text_pos = 'overlay',
        undo_restore = false,
      })
    end
  end
end

local function hide_jukit_markers(buf)
  vim.api.nvim_buf_clear_namespace(buf, ns_jukit, 0, -1)

  local ok, parser = pcall(vim.treesitter.get_parser, buf, 'python')
  if not ok then
    return
  end
  local tree = parser:parse()[1]

  for _, node in query_jukit:iter_captures(tree:root(), buf, 0, -1) do
    local text = vim.treesitter.get_node_text(node, buf)
    if text and text:match '^r?""".*°°°' or text:match '°°°"""$' then
      local start_row, start_col, end_row, end_col = node:range()
      vim.api.nvim_buf_set_extmark(buf, ns_jukit, start_row, start_col, {
        end_row = end_row,
        end_col = end_col,
        virt_text = {}, -- replace with nothing
        virt_text_pos = 'overlay',
        hl_group = 'JukitMarker',
        undo_restore = false,
      })
    end
  end
end

function M.setup()
  vim.api.nvim_create_autocmd({ 'FileType', 'WinResized' }, {
    pattern = { 'python' },
    callback = function(args)
      local buf = args.buf
      vim.api.nvim_buf_attach(buf, false, {
        on_lines = function()
          vim.schedule(function()
            update_dividers(buf)
            hide_jukit_markers(buf)
          end)
        end,
      })
      update_dividers(buf)
      hide_jukit_markers(buf)
    end,
  })
end

return M
