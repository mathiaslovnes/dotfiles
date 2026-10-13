local ns_divider = vim.api.nvim_create_namespace 'pyworks_divider'
local ns_jukit = vim.api.nvim_create_namespace 'jukit_markers'

-- Define all jukit signs to prevent E155 errors
local jukit_signs = {
  'jukit_cell_markers',
  'jukit_textcells',
  'jukit_codecells',
  'jukit_output_markers',
}

for _, sign_name in ipairs(jukit_signs) do
  vim.fn.sign_define(sign_name, {
    text = '',
    texthl = 'Normal',
  })
end
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
  (string
    (string_start) @start
    (string_end) @end) @string
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
    -- Match both jukit dialects: `#|%%--%%|` (new cells) and `# |%%--%%|` (jupytext-converted)
    if text and text:match '^#%s*|' then
      vim.api.nvim_buf_set_extmark(buf, ns_divider, start_row, 0, {
        virt_text = { { divider, 'PyworksDivider' } },
        virt_text_pos = 'overlay',
        priority = 10000,
        hl_mode = 'combine',
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
  local lines = vim.api.nvim_buf_get_lines(buf, 0, -1, false)

  for id, node in query_jukit:iter_captures(tree:root(), buf, 0, -1) do
    local capture_name = query_jukit.captures[id]

    if capture_name == 'start' then
      local start_row = select(1, node:range())

      -- Check if line contains °°° marker
      if lines[start_row + 1] and lines[start_row + 1]:match '°°°' then
        -- Overlay the line with spaces to hide it
        local line_length = #lines[start_row + 1]
        local spaces = string.rep(' ', line_length)
        vim.api.nvim_buf_set_extmark(buf, ns_jukit, start_row, 0, {
          virt_text = { { spaces, 'Normal' } },
          virt_text_pos = 'overlay',
          hl_mode = 'replace',
          priority = 15000,
          undo_restore = false,
        })
      end
    elseif capture_name == 'end' then
      local start_row = select(1, node:range())

      -- Check if line contains °°° marker
      if lines[start_row + 1] and lines[start_row + 1]:match '°°°' then
        local line_length = #lines[start_row + 1]
        local spaces = string.rep(' ', line_length)
        vim.api.nvim_buf_set_extmark(buf, ns_jukit, start_row, 0, {
          virt_text = { { spaces, 'Normal' } },
          virt_text_pos = 'overlay',
          hl_mode = 'replace',
          priority = 15000,
          undo_restore = false,
        })
      end
    end
  end
end

-- jukit renders text-cell markdown via vim-syntax (`syn region textcell`), which
-- only shows when the treesitter highlighter is OFF. On the first file opened at
-- startup there's an ordering race: treesitter ends up active and hides the
-- cells until a manual `:e`, which reloads with treesitter off and jukit's syntax
-- intact. Reproduce that reload automatically, but only when we detect the broken
-- state (treesitter highlighter active on a jukit buffer). A buffer-local guard
-- and the state check both prevent it from looping. Dividers use the treesitter
-- *parser* (not the highlighter), so they are unaffected.
vim.api.nvim_create_autocmd('FileType', {
  pattern = { 'python' },
  callback = function(args)
    local buf = args.buf
    vim.schedule(function()
      if not vim.api.nvim_buf_is_valid(buf) then
        return
      end
      if vim.b[buf].jukit_reloaded or vim.bo[buf].modified then
        return
      end
      -- Only the broken state: treesitter highlighter active on a jukit buffer.
      if not require('vim.treesitter.highlighter').active[buf] then
        return
      end
      local is_jukit = false
      for _, line in ipairs(vim.api.nvim_buf_get_lines(buf, 0, -1, false)) do
        if line:find('|%%--%%|', 1, true) then
          is_jukit = true
          break
        end
      end
      if not is_jukit then
        return
      end
      vim.b[buf].jukit_reloaded = true
      vim.api.nvim_buf_call(buf, function()
        vim.cmd 'silent! edit'
      end)
    end)
  end,
})

vim.api.nvim_create_autocmd({ 'FileType', 'WinResized' }, {
  pattern = { 'python' },
  callback = function(args)
    local buf = args.buf

    -- Enable concealing in the buffer
    vim.wo.conceallevel = 2
    vim.wo.concealcursor = ''

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

-- Trigger on text changes to handle newly typed markers
vim.api.nvim_create_autocmd({ 'TextChanged', 'TextChangedI' }, {
  pattern = '*.py',
  callback = function(args)
    local buf = args.buf
    if vim.bo[buf].filetype == 'python' then
      vim.schedule(function()
        update_dividers(buf)
        hide_jukit_markers(buf)
      end)
    end
  end,
})

-- Trigger for already-open Python buffers
for _, buf in ipairs(vim.api.nvim_list_bufs()) do
  if vim.api.nvim_buf_is_loaded(buf) and vim.bo[buf].filetype == 'python' then
    vim.schedule(function()
      update_dividers(buf)
      hide_jukit_markers(buf)
    end)
  end
end
