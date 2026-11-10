-- Replaces vim-jukit's tmux layout. The plugin moves nvim with `move-pane -f`, which sends nvim to
-- the far left of the tmux window and pushes any other pane (e.g. claude) into the middle.
-- This version leaves nvim where it is, puts the jukit panes at the far right (arranged as in
-- g:jukit_layout) and then gives every column in the window the same width.
-- Called from autoload/jukit/tmux/layouts.vim.
local M = {}

local function tmux(...)
  return vim.trim(vim.fn.system { 'tmux', ... })
end

-- Pane id if the pane is still open, nil otherwise
local function live_pane(id)
  if not id or id == '' then
    return nil
  end
  tmux('display', '-p', '-t', id, '#{pane_id}')
  return vim.v.shell_error == 0 and id or nil
end

-- left, top, right, bottom cell of a pane
local function edges(id)
  local l, t, r, b = tmux('display', '-p', '-t', id, '#{pane_left} #{pane_top} #{pane_right} #{pane_bottom}')
    :match '(%d+) (%d+) (%d+) (%d+)'
  return tonumber(l), tonumber(t), tonumber(r), tonumber(b)
end

function M.set_layout(layout)
  local nvim = vim.env.TMUX_PANE
  local ids = {
    file_content = nvim,
    output = live_pane(vim.g.jukit_output_title),
    output_history = live_pane(vim.g.jukit_outhist_title),
  }

  local file_first = type(layout.val[1]) == 'string'
  local inner = file_first and layout.val[2] or layout.val[1]
  local panes = {}
  for _, name in ipairs(inner.val) do
    if ids[name] then
      table.insert(panes, ids[name])
    end
  end
  if #panes == 0 then
    return
  end

  local flags = { horizontal = { '-h', 'x' }, vertical = { '-v', 'y' } }
  local outer_flag = flags[layout.split][1]
  local inner_flag, inner_dim = unpack(flags[inner.split])

  -- -f joins the pane to the window's top-level split, at the far right (far left with -b).
  -- Taking the jukit panes out of nvim's column lets tmux collapse that column, so nvim, the jukit
  -- panes and any other columns end up side by side at the same level.
  local move = { 'move-pane', '-d', '-f', outer_flag, '-s', panes[1], '-t', nvim }
  if not file_first then
    table.insert(move, '-b')
  end
  tmux(unpack(move))
  if panes[2] then
    tmux('move-pane', '-d', inner_flag, '-s', panes[2], '-t', panes[1])
  end

  -- -E spreads nvim and its neighbours evenly, e.g. three columns get a third each
  tmux('select-layout', '-E', '-t', nvim)

  -- Split the jukit column between output and history using the inner p1
  if panes[2] then
    local l1, t1 = edges(panes[1])
    local _, _, r2, b2 = edges(panes[2])
    local span = inner_dim == 'x' and r2 - l1 + 1 or b2 - t1 + 1
    tmux('resize-pane', '-t', panes[1], '-' .. inner_dim, tostring(math.floor(span * inner.p1)))
  end
  tmux('select-pane', '-t', nvim)
end

return M
