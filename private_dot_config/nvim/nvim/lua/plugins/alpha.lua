return {
  'goolord/alpha-nvim',
  dependencies = { 'nvim-tree/nvim-web-devicons' },
  config = function()
    local alpha = require 'alpha'
    local dashboard = require 'alpha.themes.dashboard'
    local fortune = require 'alpha.fortune'

    -- doom-style ASCII header
    local header = {
      [[                                                                   ]],
      [[      ████ ██████           █████      ██                    ]],
      [[     ███████████             █████                            ]],
      [[     █████████ ███████████████████ ███   ███████████  ]],
      [[    █████████  ███    █████████████ █████ ██████████████  ]],
      [[   █████████ ██████████ █████████ █████ █████ ████ █████  ]],
      [[ ███████████ ███    ███ █████████ █████ █████ ████ █████ ]],
      [[██████  █████████████████████ ████ █████ █████ ████ ██████]],
    }

    -- colorize header (like doom)
    local function colorize_header()
      local lines = {}
      for i, chars in ipairs(header) do
        table.insert(lines, {
          type = 'text',
          val = chars,
          opts = {
            hl = 'StartLogo' .. i,
            shrink_margin = false,
            position = 'center',
          },
        })
      end
      return lines
    end

    -- doom-style center buttons
    dashboard.section.buttons.val = {
      dashboard.button('e', '  New file', ':ene | startinsert <CR>'),
      dashboard.button('f', '  Find file', ':Telescope find_files<CR>'),
      dashboard.button('g', '  Find word', ':Telescope live_grep<CR>'),
      dashboard.button('r', '  Recent files', ':Telescope oldfiles<CR>'),
      dashboard.button('c', '  Config', ':e $MYVIMRC<CR>'),
      dashboard.button('q', '  Quit NVIM', ':qa<CR>'),
    }

    -- dashboard.section.footer.val = fortune() -- Generate quotes

    -- hide UI while in dashboard
    local group = vim.api.nvim_create_augroup('CleanDashboard', {})
    vim.api.nvim_create_autocmd('User', {
      group = group,
      pattern = 'AlphaReady',
      callback = function()
        vim.opt.showtabline = 0
        vim.opt.showmode = false
        vim.opt.laststatus = 0
        vim.opt.showcmd = false
        vim.opt.ruler = false
      end,
    })
    vim.api.nvim_create_autocmd('BufUnload', {
      group = group,
      pattern = '<buffer>',
      callback = function()
        vim.opt.showtabline = 2
        vim.opt.showmode = true
        vim.opt.laststatus = 3
        vim.opt.showcmd = true
        vim.opt.ruler = true
      end,
    })

    -- final setup
    alpha.setup {
      layout = {
        { type = 'padding', val = math.floor(vim.fn.winheight(0) * 0.33) },
        { type = 'group', val = colorize_header() },
        { type = 'padding', val = 2 },
        dashboard.section.buttons,
        dashboard.section.footer,
      },
      opts = { margin = 5 },
    }
  end,
}
