return {
  'MagicDuck/grug-far.nvim',
  cmd = { 'GrugFar', 'GrugFarWithin' },
  keys = {
    -- Search in visually selected block
    { '<leader>rp', ':GrugFarWithin<CR>', mode = 'x', desc = 'Search & Replace (selection)' },
    -- Search recursively (only for same filetypes, e.g. .py)
    {
      '<leader>rp',
      function()
        local ext = vim.fn.expand '%:e'
        require('grug-far').open { prefills = { filesFilter = ext ~= '' and '*.' .. ext or nil } }
      end,
      desc = 'Search & Replace Recursively',
    },
    -- Search in current buffer
    {
      '<leader>srf',
      function()
        require('grug-far').open { prefills = { paths = vim.fn.expand '%' } }
      end,
      desc = 'Search & Replace (current filetype)',
    },
    -- Search in open buffers
    {
      '<leader>srb',
      function()
        require('grug-far').open { prefills = { paths = '<buflist>' } }
      end,
      desc = 'Search & Replace (open buffers)',
    },
    -- Search in buffers within cwd
    {
      '<leader>srB',
      function()
        require('grug-far').open { prefills = { paths = '<buflist-cwd>' } }
      end,
      desc = 'Search & Replace (open buffers only in cwd)',
    },
    -- Search in quickfix list
    {
      '<leader>srq',
      function()
        require('grug-far').open { prefills = { paths = '<qflist>' } }
      end,
      desc = 'Search & Replace (quickfix)',
    },
  },
  config = function()
    -- optional setup call to override plugin options
    -- alternatively you can set options with vim.g.grug_far = { ... }
    require('grug-far').setup {
      keymaps = {
        replace = { n = '<localleader>r' },
        qflist = { n = '<localleader>q' }, -- Send results to quickfix list
        -- Sync: Writes changes you made in the grug-far buffer back to the original files.
        syncLocations = { n = '<localleader>S' },
        syncLine = { n = '<localleader>sl' },
        close = { n = '<localleader>c' },
        historyOpen = { n = '<localleader>ho' }, -- Open search history buffer
        historyAdd = { n = '<localleader>ha' }, -- Add current search to history
        refresh = { n = '<localleader>f' },
        openLocation = { n = '<localleader>o' },
        openNextLocation = { n = '<down>' },
        openPrevLocation = { n = '<up>' },
        gotoLocation = { n = '<enter>' },
        pickHistoryEntry = { n = '<enter>' },
        abort = { n = '<localleader>b' },
        help = { n = '<localleader>?' },
        toggleShowCommand = { n = '<localleader>ts' }, -- Show the actual rg command being run (for debugging)
        swapEngine = { n = '<localleader>se' },
        swapReplacementInterpreter = { n = '<localleader>sri' },
        previewLocation = { n = '<localleader>pv' },
        applyNext = { n = '<localleader>j' },
        applyPrev = { n = '<localleader>k' },
        -- Sync: Writes changes you made in the grug-far buffer back to the original files.
        syncNext = { n = '<localleader>sn' },
        syncPrev = { n = '<localleader>sp' },
        syncFile = { n = '<localleader>sf' },
        nextInput = { n = '<C-f>' },
        prevInput = { n = '<C-b>' },
      },
    }
  end,
}
