-- stylua: ignore start
require('lazy').setup({
  -- ╔══════════════════════════════════════════════════════════════╗
  -- ║                        Colorscheme                         ║
  -- ╚══════════════════════════════════════════════════════════════╝
  require 'plugins.catppuccin',
  -- require 'plugins.tokyonight',
  -- require 'plugins.nightfox',

  -- ╔══════════════════════════════════════════════════════════════╗
  -- ║                     LSP & Completion                       ║
  -- ╚══════════════════════════════════════════════════════════════╝
  require 'plugins.lspconfig',        -- Core LSP client configuration
  require 'plugins.mason',            -- LSP/DAP/linter/formatter installer
  require 'plugins.blink-cmp',        -- Fast completion engine
  require 'plugins.java',             -- Enhanced Java LSP support (nvim-java)
  require 'plugins.typescript-tools', -- Native tsserver protocol (faster than typescript-language-server)
  require 'plugins.tailwind-tools',   -- Tailwind CSS color hints, class sorting, and utilities
  require 'plugins.fidget',           -- LSP progress notifications
  require 'plugins.inc-rename',       -- Incremental LSP rename with live preview
  -- require 'plugins.lightbulb',       -- Show lightbulb icon for available LSP code actions

  -- ╔══════════════════════════════════════════════════════════════╗
  -- ║                   Treesitter & Syntax                      ║
  -- ╚══════════════════════════════════════════════════════════════╝
  require 'plugins.treesitter',             -- Syntax highlighting, indentation, and code parsing
  require 'plugins.treesitter-textobjects', -- Select, move, swap via treesitter nodes (functions, classes, etc.)
  require 'plugins.treesitter-context',     -- Sticky header showing current function/class scope
  require 'plugins.autotag',                -- Auto-close and auto-rename HTML/JSX tags via treesitter
  require 'plugins.highlight-colors',       -- Inline color swatches for hex/rgb/hsl values

  -- ╔══════════════════════════════════════════════════════════════╗
  -- ║                  Debugging & Testing                       ║
  -- ╚══════════════════════════════════════════════════════════════╝
  require 'plugins.debug',   -- DAP client for multi-language debugging (Python, JS/TS, Java, C/Rust)
  require 'plugins.neotest', -- Test runner framework (pytest, Jest/Vitest, Java)
  -- require 'plugins.lint',    -- Async linting engine (nvim-lint)

  -- ╔══════════════════════════════════════════════════════════════╗
  -- ║                    Formatting & Code                       ║
  -- ╚══════════════════════════════════════════════════════════════╝
  require 'plugins.conform',     -- Lightweight formatter manager (prettier, stylua, black, etc.)
  require 'plugins.neogen',      -- Auto-generate docstrings for any language
  require 'plugins.luasnip',     -- Snippet engine with friendly-snippets collection
  require 'plugins.code-runner', -- Run code/files directly from the editor

  -- ╔══════════════════════════════════════════════════════════════╗
  -- ║                     Git Integration                        ║
  -- ╚══════════════════════════════════════════════════════════════╝
  require 'plugins.gitsigns',     -- Inline git blame, hunk staging, diff signs in the gutter
  require 'plugins.neogit',       -- Magit-style interactive git interface
  require 'plugins.git-conflict', -- Resolve git conflicts with a three-pane view
  require 'plugins.diffview',     -- Tabpage-based diff viewer for commits and file history
  -- require 'plugins.lazygit', -- Lazygit TUI integration (using Snacks instead)

  -- ╔══════════════════════════════════════════════════════════════╗
  -- ║                   File Navigation                          ║
  -- ╚══════════════════════════════════════════════════════════════╝
  require 'plugins.telescope', -- Fuzzy finder for files, buffers, grep, LSP symbols, and everything
  require 'plugins.neo-tree',  -- File explorer sidebar with git status
  require 'plugins.harpoon',   -- Pin and quick-switch between a handful of key files
  require 'plugins.yazi',      -- Terminal file manager integration
  require 'plugins.zoxide',    -- Jump to frecent directories from inside Neovim
  require 'plugins.aerial',    -- Code outline / symbol sidebar (functions, classes, etc.)

  -- ╔══════════════════════════════════════════════════════════════╗
  -- ║                    Motion & Editing                        ║
  -- ╚══════════════════════════════════════════════════════════════╝
  require 'plugins.flash',               -- Leap/sneak-style jump-to-char navigation with labels
  require 'plugins.spider',              -- Smarter w/e/b that stop at subWords and punctuation
  require 'plugins.accelerated-jk',      -- Hold j/k to accelerate vertical cursor movement
  require 'plugins.tabout',              -- Tab out of brackets, quotes, and other pairs
  require 'plugins.dial',                -- Increment/decrement dates, booleans, hex, and more with <C-a>/<C-x>
  require 'plugins.substitute',          -- Operator for substituting text with register contents
  require 'plugins.yanky',               -- Paste history ring you can cycle through and search
  require 'plugins.vim-visual-multi',    -- Multiple cursors for simultaneous edits
  require 'plugins.various-textobjects', -- Extra textobjects for subwords and other selections
  require 'plugins.mini',                -- Swiss-army kit: surround, trailspace, splitjoin, bufremove, etc.
  require 'plugins.unimpaired',          -- Bracket-based mappings for jumping between methods, quickfix, etc.
  -- require 'plugins.treesj',           -- Split/join code blocks (replaced by mini.splitjoin)

  -- ╔══════════════════════════════════════════════════════════════╗
  -- ║                      UI & Visuals                          ║
  -- ╚══════════════════════════════════════════════════════════════╝
  require 'plugins.bufferline',                 -- Tab-like buffer bar at the top
  -- require 'plugins.tabby',
  require 'plugins.lualine',                    -- Statusline with mode, git, diagnostics, etc.
  require 'plugins.incline',                    -- Floating filename labels on splits
  require 'plugins.noice',                      -- Replaces cmdline, messages, and popupmenu with modern UI
  require 'plugins.neoscroll',                  -- Smooth scrolling animations
  require 'plugins.scrollview',                 -- Interactive vertical scrollbar with signs
  require 'plugins.illuminate',                 -- Highlight other occurrences of the word under cursor
  require 'plugins.unidentified-flying-object', -- nvim-ufo: modern code folding with virtual preview text
  require 'plugins.snacks',                     -- Utility suite: lazygit, dashboard, notifications, etc.
  -- require 'plugins.alpha',                    -- Startup dashboard (using Snacks instead)

  -- ╔══════════════════════════════════════════════════════════════╗
  -- ║                 Color Pickers & Tools                      ║
  -- ╚══════════════════════════════════════════════════════════════╝
  require 'plugins.cccccc',             -- Inline color picker (ccc.nvim)
  require 'plugins.oklch-color-picker', -- Advanced color picker with hue/saturation in a separate OS window

  -- ╔══════════════════════════════════════════════════════════════╗
  -- ║                  Terminals & Databases                     ║
  -- ╚══════════════════════════════════════════════════════════════╝
  require 'plugins.betterterm',     -- Improved floating/split terminal management
  require 'plugins.tmux-navigator', -- Seamless Ctrl/Cmd+hjkl navigation between Neovim and tmux panes
  require 'plugins.smart-splits',   -- Resize and navigate splits across Neovim and tmux
  -- require 'plugins.dbee',           -- Database client (Postgres, MySQL, SQLite, etc.)
  require 'plugins.dadbod',         -- Database client (Postgres, MySQL, SQLite, etc.)
  require 'plugins.dadbod-ui',      -- Interactive UI for dadbod queries and connections

  -- ╔══════════════════════════════════════════════════════════════╗
  -- ║              Domain-Specific & Filetype                    ║
  -- ╚══════════════════════════════════════════════════════════════╝
  require 'plugins.vim-jukit',       -- Jupyter-style notebook workflow (code cells, inline plots via Kitty)
  require 'plugins.vimtex',          -- Full-featured LaTeX editing, compilation, and PDF sync
  require 'plugins.csvview',         -- Pretty-print and align CSV columns
  require 'plugins.render-markdown', -- Rich markdown preview with inline rendering

  -- ╔══════════════════════════════════════════════════════════════╗
  -- ║                  Workflow & Utilities                       ║
  -- ╚══════════════════════════════════════════════════════════════╝
  require 'plugins.which-key',      -- Popup showing available keybinding continuations
  require 'plugins.todo-comments',  -- Highlight and search TODO/FIXME/HACK/NOTE comments
  require 'plugins.helpview',       -- Enhanced :help viewer with syntax highlighting
  require 'plugins.trouble',        -- Pretty diagnostics, references, and quickfix list
  require 'plugins.betterquickfix', -- Enhanced quickfix window with previews
  require 'plugins.undotree',       -- Visual undo history tree browser
  require 'plugins.grug-far',       -- Project-wide find and replace
  require 'plugins.marks',          -- Visible marks in the gutter with keybindings to manage them
  require 'plugins.dooing',         -- Simple todo list manager
  require 'plugins.stay',           -- Restore cursor position when reopening buffers
  require 'plugins.hardtime',       -- Break bad habits by discouraging repeated hjkl spam
  -- require 'plugins.quick-todo',  -- Quick inline todo (disabled)

  -- ╔══════════════════════════════════════════════════════════════╗
  -- ║                        Unused                              ║
  -- ╚══════════════════════════════════════════════════════════════╝
  -- require 'plugins.devicons',       -- File type icons
  -- require 'plugins.notify',         -- Notification popups (using noice/snacks instead)
  -- require 'plugins.lsp-notify',     -- LSP-specific notifications
  -- require 'plugins.indent_line',    -- Indentation guide lines
  -- require 'plugins.vim-markdown',   -- Markdown extras (using render-markdown instead)
  -- require 'plugins.markview',       -- Markdown viewer (using render-markdown instead)
  -- require 'plugins.borderline',     -- Window border styling
  -- stylua: ignore end
}, {
  ui = {
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
