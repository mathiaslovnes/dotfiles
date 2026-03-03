# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a personal Neovim configuration. All configuration is written in Lua.

## Architecture

Loading order defined in `init.lua`:
1. `lua/options.lua` — editor options (tabs, indent, fold, etc.)
2. `lua/keymaps.lua` — global keymaps (leader = `<Space>`)
3. `lua/lazy-bootstrap.lua` — auto-installs lazy.nvim if missing
4. `lua/lazy-plugins.lua` — registers all plugins with lazy.nvim

Each plugin lives in its own file under `lua/plugins/`. To add a plugin, create a new file there and `require` it in `lazy-plugins.lua`. To disable a plugin temporarily, comment out its `require` line in `lazy-plugins.lua` (several examples exist in the `UNUSED` block at the bottom).

## Key Plugin Categories

| Category | Plugin(s) |
|---|---|
| Completion | `blink-cmp` + `luasnip` |
| LSP | `lspconfig` + `mason` (auto-installs servers) |
| Formatting | `conform.nvim` (stylua for Lua; LSP fallback for others) |
| Linting | `lint.lua` |
| Fuzzy finding | `telescope` (file/grep searches) + `snacks.nvim` (LSP nav, git, pickers) |
| File navigation | `harpoon`, `yazi`, `neo-tree`, `zoxide` |
| Git | `gitsigns`, `neogit`, `diffview`, `snacks` lazygit integration |
| Treesitter | `treesitter`, `treesitter-textobjects`, `treesitter-context` |
| Python/Jupyter | `pyworks.nvim` (molten + jupytext + image.nvim via kitty backend) |
| UI | `catppuccin` (active colorscheme), `bufferline`, `lualine`, `noice`, `snacks` |
| Surround/text ops | `mini` (surround, comment, bufremove, trailspace, split-join) |


## LSP Servers (auto-installed via Mason)

`clangd`, `gopls`, `rust_analyzer`, `pyright`, `sqlls`, `jdtls`, `ts_ls`, `svelte`, `cssls`, `css_variables`, `cssmodules_ls`, `lua_ls`

TypeScript uses `typescript-tools.nvim` (native tsserver protocol, faster than ts_ls).

## Snacks vs Telescope

Both are active. Snacks handles LSP navigation (`gd`, `gr`, `gI`, `gy`), git pickers (`<leader>gl`, `<leader>gs`), and general search (`<leader>s*`). Telescope is used for file finding, colorscheme switching, and some LSP actions defined in `lspconfig.lua` (`grr`, `gri`, `grd`, `gO`, `gW`, `grt`).

## Python / Jupyter Workflow

`pyworks.nvim` manages + jupytext + image.nvim. Uses `uv` for package management and the **kitty** terminal for image rendering. Jupyter notebook files are handled via jupytext conversion.

## Custom Global Helpers (available after `VeryLazy`)

```lua
dd(...)  -- Snacks.debug.inspect (pretty-print)
bt()     -- Snacks.debug.backtrace
```

## After/Queries

Custom tree-sitter queries for Python live in `after/queries/python/` — `injections.scm` and `highlights.scm` (used by pyworks_divider for section dividers and rainbow bold headers).
