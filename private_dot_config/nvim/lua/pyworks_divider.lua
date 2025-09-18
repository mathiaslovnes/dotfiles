local M = {}

local ns = vim.api.nvim_create_namespace 'pyworks_divider'

-- Define custom highlight group
vim.api.nvim_set_hl(0, 'PyworksDivider', { fg = '#FFFFFF', bold = true })

local query_str = [[
  (comment) @divider
]]
local query = vim.treesitter.query.parse('python', query_str)

local function update_dividers(buf)
  vim.api.nvim_buf_clear_namespace(buf, ns, 0, -1)

  local win_width = vim.api.nvim_win_get_width(0) - 5
  local divider = string.rep('━', math.max(10, win_width))

  local ok, parser = pcall(vim.treesitter.get_parser, buf, 'python')
  if not ok then
    return
  end

  local tree = parser:parse()[1]

  for _, node, _ in query:iter_captures(tree:root(), buf, 0, -1) do
    local start_row = select(1, node:range())
    local text = vim.treesitter.get_node_text(node, buf)
    if text and text:match '^#|' then
      vim.api.nvim_buf_set_extmark(buf, ns, start_row, 0, {
        virt_text = { { divider, 'PyworksDivider' } },
        virt_text_pos = 'overlay',
        undo_restore = false,
      })
    end
  end
end

function M.setup()
  vim.api.nvim_create_autocmd({ 'FileType', 'WinResized' }, {
    pattern = { 'python', '*' },
    callback = function(args)
      local buf = args.buf
      if vim.bo[buf].filetype ~= 'python' then
        return
      end
      vim.api.nvim_buf_attach(buf, false, {
        on_lines = function()
          vim.schedule(function()
            update_dividers(buf)
          end)
        end,
      })
      update_dividers(buf)
    end,
  })
end

return M
