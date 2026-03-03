-- debug.lua
--
-- DAP (Debug Adapter Protocol) configuration

return {
  -- NOTE: Yes, you can install new plugins here!
  'mfussenegger/nvim-dap',
  -- NOTE: And you can specify dependencies as well
  dependencies = {
    -- Creates a beautiful debugger UI
    'rcarriga/nvim-dap-ui',

    -- Required dependency for nvim-dap-ui
    'nvim-neotest/nvim-nio',

    -- Installs the debug adapters for you
    'mason-org/mason.nvim',
    'jay-babu/mason-nvim-dap.nvim',

    -- Language-specific DAP plugins
    'mfussenegger/nvim-dap-python',
    'leoluz/nvim-dap-go',

    -- Inline variable values while debugging
    'theHamsta/nvim-dap-virtual-text',
  },
  -- stylua: ignore start
  keys = {
    -- Session control
    { '<leader>dc',  function() require('dap').continue() end,          desc = 'Debug: Start/Continue' },
    { '<leader>dR',  function() require('dap').restart() end,           desc = 'Debug: Restart' },
    { '<leader>dt',  function() require('dap').terminate() end,         desc = 'Debug: Terminate' },
    { '<leader>dl',  function() require('dap').run_last() end,          desc = 'Debug: Run Last' },

    -- Stepping
    { '<leader>di',  function() require('dap').step_into() end,         desc = 'Debug: Step Into' },
    { '<leader>do',  function() require('dap').step_over() end,         desc = 'Debug: Step Over' },
    { '<leader>dO',  function() require('dap').step_out() end,          desc = 'Debug: Step Out' },

    -- Breakpoints
    { '<leader>bp',  function() require('dap').toggle_breakpoint() end, desc = 'Debug: Toggle Breakpoint' },
    { '<leader>Bp',  function() require('dap').set_breakpoint(vim.fn.input 'Breakpoint condition: ') end, desc = 'Debug: Conditional Breakpoint' },
    { '<leader>bc',  function() require('dap').clear_breakpoints() end, desc = 'Debug: Clear All Breakpoints' },
    { '<leader>bl',  function() require('dap').list_breakpoints() end, desc = 'Debug: List All Breakpoints' },
    { '<leader>lp',  function() require('dap').set_breakpoint(nil, nil, vim.fn.input 'Log point message: ') end, desc = 'Debug: Log Point' },

    -- UI and inspection
    { '<leader>dap', function() require('dapui').toggle() end,           desc = 'Debug: Toggle DAP UI' },
    { '<leader>dr',  function() require('dap').repl.open() end,          desc = 'Debug: Open REPL' },
    { '<leader>dh',  function() require('dap.ui.widgets').hover() end,   desc = 'Debug: Hover Variable', mode = { 'n', 'v' } },
    { '<leader>dp',  function() require('dap.ui.widgets').preview() end, desc = 'Debug: Preview', mode = { 'n', 'v' } },
  },
  -- stylua: ignore end

  config = function()
    local dap = require 'dap'
    local dapui = require 'dapui'

    require('mason-nvim-dap').setup {
      -- Makes a best effort to setup the various debuggers with
      -- reasonable debug configurations
      automatic_installation = true,

      -- You can provide additional configuration to the handlers,
      -- see mason-nvim-dap README for more information
      handlers = {},

      -- You'll need to check that you have the required things installed
      -- online, please don't ask me how to install them :)
      ensure_installed = {
        -- Update this to ensure that you have the debuggers for the langs you want
        'delve', -- Go
        'debugpy', -- Python
      },
    }

    -----------------------------------------------------------
    -- DAP UI
    -----------------------------------------------------------
    -- For more information, see |:help nvim-dap-ui|
    dapui.setup {
      -- Set icons to characters that are more likely to work in every terminal.
      --    Feel free to remove or use ones that you like more! :)
      --    Don't feel like these are good choices.
      icons = { expanded = '▾', collapsed = '▸', current_frame = '*' },
      controls = {
        icons = {
          pause = '⏸',
          play = '▶',
          step_into = '⏎',
          step_over = '⏭',
          step_out = '⏮',
          step_back = 'b',
          run_last = '▶▶',
          terminate = '⏹',
          disconnect = '⏏',
        },
      },
    }

    -----------------------------------------------------------
    -- Virtual text (inline variable values while debugging)
    -----------------------------------------------------------
    require('nvim-dap-virtual-text').setup()

    -----------------------------------------------------------
    -- Breakpoint visuals (uncomment if you have nerd font)
    -----------------------------------------------------------
    vim.api.nvim_set_hl(0, 'DapBreak', { fg = '#e51400' })
    vim.api.nvim_set_hl(0, 'DapStop', { fg = '#ffcc00' })
    local breakpoint_icons = vim.g.have_nerd_font and { Breakpoint = '', BreakpointCondition = '', BreakpointRejected = '', LogPoint = '', Stopped = '' }
      or { Breakpoint = '●', BreakpointCondition = '⊜', BreakpointRejected = '⊘', LogPoint = '◆', Stopped = '⭔' }
    for type, icon in pairs(breakpoint_icons) do
      local tp = 'Dap' .. type
      local hl = (type == 'Stopped') and 'DapStop' or 'DapBreak'
      vim.fn.sign_define(tp, { text = icon, texthl = hl, numhl = hl })
    end

    -- Auto open/close DAP UI on debug session events
    dap.listeners.after.event_initialized['dapui_config'] = dapui.open
    dap.listeners.before.event_terminated['dapui_config'] = dapui.close
    dap.listeners.before.event_exited['dapui_config'] = dapui.close

    -----------------------------------------------------------
    -- Python (debugpy)
    -----------------------------------------------------------
    -- debugpy is itself a Python program, so it needs a Python
    -- interpreter to run. Mason installs debugpy into its own
    -- isolated venv — this path points to THAT venv's python.
    -- This is NOT your project's interpreter. When you debug your
    -- code, debugpy automatically uses your project's python/venv.
    local debugpy_python = vim.fn.stdpath 'data' .. '/mason/packages/debugpy/venv/bin/python'
    require('dap-python').setup(debugpy_python)

    -- When you press <continue> with no active debug session, nvim-dap
    -- shows a picker with these pre-registered configurations:
    --   1. Launch file              — debug the current file
    --   2. Launch file with arguments — prompts for CLI args first
    --   3. Attach remote            — connect to a running process
    --                                 (e.g. a server started with debugpy)

    -----------------------------------------------------------
    -- Go (delve)
    -----------------------------------------------------------
    require('dap-go').setup {
      delve = {
        -- On Windows delve must be run attached or it crashes.
        -- See https://github.com/leoluz/nvim-dap-go/blob/main/README.md#configuring
        detached = vim.fn.has 'win32' == 0,
      },
    }
  end,
}
