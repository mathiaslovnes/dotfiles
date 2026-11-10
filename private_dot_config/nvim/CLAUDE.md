# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a personal Neovim configuration (Neovim 0.12). All configuration is written in Lua.

## Architecture

Loading order defined in `init.lua`:
1. `lua/options.lua` — editor options (tabs, indent, fold, etc.)
2. `lua/keymaps.lua` — global keymaps (leader = `<Space>`)
3. `lua/highlights.lua` — colorscheme-independent highlight overrides, re-applied on every `ColorScheme` event (must load before plugins so it catches the first colorscheme load)
4. `lua/lazy-bootstrap.lua` — auto-installs lazy.nvim if missing
5. `lua/lazy-plugins.lua` — registers all plugins with lazy.nvim
6. `lua/jukit_dividers.lua` — jukit cell dividers (see Python / Jupyter Workflow)
7. `lua/autocmds.lua` — autocommands, including the one that starts treesitter per buffer

`init.lua` also sets the `vim.g.jukit_*` globals that must exist before vim-jukit loads.

Each plugin lives in its own file under `lua/plugins/`. To add a plugin, create a new file there and `require` it in `lazy-plugins.lua`. To disable a plugin temporarily, comment out its `require` line in `lazy-plugins.lua` (several examples exist in the `UNUSED` block at the bottom).

## Key Plugin Categories

| Category | Plugin(s) |
|---|---|
| Completion | `blink-cmp` + `luasnip` (friendly-snippets loaded per filetype) |
| LSP | `lspconfig` + `mason` (auto-installs servers) |
| Formatting | `conform.nvim` (stylua for Lua; LSP fallback for others) |
| Linting | none (`plugins/lint.lua` exists but is commented out in lazy-plugins.lua) |
| Fuzzy finding | `telescope` (file/grep searches) + `snacks.nvim` (LSP nav, git, pickers) |
| File navigation | `harpoon`, `yazi`, `neo-tree`, `zoxide` |
| Git | `gitsigns`, `neogit`, `diffview`, `snacks` lazygit integration |
| Treesitter | `treesitter` (main branch), `treesitter-textobjects`, `treesitter-context` |
| Python/Jupyter | `vim-jukit` (cells sent to IPython in a tmux pane); `plugins/pyworks.lua` is unused |
| UI | `catppuccin` (active colorscheme), `bufferline`, `lualine`, `noice`, `snacks` |
| Surround/text ops | `mini` (surround, comment, bufremove, trailspace, split-join) |

## Treesitter

nvim-treesitter is on its `main` branch: `plugins/treesitter.lua` only installs parsers. A FileType autocmd in `autocmds.lua` starts the highlighter and sets treesitter indent for every buffer with a parser except latex and tmux, jukit notebooks included.

## LSP Servers (auto-installed via Mason)

`clangd`, `gopls`, `rust_analyzer`, `pyright`, `sqlls`, `jdtls`, `svelte`, `cssls`, `css_variables`, `cssmodules_ls`, `lua_ls`

TypeScript uses `typescript-tools.nvim` (native tsserver protocol), not ts_ls; mason-lspconfig's `automatic_enable` excludes `ts_ls` and `jdtls` (nvim-java enables jdtls itself). nvim-java and typescript-tools load only for their filetypes. pyright treats `.envrc` as a root marker and uses the folder's direnv venv (`.direnv/*/bin/python`).

## Snacks vs Telescope

Both are active. Snacks handles LSP navigation (`gd`, `gr`, `gI`, `gy`), git pickers (`<leader>gl`, `<leader>gs`), and general search (`<leader>s*`). Telescope is used for file finding, colorscheme switching, and some LSP actions defined in `lspconfig.lua` (`grr`, `gri`, `grd`, `gO`, `gW`, `grt`).

## Python / Jupyter Workflow

Notebooks are vim-jukit `.py` files: cells are split by `# |%%--%%| <id|id>` lines, and markdown cells are `r"""°°° ... °°°"""` strings. jukit (`lua/plugins/vim-jukit.lua`) sends cells to an IPython pane in tmux; its buffer maps only exist in `.py`/`.ipynb` buffers (`g:jukit_mappings_ext_enabled` in init.lua).
- Markdown in text cells comes from treesitter: `after/queries/python/injections.scm` injects markdown into `°°°` strings, and render-markdown renders it. jukit's own vim-syntax region `textcell` doesn't show, because the treesitter highlighter turns vim syntax off.
- `lua/jukit_dividers.lua`: a decoration provider (namespace `pyworks_deco`) that draws the cell divider lines and hides the `°°°` lines on the visible lines at redraw time.
- `autoload/jukit/tmux/layouts.vim` shadows jukit's layout function and calls `lua/jukit_tmux_layout.lua` (output panes at the far right, columns evenly sized).

## Custom Global Helpers (available after `VeryLazy`)

```lua
dd(...)  -- Snacks.debug.inspect (pretty-print)
bt()     -- Snacks.debug.backtrace
```

## After/Queries

`after/queries/python/injections.scm` injects markdown inside `°°°` strings (jukit text cells), and `highlights.scm` mutes `# |` divider comments. Don't conceal string contents there: render-markdown sets conceallevel 3 in Python buffers, so concealed text disappears.
