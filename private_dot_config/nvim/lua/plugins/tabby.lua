return {
  "nanozuki/tabby.nvim",
  event = "VimEnter",
  dependencies = { "nvim-tree/nvim-web-devicons" }, -- or "echasnovski/mini.icons"
  config = function()
    vim.o.showtabline = 2

    local theme = {
      fill = "TabLineFill",
      head = "TabLine",
      current_tab = "TabLineSel",
      tab = "TabLine",
      win = "TabLine",
      tail = "TabLine",
    }

    require("tabby").setup({
      preset = "active_wins_at_tail",
      option = {
        theme = {
          fill = "TabLineFill",
          head = "TabLine",
          current_tab = "TabLineSel",
          tab = "TabLine",
          win = "TabLine",
          tail = "TabLine",
        },
        nerdfont = true,
        lualine_theme = nil,
        tab_name = {
          name_fallback = function(tabid)
            return tabid
          end,
        },
        buf_name = {
          mode = "unique",
        },
      },
    })
  end,
  keys = {
    { "<leader>ta", "<cmd>$tabnew<CR>",           desc = "New tab" },
    { "<leader>tc", "<cmd>tabclose<CR>",          desc = "Close tab" },
    { "<leader>to", "<cmd>tabonly<CR>",           desc = "Close other tabs" },
    { "<leader>tn", "<cmd>tabn<CR>",              desc = "Next tab" },
    { "<leader>tp", "<cmd>tabp<CR>",              desc = "Prev tab" },
    { "<leader>tr", "<cmd>Tabby rename_tab ",     desc = "Rename tab" },
    { "<leader>tj", "<cmd>Tabby jump_to_tab<CR>", desc = "Jump to tab" },
    { "<leader>tw", "<cmd>Tabby pick_window<CR>", desc = "Pick window" },
  },
}
