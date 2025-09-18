vim.g.snacks_animate = false
return {
  'folke/snacks.nvim',
  priority = 1000,
  lazy = false,
  ---@type snacks.Config
  opts = {
    -- your configuration comes here
    -- or leave it empty to use the default settings
    -- refer to the configuration section below
    image = { enabled = true },
    bigfile = { enabled = true },
    gitbrowse = {
      ---@class snacks.gitbrowse.Config
      ---@field url_patterns? table<string, table<string, string|fun(fields:snacks.gitbrowse.Fields):string>>
      {
        notify = true, -- show notification on open
        -- Handler to open the url in a browser
        ---@param url string
        open = function(url)
          if vim.fn.has 'nvim-0.10' == 0 then
            require('lazy.util').open(url, { system = true })
            return
          end
          vim.ui.open(url)
        end,
        ---@type "repo" | "branch" | "file" | "commit" | "permalink"
        what = 'commit', -- what to open. not all remotes support all types
        branch = nil, ---@type string?
        line_start = nil, ---@type number?
        line_end = nil, ---@type number?
        -- patterns to transform remotes to an actual URL
        remote_patterns = {
          { '^(https?://.*)%.git$', '%1' },
          { '^git@(.+):(.+)%.git$', 'https://%1/%2' },
          { '^git@(.+):(.+)$', 'https://%1/%2' },
          { '^git@(.+)/(.+)$', 'https://%1/%2' },
          { '^org%-%d+@(.+):(.+)%.git$', 'https://%1/%2' },
          { '^ssh://git@(.*)$', 'https://%1' },
          { '^ssh://([^:/]+)(:%d+)/(.*)$', 'https://%1/%3' },
          { '^ssh://([^/]+)/(.*)$', 'https://%1/%2' },
          { 'ssh%.dev%.azure%.com/v3/(.*)/(.*)$', 'dev.azure.com/%1/_git/%2' },
          { '^https://%w*@(.*)', 'https://%1' },
          { '^git@(.*)', 'https://%1' },
          { ':%d+', '' },
          { '%.git$', '' },
        },
        url_patterns = {
          ['github%.com'] = {
            branch = '/tree/{branch}',
            file = '/blob/{branch}/{file}#L{line_start}-L{line_end}',
            permalink = '/blob/{commit}/{file}#L{line_start}-L{line_end}',
            commit = '/commit/{commit}',
          },
          ['gitlab%.com'] = {
            branch = '/-/tree/{branch}',
            file = '/-/blob/{branch}/{file}#L{line_start}-L{line_end}',
            permalink = '/-/blob/{commit}/{file}#L{line_start}-L{line_end}',
            commit = '/-/commit/{commit}',
          },
          ['bitbucket%.org'] = {
            branch = '/src/{branch}',
            file = '/src/{branch}/{file}#lines-{line_start}-L{line_end}',
            permalink = '/src/{commit}/{file}#lines-{line_start}-L{line_end}',
            commit = '/commits/{commit}',
          },
          ['git.sr.ht'] = {
            branch = '/tree/{branch}',
            file = '/tree/{branch}/item/{file}',
            permalink = '/tree/{commit}/item/{file}#L{line_start}',
            commit = '/commit/{commit}',
          },
        },
      },
    },
    terminal = { enabled = true },
    -- dashboard = { enabled = true },
    explorer = { enabled = true },
    indent = { enabled = true },
    input = {
      backdrop = false,
      position = 'float',
      border = 'rounded',
      title_pos = 'center',
      height = 1,
      width = 60,
      relative = 'editor',
      noautocmd = true,
      row = 2,
      -- relative = "cursor",
      -- row = -3,
      -- col = 0,
      wo = {
        winhighlight = 'NormalFloat:SnacksInputNormal,FloatBorder:SnacksInputBorder,FloatTitle:SnacksInputTitle',
        cursorline = false,
      },
      bo = {
        filetype = 'snacks_input',
        buftype = 'prompt',
      },
      --- buffer local variables
      b = {
        completion = false, -- disable blink completions in input
      },
      keys = {
        n_esc = { '<esc>', { 'cmp_close', 'cancel' }, mode = 'n', expr = true },
        i_esc = { '<esc>', { 'cmp_close', 'stopinsert' }, mode = 'i', expr = true },
        i_cr = { '<cr>', { 'cmp_accept', 'confirm' }, mode = { 'i', 'n' }, expr = true },
        i_tab = { '<tab>', { 'cmp_select_next', 'cmp' }, mode = 'i', expr = true },
        i_ctrl_w = { '<c-w>', '<c-s-w>', mode = 'i', expr = true },
        i_up = { '<up>', { 'hist_up' }, mode = { 'i', 'n' } },
        i_down = { '<down>', { 'hist_down' }, mode = { 'i', 'n' } },
        q = 'cancel',
      },
    },
    picker = { enabled = true },
    notifier = { enabled = true },
    quickfile = { enabled = true },
    scope = { enabled = true },
    scroll = { enabled = true },
    statuscolumn = { enabled = false },
    words = { enabled = true },
    lazygit = {
      {
        -- automatically configure lazygit to use the current colorscheme
        -- and integrate edit with the current neovim instance
        configure = true,
        -- extra configuration for lazygit that will be merged with the default
        -- snacks does NOT have a full yaml parser, so if you need `"test"` to appear with the quotes
        -- you need to double quote it: `"\"test\""`
        config = {
          os = { editPreset = 'nvim-remote' },
          gui = {
            -- set to an empty string "" to disable icons
            nerdFontsVersion = '3',
          },
        },
        -- Theme for lazygit
        theme = {
          [241] = { fg = 'Special' },
          activeBorderColor = { fg = 'MatchParen', bold = true },
          cherryPickedCommitBgColor = { fg = 'Identifier' },
          cherryPickedCommitFgColor = { fg = 'Function' },
          defaultFgColor = { fg = 'Normal' },
          inactiveBorderColor = { fg = 'FloatBorder' },
          optionsTextColor = { fg = 'Function' },
          searchingActiveBorderColor = { fg = 'MatchParen', bold = true },
          selectedLineBgColor = { bg = 'Visual' }, -- set to `default` to have no background colour
          unstagedChangesColor = { fg = 'DiagnosticError' },
        },
        win = {
          style = 'lazygit',
        },
      },
    },
  },
}
