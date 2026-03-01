-- [[ Configure and install plugins ]]
--
--  To check the current status of your plugins, run
--    :Lazy
--
--  You can press `?` in this menu for help. Use `:q` to close the window
--
--  To update plugins you can run
--    :Lazy update
--
-- NOTE: Here is where you install your plugins.
require('lazy').setup({
  -- NOTE: Plugins can be added with a link (or for a github repo: 'owner/repo' link).
  'NMAC427/guess-indent.nvim', -- Detect tabstop and shiftwidth automatically

  -- NOTE: Plugins can also be added by using a table,
  -- with the first argument being the link and the following
  -- keys can be used to configure plugin behavior/loading/etc.
  --
  -- Use `opts = {}` to automatically pass options to a plugin's `setup()` function, forcing the plugin to be loaded.

  -- modular approach: using `require 'path.name'` will
  -- include a plugin definition from file lua/path/name.lua

  -- Colorscheme
  -- require 'plugins.tokyonight',
  -- require 'plugins.nightfox',
  require 'plugins.catppuccin',

  require 'plugins.gitsigns',
  require 'plugins.which-key',
  require 'plugins.telescope',
  require 'plugins.lspconfig',
  require 'plugins.java',
  require 'plugins.mason',
  require 'plugins.conform',
  require 'plugins.blink-cmp',
  require 'plugins.betterquickfix',
  require 'plugins.inc-rename',

  require 'plugins.todo-comments',
  require 'plugins.helpview',

  -- Treesitter plugins
  require 'plugins.treesitter',
  require 'plugins.treesitter-textobjects',
  require 'plugins.treesitter-context',

  require 'plugins.accelerated-jk',
  require 'plugins.bufferline',
  require 'plugins.lualine',
  require 'plugins.debug',
  require 'plugins.lint',
  require 'plugins.snacks',
  require 'plugins.csvview',
  -- require 'plugins.lazygit',
  require 'plugins.noice',
  require 'plugins.neoscroll',
  require 'plugins.incline',
  require 'plugins.dadbod',
  require 'plugins.dadbod-ui',
  require 'plugins.diffview',
  require 'plugins.tmux-navigator',
  require 'plugins.undotree',
  require 'plugins.code-runner',

  -- File navigation
  require 'plugins.zoxide',
  require 'plugins.yazi',
  require 'plugins.neo-tree',
  require 'plugins.harpoon',

  -- For splitting/joining blocks of code like arrays, hashes, statements, objects, dictionaries, etc. - replaced by
  -- mini
  -- require 'plugins.treesj',
  require 'plugins.tabout',
  require 'plugins.flash',
  -- require 'plugins.quick-todo',
  require 'plugins.aerial',
  require 'plugins.render-markdown',
  require 'plugins.trouble',
  require 'plugins.vim-jukit',
  require 'plugins.betterterm',
  require 'plugins.vimtex',
  require 'plugins.luasnip',
  require 'plugins.hardtime',
  require 'plugins.neogit',
  -- Fast TypeScript/JS LSP replacement using native Tsserver protocol (faster than typescript-language-server)
  require 'plugins.typescript-tools',
  -- Tailwind CSS integration with color hints, class sorting, and utilities
  require 'plugins.tailwind-tools',
  require 'plugins.highlight-colors',
  -- Displays interactive vertical scrollbars and signs (see :help scrollview-configuration)
  -- Similar plugins: scrollbar and satellite
  require 'plugins.scrollview',
  require 'plugins.fidget',
  -- Opens buffer with cursor where you left off
  require 'plugins.stay',
  -- require 'plugins.borderline',
  -- Find and replace plugin
  require 'plugins.grug-far',
  require 'plugins.dooing',
  require 'plugins.marks',
  require 'plugins.spider',
  require 'plugins.smart-splits',

  -- Plugins I need to learn/use more
  require 'plugins.mini', -- surround etc.
  require 'plugins.unimpaired', -- Convenient binds for jumping around (e.g. methods)
  -- Needs to be added last
  require 'plugins.alpha',

  ------------------------- UNUSED START -------------------------
  -- require 'plugins.devicons',
  -- require 'plugins.notify',
  -- require 'plugins.lsp-notify',
  -- require 'plugins.indent_line',
  -- replaced by mini
  -- require 'plugins.autopairs',
  -- require 'plugins.vim-markdown',
  -- require 'plugins.markview',
  ------------------------- UNUSED END -------------------------

  -- For additional information with loading, sourcing and examples see `:help lazy.nvim-🔌-plugin-spec`
  -- Or use telescope!
  -- In normal mode type `<space>sh` then write `lazy.nvim-plugin`
  -- you can continue same window with `<space>sr` which resumes last telescope search
}, {
  ui = {
    -- If you are using a Nerd Font: set icons to an empty table which will use the
    -- default lazy.nvim defined Nerd Font icons, otherwise define a unicode icons table
    icons = vim.g.have_nerd_font and {} or {
      cmd = '⌘',
      config = '🛠',
      event = '📅',
      ft = '📂',
      init = '⚙',
      keys = '🗝',
      plugin = '🔌',
      runtime = '💻',
      require = '🌙',
      source = '📄',
      start = '🚀',
      task = '📌',
      lazy = '💤 ',
    },
  },
})

-- vim: ts=2 sts=2 sw=2 et
