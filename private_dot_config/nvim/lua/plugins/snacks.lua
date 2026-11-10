vim.g.snacks_animate = false
return {
  'folke/snacks.nvim',
  priority = 1000,
  lazy = false,
  ---@type snacks.Config
  opts = {
    bigfile = { enabled = true },
    dashboard = { enabled = true },
    explorer = { enabled = false },
    image = { enabled = true },
    indent = { enabled = true },
    input = { enabled = false },
    notifier = {
      enabled = true,
      timeout = 4444,
    },
    picker = {
      enabled = true,
      actions = {
        -- open the file in place of the current buffer: the old buffer closes and the new one
        -- takes its spot in the bufferline
        replace_buffer = function(picker)
          local original = vim.api.nvim_win_get_buf(picker.main)
          local listed = vim.tbl_filter(function(b)
            return vim.bo[b].buflisted
          end, vim.api.nvim_list_bufs())
          local pos = vim.fn.index(listed, original) + 1
          picker:action 'confirm'
          vim.schedule(function()
            if vim.api.nvim_get_current_buf() ~= original and vim.api.nvim_buf_is_valid(original) then
              pcall(vim.api.nvim_buf_delete, original, { force = false })
              if pos > 0 then
                pcall(require('bufferline').move_to, pos)
              end
            end
          end)
        end,
      },
      win = {
        input = {
          keys = {
            ['<Esc>'] = { 'close', mode = { 'n', 'i' } }, -- one Esc closes, as telescope did
            ['<C-y>'] = { 'replace_buffer', mode = { 'n', 'i' } },
            ['<C-x>'] = { 'edit_split', mode = { 'n', 'i' } }, -- telescope's split key (Snacks' own is <C-s>)
            ['<M-BS>'] = { '<c-s-w>', mode = { 'i' }, expr = true, desc = 'delete word' },
          },
        },
      },
    },
    quickfile = { enabled = true },
    scope = { enabled = true, keys = { textobject = { ii = false, ai = false } } }, -- ai/ii select a conditional (treesitter-textobjects)
    scroll = { enabled = false },
    statuscolumn = { enabled = true },
    words = { enabled = false }, -- vim-illuminate highlights the word under the cursor
    styles = {
      notification = {
        wo = { wrap = true }, -- Wrap notifications
      },
    },
  },
  keys = {
    -- stylua: ignore start
    -- Top Pickers & Explorer
    ---@diagnostic disable: undefined-global
    -- { "<leader><space>", function() Snacks.picker.smart() end, desc = "Smart Find Files" },
    -- { "<leader>,", function() Snacks.picker.buffers() end, desc = "Buffers" },
    -- { "<leader>/", function() Snacks.picker.grep() end, desc = "Grep" },
    { "<leader>:", function() Snacks.picker.command_history() end, desc = "Command History" },
    { "<leader>nh",  function() Snacks.notifier.show_history() end, desc = "Notification History" },
    -- { "<leader>fe", function() Snacks.explorer() end, desc = "File Explorer" },
    -- find
    -- { "<leader>fb", function() Snacks.picker.buffers() end, desc = "Buffers" },
    -- { "<leader>fc", function() Snacks.picker.files({ cwd = vim.fn.stdpath("config") }) end, desc = "Find Config File" },
    -- { "<leader>fg", function() Snacks.picker.git_files() end, desc = "Find Git Files" },
    -- { "<leader>fr", function() Snacks.picker.recent() end, desc = "Recent" },
    -- Telescope replacement
    { "<leader>sp", function() Snacks.picker.projects() end, desc = "Search Projects" },
    -- git
    { "<leader>lg", function() Snacks.lazygit() end, desc = "Lazygit" },
    { "<leader>gb", function() Snacks.picker.git_branches() end, desc = "Git Branches" },
    { "<leader>gl", function() Snacks.picker.git_log() end, desc = "Git Log" },
    { "<leader>gL", function() Snacks.picker.git_log_line() end, desc = "Git Log Line" },
    { "<leader>gs", function() Snacks.picker.git_status() end, desc = "Git Status" },
    -- { "<leader>gS", function() Snacks.picker.git_stash() end, desc = "Git Stash" },
    { "<leader>gh", function() Snacks.picker.git_diff() end, desc = "Git Diff (Hunks)" }, -- <leader>gd is gitsigns' diff view
    { "<leader>gB", function() Snacks.gitbrowse() end, desc = "Git Browse", mode = { "n", "v" } },

    -- { "<leader>glf", function() Snacks.picker.git_log_file() end, desc = "Git Log File" },
    -- gh
    { "<leader>gi", function() Snacks.picker.gh_issue() end, desc = "GitHub Issues (open)" },
    { "<leader>gI", function() Snacks.picker.gh_issue({ state = "all" }) end, desc = "GitHub Issues (all)" },
    { "<leader>gp", function() Snacks.picker.gh_pr() end, desc = "GitHub Pull Requests (open)" },
    { "<leader>gP", function() Snacks.picker.gh_pr({ state = "all" }) end, desc = "GitHub Pull Requests (all)" },

    -- Search (these were telescope's)
    { "<leader>sf", function() Snacks.picker.files() end, desc = "[S]earch [F]iles" },
    { "<leader>sg", function() Snacks.picker.grep() end, desc = "[S]earch by [G]rep" },
    { "<leader>sw", function() Snacks.picker.grep_word() end, desc = "[S]earch current [W]ord", mode = { "n", "x" } },
    { "<leader>sh", function() Snacks.picker.help() end, desc = "[S]earch [H]elp" },
    { "<leader>sk", function() Snacks.picker.keymaps() end, desc = "[S]earch [K]eymaps" },
    { "<leader>sd", function() Snacks.picker.diagnostics() end, desc = "[S]earch [D]iagnostics" },
    { "<leader>ss", function() Snacks.picker.lsp_symbols() end, desc = "[S]earch Document [S]ymbols" },
    { "<leader>sr", function() Snacks.picker.recent() end, desc = "[S]earch [R]ecent Files" },
    { "<leader>sb", function() Snacks.picker.buffers() end, desc = "[S]earch Existing [B]uffers" },
    { "<leader>sn", function() Snacks.picker.files({ cwd = vim.fn.stdpath("config") }) end, desc = "[S]earch [N]eovim files" },
    { "<leader>f", function() Snacks.picker.lines() end, desc = "[F]uzzily search in current buffer" },

    -- search
    -- { '<leader>s"', function() Snacks.picker.registers() end, desc = "Search Registers" },
    -- { '<leader>s/', function() Snacks.picker.search_history() end, desc = "Search History" },
    { "<leader>sa", function() Snacks.picker.autocmds() end, desc = "Autocmds" },
    { "<leader>sc", function() Snacks.picker.command_history() end, desc = "Search Command History" },
    -- { "<leader>sC", function() Snacks.picker.commands() end, desc = "Search All Commands" },
    { "<leader>sD", function() Snacks.picker.diagnostics_buffer() end, desc = "Buffer Diagnostics" },
    { "<leader>sH", function() Snacks.picker.highlights() end, desc = "Highlights" },
    { "<leader>si", function() Snacks.picker.icons() end, desc = "Icons" },
    { "<leader>sj", function() Snacks.picker.jumps() end, desc = "Jumps" },
    { "<leader>sl", function() Snacks.picker.loclist() end, desc = "Location List" },
    { "<leader>sm", function() Snacks.picker.marks() end, desc = "Marks" },
    -- { "<leader>sM", function() Snacks.picker.man() end, desc = "Man Pages" },
    { "<leader>sP", function() Snacks.picker.lazy() end, desc = "Search for Plugin Spec" },
    { "<leader>sq", function() Snacks.picker.qflist() end, desc = "Quickfix List" },
    { "<leader>sR", function() Snacks.picker.resume() end, desc = "Resume" },
    -- { "<leader>su", function() Snacks.picker.undo() end, desc = "Undo History" },
    { "<leader>sC", function() Snacks.picker.colorschemes() end, desc = "Search Colorschemes" },

    -- LSP
    { "gd", function() Snacks.picker.lsp_definitions() end, desc = "Goto Definition" },
    { "gD", function() Snacks.picker.lsp_declarations() end, desc = "Goto Declaration" },
    { "gI", function() Snacks.picker.lsp_implementations() end, desc = "Goto Implementation" },
    { "gy", function() Snacks.picker.lsp_type_definitions() end, desc = "Goto T[y]pe Definition" },
    -- { "gai", function() Snacks.picker.lsp_incoming_calls() end, desc = "C[a]lls Incoming" },
    -- { "gao", function() Snacks.picker.lsp_outgoing_calls() end, desc = "C[a]lls Outgoing" },
    -- { "<leader>sS", function() Snacks.picker.lsp_workspace_symbols() end, desc = "LSP Workspace Symbols" },

    -- Other
    { "<leader>Z",  function() Snacks.zen.zoom() end, desc = "Toggle Zoom" },
    -- { "<leader>.",  function() Snacks.scratch() end, desc = "Toggle Scratch Buffer" },
    -- { "<leader>S",  function() Snacks.scratch.select() end, desc = "Select Scratch Buffer" },
    { "<leader>bd", function() Snacks.bufdelete() end, desc = "Delete Buffer" },
    { "<leader>rf", function() Snacks.rename.rename_file() end, desc = "Rename File" },
    { "<leader>nd", function() Snacks.notifier.hide() end, desc = "Dismiss All Notifications" },
    -- { "<c-/>",      function() Snacks.terminal() end, desc = "Toggle Terminal" },
    -- { "<c-_>",      function() Snacks.terminal() end, desc = "which_key_ignore" },
    -- { "]]",         function() Snacks.words.jump(vim.v.count1) end, desc = "Next Reference", mode = { "n", "t" } },
    -- { "[[",         function() Snacks.words.jump(-vim.v.count1) end, desc = "Prev Reference", mode = { "n", "t" } },
    {
    -- stylua: ignore start
      "<leader>N",
      desc = "Neovim News",
      function()
        Snacks.win({
          file = vim.api.nvim_get_runtime_file("doc/news.txt", false)[1],
          width = 0.6,
          height = 0.6,
          wo = {
            spell = false,
            wrap = false,
            signcolumn = "yes",
            statuscolumn = " ",
            conceallevel = 3,
          },
        })
      end,
    }
,
  },
  init = function()
    vim.api.nvim_create_autocmd('User', {
      pattern = 'VeryLazy',
      callback = function()
        -- Setup some globals for debugging (lazy-loaded)
        _G.dd = function(...)
          Snacks.debug.inspect(...)
        end
        _G.bt = function()
          Snacks.debug.backtrace()
        end

        -- Override print to use snacks for `:=` command
        if vim.fn.has 'nvim-0.11' == 1 then
          vim._print = function(_, ...)
            dd(...)
          end
        else
          vim.print = _G.dd
        end

        -- Create some toggle mappings
        Snacks.toggle.option('spell', { name = 'Toggle Spelling' }):map '<leader>us'
        Snacks.toggle.option('wrap', { name = 'Toggle Wrap' }):map '<leader>uw'
        Snacks.toggle.diagnostics({ name = 'Toggle Diagnostics' }):map '<leader>ud'
        Snacks.toggle.option('conceallevel', { name = 'Toggle Conceallevel', off = 0, on = vim.o.conceallevel > 0 and vim.o.conceallevel or 2 }):map '<leader>uc'
        Snacks.toggle.inlay_hints({ name = 'Toggle Inlay Hints' }):map '<leader>uh'
        Snacks.toggle.indent({ name = 'Toggle Indent Guides' }):map '<leader>ui'
      end,
    })
  end,
}
