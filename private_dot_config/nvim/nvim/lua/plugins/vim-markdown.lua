return {
  'preservim/vim-markdown',
  config = function()
    vim.g.markdown_fenced_languages = { 'python', 'javascript', 'html', 'bash' } -- Add languages you use in code blocks
  end,
}
