return {
  'monaqa/dial.nvim',
  -- stylua: ignore start
  keys = {
    { "<C-a>", function() require("dial.map").manipulate("increment", "normal") end, desc = "Increment" },
    { "<C-x>", function() require("dial.map").manipulate("decrement", "normal") end, desc = "Decrement" },
    { "g<C-a>", function() require("dial.map").manipulate("increment", "gnormal") end, desc = "Increment (g)" },
    { "g<C-x>", function() require("dial.map").manipulate("decrement", "gnormal") end, desc = "Decrement (g)" },
    { "<C-a>", function() require("dial.map").manipulate("increment", "visual") end, mode = "v", desc = "Increment" },
    { "<C-x>", function() require("dial.map").manipulate("decrement", "visual") end, mode = "v", desc = "Decrement" },
    { "g<C-a>", function() require("dial.map").manipulate("increment", "gvisual") end, mode = "v", desc = "Increment (g)" },
    { "g<C-x>", function() require("dial.map").manipulate("decrement", "gvisual") end, mode = "v", desc = "Decrement (g)" },
  },
  -- stylua: ignore end
  config = function()
    local augend = require 'dial.augend'
    require('dial.config').augends:register_group {
      default = {
        augend.semver.alias.semver, -- version tags, e.g. 0.9.1
        augend.integer.alias.decimal_int,
        augend.integer.alias.hex,
        augend.date.alias['%Y/%m/%d'],
        augend.date.alias['%m/%d/%Y'],
        augend.date.alias['%d/%m/%Y'],
        augend.date.alias['%m/%d/%y'],
        augend.date.alias['%d/%m/%y'],
        augend.date.alias['%m/%d'],
        augend.date.alias['%-m/%-d'],
        augend.date.alias['%Y-%m-%d'],
        augend.date.alias['%d.%m.%Y'],
        augend.date.alias['%d.%m.%y'],
        augend.date.alias['%d.%m.'],
        augend.date.alias['%-d.%-m.'],
        augend.date.alias['%H:%M'],
        augend.constant.alias.en_weekday,
        augend.constant.alias.en_weekday_full,
        augend.constant.alias.bool, -- true/false
        augend.constant.alias.Bool, -- True/False
        augend.constant.new { elements = { '&&', '||' }, word = false, cyclic = true },
        augend.constant.new { elements = { 'let', 'const' }, word = true, cyclic = true },
        augend.constant.new { elements = { 'yes', 'no' }, word = true, cyclic = true },
      },
    }
  end,
}
