-- Open a todo.md in a float; checkmate's keys (<leader>Tt toggle, <leader>Tn new, ...) work inside it
local function open_todo(path)
  -- load the buffer here: Snacks.win's `file` option opens it read-only
  local buf = vim.fn.bufadd(path)
  vim.fn.bufload(buf)
  Snacks.win {
    buf = buf,
    width = 0.6,
    height = 0.6,
    border = 'rounded',
    title = ' ' .. vim.fn.fnamemodify(path, ':~') .. ' ',
    -- save on close, like dooing did
    on_close = function(win)
      if vim.api.nvim_buf_is_valid(win.buf) and vim.bo[win.buf].modified then
        vim.api.nvim_buf_call(win.buf, function()
          vim.cmd 'silent write'
        end)
      end
    end,
  }
end

return {
  'bngarren/checkmate.nvim',
  ft = 'markdown', -- activates on files named todo.md / TODO.md / *.todo.md
  opts = {},
  keys = {
    {
      '<leader>td',
      function()
        open_todo((vim.fs.root(0, '.git') or vim.fn.getcwd()) .. '/todo.md')
      end,
      desc = 'Project todos',
    },
    {
      '<leader>tD',
      function()
        open_todo(vim.fn.stdpath 'data' .. '/todo.md')
      end,
      desc = 'Global todos',
    },
  },
}
