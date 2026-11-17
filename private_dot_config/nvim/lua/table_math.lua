-- Keeps render-markdown's tables aligned around math drawn by snacks.image. snacks hides a formula's LaTeX source and
-- draws an image a few cells wide in its place, but render-markdown pads each cell by its source width, so rows with
-- math came out short. cell_offset (render-markdown.lua) corrects each cell by the difference, and image_updated
-- (snacks.lua) lays a table out again when its images are drawn, which happens after render-markdown first lays it out.
local M = {}

local ns = vim.api.nvim_create_namespace 'snacks.image'

-- Width an image adds minus the source it hides, by LaTeX source. Kept for when snacks shows the source on the
-- cursor's line instead of the image, so the table doesn't change width as the cursor moves through it.
local deltas = {} ---@type table<string, integer>
-- The delta each image extmark had when its table was last laid out, per buffer
local laid_out = {} ---@type table<integer, table<integer, integer>>
-- The buffer each syntax tree belongs to: cell_offset only gets the cell's node
local owners = setmetatable({}, { __mode = 'k' }) ---@type table<TSTree, integer>
local pending = {} ---@type table<integer, true>

---@param buf integer
---@param mark vim.api.keyset.get_extmark_item
---@return integer? nil if the image hasn't been drawn yet
local function delta(buf, mark)
  local row, col, details = mark[2], mark[3], mark[4]
  local source = table.concat(vim.api.nvim_buf_get_text(buf, row, col, details.end_row or row, details.end_col or col, {}))
  if details.virt_text and details.virt_text_pos == 'inline' then
    local width = 0
    for _, chunk in ipairs(details.virt_text) do
      width = width + vim.api.nvim_strwidth(chunk[1])
    end
    deltas[source] = width - (details.conceal and vim.api.nvim_strwidth(source) or 0)
  end
  return deltas[source]
end

---@param node TSNode
---@return integer?
local function owner(node)
  local tree = node:tree()
  if not owners[tree] then
    for buf, highlighter in pairs(vim.treesitter.highlighter.active) do
      highlighter.tree:for_each_tree(function(t)
        if t == tree then
          owners[tree] = buf
        end
      end)
    end
  end
  return owners[tree]
end

---@param buf integer
local function rerender(buf)
  if pending[buf] then
    return
  end
  pending[buf] = true
  vim.schedule(function()
    pending[buf] = nil
    if vim.api.nvim_buf_is_valid(buf) then
      require('render-markdown').render { buf = buf }
    end
  end)
end

-- render-markdown's pipe_table.cell_offset: the width the cell's images add to it
---@param ctx { node: TSNode }
---@return integer
function M.cell_offset(ctx)
  local buf = owner(ctx.node)
  local row, start_col, _, end_col = ctx.node:range()
  if not buf or end_col <= start_col then
    return 0
  end
  laid_out[buf] = laid_out[buf] or {}
  local offset = 0
  for _, mark in ipairs(vim.api.nvim_buf_get_extmarks(buf, ns, { row, start_col }, { row, end_col - 1 }, { details = true })) do
    laid_out[buf][mark[1]] = delta(buf, mark) or 0
    offset = offset + laid_out[buf][mark[1]]
  end
  return offset
end

-- snacks.image's doc.on_update_pre: lays the image's table out again if the image changed its width there
---@param placement snacks.image.Placement
function M.image_updated(placement)
  local buf = placement.buf
  vim.schedule(function() -- after snacks has drawn it
    if not laid_out[buf] or not vim.api.nvim_buf_is_valid(buf) then
      return
    end
    for _, id in ipairs(placement.eids) do
      local mark = vim.api.nvim_buf_get_extmark_by_id(buf, ns, id, { details = true })
      local line = mark[1] and vim.api.nvim_buf_get_lines(buf, mark[1], mark[1] + 1, false)[1]
      local d = line and line:find '^%s*|' and delta(buf, { id, mark[1], mark[2], mark[3] })
      if d and laid_out[buf][id] ~= d then
        laid_out[buf][id] = d
        rerender(buf)
      end
    end
  end)
end

return M
