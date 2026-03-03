local ns_divider = vim.api.nvim_create_namespace 'pyworks_divider'
local ns_jukit = vim.api.nvim_create_namespace 'jukit_markers'

-- Divider highlight group
vim.api.nvim_set_hl(0, 'PyworksDivider', { fg = '#FFFFFF', bold = true })

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
    if text and text:match '^#|' then
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
