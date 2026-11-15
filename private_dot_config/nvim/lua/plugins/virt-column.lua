return {
  'lukas-reineke/virt-column.nvim',
  event = { 'BufReadPost', 'BufNewFile' },
  opts = {
    -- Thin vertical line instead of the solid ColorColumn block.
    -- Alternatives: '┊' (dotted), '╎' (dashed), '▕' (hairline at the right edge of the cell)
    char = '│',
    -- '+1' = one column after 'textwidth' (120), so a line of exactly 120 chars just touches it
    virtcolumn = '+1',
    -- Theme-aware subtle color (same group as trailing-space dots); survives colorscheme reloads
    highlight = 'Whitespace',
  },
}
