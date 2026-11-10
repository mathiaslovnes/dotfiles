; extends

; jukit markdown cells: r"""°°° ... °°°""" (each °°° is 6 bytes)
((string (string_content) @injection.content)
 (#lua-match? @injection.content "^°°°")
 (#offset! @injection.content 0 6 0 -6)
 (#set! injection.language "markdown"))

; ; extends
;
; ((string_content) @injection.content
;  (#set! injection.language "markdown")
;  (#gsub! @injection.content "^%s+" ""))


