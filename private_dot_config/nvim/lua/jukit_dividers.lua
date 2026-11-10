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

-- Cell dividers and hidden °°° markdown-cell markers, drawn at redraw time on the visible lines only
-- (scanning the whole notebook on every keystroke took up to ~70 ms in big notebooks) and sized to the
-- window actually showing the buffer, so they follow splits and resizes.
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
      elseif line:match '^%s*r?"""°°°' or line:match '°°°"""%s*$' then
        vim.api.nvim_buf_set_extmark(buf, ns, row, 0, {
          virt_text = { { string.rep(' ', #line), 'Normal' } },
          virt_text_pos = 'overlay',
          priority = 15000,
          hl_mode = 'replace',
          ephemeral = true,
        })
      end
    end
    return false
  end,
})
