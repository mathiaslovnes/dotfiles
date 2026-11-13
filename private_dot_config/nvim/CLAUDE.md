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
| Formatting | `conform.nvim` (stylua for Lua, ruff for Python, prettier for JS/TS; LSP fallback for others) |
| Linting | the ruff language server, narrowed to unused imports/variables and redefinitions (`plugins/lint.lua` is commented out) |
| Fuzzy finding | `snacks.picker` (files, grep, LSP lists, git); `plugins/telescope.lua` is commented out |
| File navigation | `harpoon`, `yazi`, `neo-tree`, `zoxide` |
| Git | `gitsigns`, `neogit`, `diffview`, `snacks` lazygit integration |
| Treesitter | `treesitter` (main branch), `treesitter-textobjects`, `treesitter-context` |
| Python/Jupyter | `vim-jukit` (cells sent to IPython in a tmux pane); `plugins/pyworks.lua` is unused |
| UI | `catppuccin` (active colorscheme), `bufferline`, `lualine`, `noice`, `snacks` |
| Surround/text ops | `mini` (surround, comment, bufremove, trailspace, split-join) |

## Treesitter

nvim-treesitter is on its `main` branch: `plugins/treesitter.lua` only installs parsers. A FileType autocmd in `autocmds.lua` starts the highlighter and sets treesitter indent for every buffer with a parser except latex and tmux, jukit notebooks included.

## LSP Servers (auto-installed via Mason)

`clangd`, `gopls`, `rust_analyzer`, `pyright`, `ruff`, `sqlls`, `jdtls`, `svelte`, `cssls`, `css_variables`, `cssmodules_ls`, `lua_ls`, `texlab`

The extra tools Mason installs (formatters) are in the `vim.list_extend(ensure_installed, ...)` list in `lspconfig.lua`; the list in `mason.lua` is overridden and does nothing. pyright's "is not accessed" hints are dropped by a `textDocument/diagnostic` handler in its `vim.lsp.config`, because pyright's `disableTaggedHints` only filters pushed diagnostics and Neovim 0.12 pulls them.

TypeScript uses `typescript-tools.nvim` (native tsserver protocol), not ts_ls; mason-lspconfig's `automatic_enable` excludes `ts_ls` and `jdtls` (nvim-java enables jdtls itself). nvim-java and typescript-tools load only for their filetypes. pyright treats `.envrc` as a root marker and uses the folder's direnv venv (`.direnv/*/bin/python`).

## Pickers and key scheme

Snacks' picker does all fuzzy finding: search (`<leader>s*`, `<leader>f`), LSP navigation (`gd`, `gD`, `gI`, `gy` in snacks.lua; `grr`, `gri`, `grd`, `gW`, `grt` in lspconfig.lua), git (`<leader>g*`) and `vim.ui.select`. Its picker keys (one-Esc close, `<C-x>` split, `<C-y>` replace the current buffer) are in snacks.lua's `picker` opts. Telescope is commented out.

`-` and `+` stand in for `[` and `]` (keymaps.lua, with remap so they reach `[d`, `]s` and the like; hardtime's `+` restriction is turned off for this, and vim-visual-multi, whose leader was `-`, is disabled).

treesitter-textobjects' jumps are `]` + letter (next) and `[` + letter (previous), with `a`/`i` + the same letter selecting that node: `f` function, `i` conditional, `o` loop, `a` parameter, `r` return, `t` comment, `x` regex. Class jumps with `]]`/`[[` (`]s` stays spell's next misspelling) and selects with `as`/`is`; in tex buffers `]]`/`[[` are vimtex's section jumps, mapped in vimtex.lua because vimtex skips keys that are already mapped. Conditionals use `i` because `ac`/`ic` select a jukit cell (mini.ai custom object in mini.lua); loops use `o` because `al`/`il` are mini.ai's "last" objects. The g-keys are Neovim's own (`gc` comment, `gx` open URL, `gf` file, `gt` tabs, `gO` symbols). gitsigns' hunk jumps are `]c`/`[c`.

