; extends

; Disable highlighting for comments starting with #| or # | (your divider pattern)
((comment) @_divider_comment
  (#match? @_divider_comment "^#\\s*|")
  (#set! "priority" 0))
