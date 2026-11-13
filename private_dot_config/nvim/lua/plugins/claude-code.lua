return {
  "coder/claudecode.nvim",
  dependencies = { "folke/snacks.nvim" },
  -- start the IDE server with Neovim, so a `claude` in another tmux pane can connect (/ide) before any <leader>a key
  event = "VeryLazy",
  opts = {
    terminal = {
      -- Esc Esc reaches Claude (clear input, rewind) instead of leaving terminal mode; leave with <C-\><C-n>
      snacks_win_opts = { keys = { term_normal = false } },
    },
  },
  -- /ide lists every Neovim as "Neovim" plus its folder, so two Neovims in one folder look the same. Add the
  -- tmux window to the name; the plugin hard-codes it, so rewrite it in each lock file it writes.
  config = function(_, opts)
    local window = vim.env.TMUX_PANE
      and vim.trim(vim.fn.system { 'tmux', 'display-message', '-p', '-t', vim.env.TMUX_PANE, '#{session_name}:#{window_index} #{window_name}' })
    if window and window ~= '' and vim.v.shell_error == 0 then
      local lockfile = require 'claudecode.lockfile'
      local create = lockfile.create
      lockfile.create = function(...)
        local ok, path, token = create(...)
        if ok then
          -- edit the text rather than re-encode it (an empty workspaceFolders [] would come back as {}),
          -- and never let a failure here stop the server
          pcall(function()
            local name = '"ideName":' .. vim.json.encode(('Neovim (tmux %s)'):format(window))
            local text = table.concat(vim.fn.readfile(path), '\n'):gsub('"ideName":"Neovim"', function()
              return name
            end)
            vim.fn.writefile({ text }, path)
          end)
        end
        return ok, path, token
      end
    end
    require('claudecode').setup(opts)

    -- Sends (<leader>as, <leader>ab) reach the connected Claude, but the plugin then opens a Claude split in Neovim
    -- even when that Claude runs in a tmux pane (/ide). Without a Claude split, send only to a connected Claude.
    local claudecode, terminal = require 'claudecode', require 'claudecode.terminal'
    local send = claudecode.send_at_mention
    claudecode.send_at_mention = function(...)
      if terminal.get_active_terminal_bufnr() then
        return send(...)
      end
      if not claudecode.is_claude_connected() then
        return false, 'no Claude connected: run /ide in your Claude pane, or start one here with <Space>ac'
      end
      local ensure_visible, open = terminal.ensure_visible, terminal.open
      terminal.ensure_visible, terminal.open = function() end, function() end
      local ok, success, err = pcall(send, ...)
      terminal.ensure_visible, terminal.open = ensure_visible, open
      if not ok then
        error(success)
      end
      return success, err
    end
  end,
  -- `cmd` lets lazy.nvim create command stubs that load the plugin on first use,
  -- so `:ClaudeCode` and friends work on a fresh start. Without it, a keys-only
  -- spec defers loading until a <leader>a* mapping is pressed and the commands
  -- would not exist yet.
  cmd = {
    "ClaudeCode",
    "ClaudeCodeFocus",
    "ClaudeCodeSelectModel",
    "ClaudeCodeAdd",
    "ClaudeCodeSend",
    "ClaudeCodeTreeAdd",
    "ClaudeCodeStatus",
    "ClaudeCodeStart",
    "ClaudeCodeStop",
    "ClaudeCodeOpen",
    "ClaudeCodeClose",
    "ClaudeCodeDiffAccept",
    "ClaudeCodeDiffDeny",
    "ClaudeCodeCloseAllDiffs",
  },
  keys = {
    { "<leader>ac", "<cmd>ClaudeCode<cr>",            desc = "Toggle Claude" },
    { "<leader>af", "<cmd>ClaudeCodeFocus<cr>",       desc = "Focus Claude" },
    { "<leader>ar", "<cmd>ClaudeCode --resume<cr>",   desc = "Resume Claude" },
    { "<leader>aC", "<cmd>ClaudeCode --continue<cr>", desc = "Continue Claude" },
    { "<leader>am", "<cmd>ClaudeCodeSelectModel<cr>", desc = "Select Claude model" },
    { "<leader>ab", "<cmd>ClaudeCodeAdd %<cr>",       desc = "Add current buffer" },
    { "<leader>as", "<cmd>ClaudeCodeSend<cr>",        mode = "v",                  desc = "Send to Claude" },
    {
      "<leader>as",
      "<cmd>ClaudeCodeTreeAdd<cr>",
      desc = "Add file",
      ft = { "NvimTree", "neo-tree", "oil", "minifiles", "netrw", "snacks_picker_list" },
    },
    -- Diff management
    { "<leader>aa", "<cmd>ClaudeCodeDiffAccept<cr>", desc = "Accept diff" },
    { "<leader>ad", "<cmd>ClaudeCodeDiffDeny<cr>",   desc = "Deny diff" },
  },
}