## Python / Jupyter Workflow

Notebooks are vim-jukit `.py` files: cells are split by `# |%%--%%| <id|id>` lines, and markdown cells are `r"""°°° ... °°°"""` strings. jukit (`lua/plugins/vim-jukit.lua`) sends cells to an IPython pane in tmux; its buffer maps only exist in `.py`/`.ipynb` buffers (`g:jukit_mappings_ext_enabled` in init.lua).
- vim-jukit is the user's fork, loaded with lazy.nvim's dev mode from `~/Dev/vim-jukit` (a git clone of the fork; lazy never updates it). Edit and commit the plugin there, not under `~/.local/share/nvim/lazy`.
- Markdown in text cells comes from treesitter: `after/queries/python/injections.scm` injects markdown into `°°°` strings, and render-markdown renders it. jukit's own vim-syntax region `textcell` doesn't show, because the treesitter highlighter turns vim syntax off.
- `lua/jukit_dividers.lua`: a decoration provider (namespace `pyworks_deco`) that draws the cell divider lines and hides the `°°°` lines on the visible lines at redraw time.
- `autoload/jukit/tmux/layouts.vim` shadows jukit's layout function and calls `lua/jukit_tmux_layout.lua` (output panes at the far right, columns evenly sized).

## LaTeX

vimtex compiles with latexmk into `.texfiles/` and views in Skim (it jumps to the cursor after each build). Own keys replace some defaults: `<localleader>lc` starts/stops compiling (was `ll`), `lC` restarts it, `lb` builds once (was `lS`), `ld`/`lD` delete the build files / also the PDF (were `lc`/`lC`), `lt` toggles the outline, `lm` picks the main document (saved as an empty `<main>.tex.latexmain` marker, ignored in `~/.gitignore_global`; switching kills the old main's compiler), `lM` lists the insert-mode shortcuts (was `lm`); they're mapped in a `VimtexEventInitPre` autocmd in `vimtex.lua`, so vimtex skips the defaults they replace. texlab is the language server (completion, labels, outline). The LaTeX `FileType` autocmd in `autocmds.lua` sets conceal (snacks.image hides the source behind rendered math), spell and `<leader>wc` (`:VimtexCountWords!`). latexmk only rebuilds on content changes, so a `BufWritePost` autocmd reports the last build's result when a save had no edits.
- Overleaf clones resolve `\input`/`\usepackage` paths from the project root, but vimtex always uses the main file's folder as its root. A local-only `.texlabroot` at the project root (listed in the repo's `.git/info/exclude`) marks it: texlab reads it natively, latexmk gets it from `~/.config/latexmk/latexmkrc` (adds it to `TEXINPUTS`), and a `BufEnter` autocmd in `autocmds.lua` points vimtex's kpsewhich lookups (`TEXINPUTS`) and texcount (`-dir=`) at it.
- texlab stops at the nearest `.latexmkrc` before reaching `.texlabroot`, so don't put a `.latexmkrc` in an assignment folder.
- vimtex caches kpsewhich lookups by relative path, shared across projects (`~/.cache/vimtex/kpsewhich.json`), failures included. If `\input`s stop resolving, run `:VimtexClearCache kpsewhich`; give headless tests on copies of a project their own `g:vimtex_cache_root`, or they overwrite the real project's paths.

## Custom Global Helpers (available after `VeryLazy`)

```lua
dd(...)  -- Snacks.debug.inspect (pretty-print)
bt()     -- Snacks.debug.backtrace
```

## After/Queries

`after/queries/python/injections.scm` injects markdown inside `°°°` strings (jukit text cells), and `highlights.scm` mutes `# |` divider comments. Don't conceal string contents there: render-markdown sets conceallevel 3 in Python buffers, so concealed text disappears.
