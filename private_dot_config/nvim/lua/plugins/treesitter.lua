-- nvim-treesitter's main branch (Neovim 0.12): setup() only installs parsers; highlighting and indent
-- are started per buffer by the FileType autocmd in lua/autocmds.lua
return {
  'nvim-treesitter/nvim-treesitter',
  branch = 'main',
  lazy = false,
  build = ':TSUpdate',
  config = function()
    require('nvim-treesitter').install {
      'python',
      'sql',
      'bash',
      'c',
      'diff',
      'java',
      'javadoc',
      'html',
      'css',
      'lua',
      'luadoc',
      'query',
      'vim',
      'vimdoc',
      'markdown',
      'markdown_inline',
      'javascript',
      'typescript',
      'tsx',
      'svelte',
      'vue',
      'regex',
    }
  end,
}
