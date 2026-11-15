; extends

; Disable highlighting for comments starting with #| or # | (your divider pattern)
((comment) @_divider_comment
  (#match? @_divider_comment "^#\\s*|")
  (#set! "priority" 0))

; jukit markdown cells: plain text in the normal text color instead of the string color. Same priority as the
; string capture but later, so it wins over it; the injected markdown (headings, bold, code) still wins over it.
((string (string_content) @jukit.text)
 (#lua-match? @jukit.text "^°°°"))
