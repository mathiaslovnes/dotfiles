return {
  'luk400/vim-jukit',
  ft = { 'python', 'ipynb' },
  config = function()
    vim.g.jukit_terminal = 'tmux' -- Optional: Set terminal for plotting
    vim.g.jukit_use_uberzug = 1
    vim.g.jukit_python_os_cmd = 'ipython3'

    -- trying this out

    ----------

    vim.g.jukit_layout = {
      split = 'horizontal',
      p1 = 0.67, -- 50% for file_content, 50% for the vertical split
      val = {
        'file_content',
        {
          split = 'vertical',
          p1 = 0.5, -- 60% for output, 40% for output_history
          val = { 'output', 'output_history' },
        },
      },
    }
  end,
}
