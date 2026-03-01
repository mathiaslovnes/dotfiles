; extends

; Disable highlighting for comments starting with #| (your divider pattern)
((comment) @_divider_comment
  (#match? @_divider_comment "^#\\|")
  (#set! "priority" 0))

; Disable Python string highlighting for raw docstrings (so markdown highlighting shows through)
((string
  (string_start) @_start
  (string_content) @nohl
  (string_end) @_end)
 (#match? @_start "^r['\"]")
 (#set! @nohl "conceal" ""))
