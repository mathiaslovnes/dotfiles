return {
  { -- Autoformat
    'stevearc/conform.nvim',
    event = { 'BufWritePre' },
    cmd = { 'ConformInfo' },
    keys = {
      {
        '=',
        function()
          require('conform').format { async = true, lsp_format = 'fallback' }
          require('mini.trailspace').trim()
        end,
        mode = 'n',
        desc = 'Format buffer',
      },
    },
    opts = {
      formatters = {
        stylua = {
          args = { '--column-width', '0' },
        },
        -- --config goes before the subcommand; --line-length there makes ruff exit with an error
        ruff_format = { prepend_args = { '--config', 'line-length=100' } },
        ruff_organize_imports = { prepend_args = { '--config', 'line-length=100' } },
      },
      formatters_by_ft = {
        lua = { 'stylua' },
        python = { 'ruff_organize_imports', 'ruff_format' },
        javascript = { 'prettier' },
        javascriptreact = { 'prettier' },
        typescript = { 'prettier' },
        typescriptreact = { 'prettier' },
        -- java = { 'google-java-format' },
      },
      -- Conform can also run multiple formatters sequentially
      -- python = { "isort", "black" },
      --
      -- You can use 'stop_after_first' to run the first available formatter from the list
      -- javascript = { "prettierd", "prettier", stop_after_first = true },
      notify_on_error = false,
      format_on_save = function(bufnr)
        -- Disable "format_on_save lsp_fallback" for languages that don't
        -- have a well standardized coding style. You can add additional
        -- languages here or re-enable it for the disabled ones.
        local disable_filetypes = { c = true, cpp = true, java = true }
        if disable_filetypes[vim.bo[bufnr].filetype] then
          return nil
        else
          return {
            timeout_ms = 500,
            lsp_format = 'fallback',
          }
        end
      end,
    },
  },
}
