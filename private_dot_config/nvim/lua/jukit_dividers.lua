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

-- Cell dividers, drawn at redraw time on the visible lines only (scanning the whole notebook on every
-- keystroke took up to ~70 ms in big notebooks) and sized to the window actually showing the buffer, so
-- they follow splits and resizes.
local ns = vim.api.nvim_create_namespace 'pyworks_deco'
vim.api.nvim_set_decoration_provider(ns, {
  on_win = function(_, win, buf, top, bot)
    if vim.bo[buf].filetype ~= 'python' then
      return false
    end
    local divider = string.rep('━', math.max(10, vim.api.nvim_win_get_width(win) - 5))
    for i, line in ipairs(vim.api.nvim_buf_get_lines(buf, top, bot + 1, false)) do
      local row = top + i - 1
      -- Both jukit dialects: `#|%%--%%|` (new cells) and `# |%%--%%|` (jupytext-converted)
      if line:match '^#%s*|%%%%%-%-%%%%|' then
        vim.api.nvim_buf_set_extmark(buf, ns, row, 0, {
          virt_text = { { divider, 'PyworksDivider' } },
          virt_text_pos = 'overlay',
          priority = 10000,
          hl_mode = 'combine',
          ephemeral = true,
        })
      end
    end
    return false
  end,
})

-- The r"""°°° and °°°""" lines of markdown cells aren't drawn (with conceallevel > 0), so a cell's text sits
-- right against its dividers, and the cursor steps over them, so they can't be deleted by accident. Only
-- when they're on lines of their own and the cell has at least one line of text.
local md_ns = vim.api.nvim_create_namespace 'jukit_md_marks'

local function is_md_open(line)
  return line ~= nil and line:match '^r?"""°°°%s*$' ~= nil
end

local function is_md_close(line)
  return line ~= nil and line:match '^°°°"""%s*$' ~= nil
end

-- Whether line i of lines (1-based) is one of the hidden lines
local function hidden_md_mark(lines, i)
  return is_md_open(lines[i]) and not is_md_close(lines[i + 1]) or is_md_close(lines[i]) and not is_md_open(lines[i - 1])
end

-- Marks are placed from the text on every change (a scan of a 1700-line notebook takes under 0.1 ms)
local function hide_md_marks(buf)
  vim.api.nvim_buf_clear_namespace(buf, md_ns, 0, -1)
  local lines = vim.api.nvim_buf_get_lines(buf, 0, -1, false)
  for i in ipairs(lines) do
    if hidden_md_mark(lines, i) then
      vim.api.nvim_buf_set_extmark(buf, md_ns, i - 1, 0, { conceal_lines = '' })
    end
  end
end

vim.api.nvim_create_autocmd({ 'FileType', 'TextChanged', 'TextChangedI' }, {
  callback = function(a)
    if vim.bo[a.buf].filetype == 'python' then
      hide_md_marks(a.buf)
    end
  end,
})

-- Steps in the direction the cursor was moving; when it didn't move (the line under it was deleted), into
-- the cell's text
vim.api.nvim_create_autocmd('CursorMoved', {
  callback = function(a)
    if vim.bo[a.buf].filetype ~= 'python' or vim.wo.conceallevel == 0 then
      return
    end
    local row = vim.fn.line '.'
    local last = vim.w.jukit_last_pos or {}
    local prev = last[1] == a.buf and last[2] or row
    vim.w.jukit_last_pos = { a.buf, row }
    -- The lines around the cursor are enough: a divider or a line of text always sits between two hidden lines
    local first = math.max(1, row - 3)
    local lines = vim.api.nvim_buf_get_lines(a.buf, first - 1, row + 3, false)
    local function hidden(r)
      return hidden_md_mark(lines, r - first + 1)
    end
    if not hidden(row) then
      return
    end
    local step = row > prev and 1 or row < prev and -1 or is_md_close(lines[row - first + 1]) and -1 or 1
    for _, dir in ipairs { step, -step } do
      local target = row + dir
      while hidden(target) do
        target = target + dir
      end
      if target >= 1 and target <= vim.fn.line '$' then
        vim.cmd('normal! ' .. math.abs(target - row) .. (dir > 0 and 'j' or 'k'))
        vim.w.jukit_last_pos = { a.buf, target }
        return
      end
    end
  end,
})
