return {
  {
    'akinsho/bufferline.nvim',
    dependencies = 'nvim-tree/nvim-web-devicons', -- optional, for icons
    version = '*', -- recommended to avoid breaking changes
    config = function()
      require('bufferline').setup {
        options = {
          numbers = 'ordinal', -- show buffer numbers
          diagnostics = 'nvim_lsp', -- show LSP diagnostics in bufferline
          close_command = 'bdelete! %d', -- how to close buffers
          right_mouse_command = 'bdelete! %d',
          left_trunc_marker = '',
          right_trunc_marker = '',
          offsets = { { filetype = 'NvimTree', text = 'Explorer', padding = 1 } },
          show_buffer_close_icons = true,
          show_close_icon = true,
          enforce_regular_tabs = false,
          separator_style = 'slant', -- can also be "thick", "thin", or "padded_slant"
          always_show_bufferline = true,
        },
      }
    end,
  },
}
