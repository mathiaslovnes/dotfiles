return {
  "kndndrj/nvim-dbee",
  dependencies = {
    "MunifTanjim/nui.nvim",
  },
  build = function()
    -- Install tries to automatically detect the install method.
    -- if it fails, try calling it with one of these parameters:
    --    "curl", "wget", "bitsadmin", "go"
    require("dbee").install()
  end,
  config = function()
    require("dbee").setup({ --[[optional config]]
      -- drawer window config
      drawer = {
        mappings = {
          -- manually refresh drawer
          { key = "r",     mode = "n", action = "refresh" },
          -- actions perform different stuff depending on the node:
          -- action_1 opens a note or executes a helper
          { key = "<CR>",  mode = "n", action = "action_1" },
          -- action_2 renames a note or sets the connection as active manually
          { key = "cw",    mode = "n", action = "action_2" },
          -- action_3 deletes a note or connection (removes connection from the file if you configured it like so)
          { key = "dd",    mode = "n", action = "action_3" },
          -- these are self-explanatory:
          -- { key = "c", mode = "n", action = "collapse" },
          -- { key = "e", mode = "n", action = "expand" },
          { key = "o",     mode = "n", action = "toggle" },
          -- mappings for menu popups:
          { key = "<CR>",  mode = "n", action = "menu_confirm" },
          { key = "y",     mode = "n", action = "menu_yank" },
          { key = "<Esc>", mode = "n", action = "menu_close" },
          { key = "q",     mode = "n", action = "menu_close" },
        },
      }
    })

    vim.keymap.set("n", "<leader>db", function()
      require("dbee").toggle()
    end, { desc = "Toggle Dbee" })
  end,
}
