" Shadows vim-jukit's autoload/jukit/tmux/layouts.vim (this config comes first in 'runtimepath').
" The layout logic lives in lua/jukit_tmux_layout.lua.
fun! jukit#tmux#layouts#set_layout(layout) abort
    call luaeval('require("jukit_tmux_layout").set_layout(_A)', a:layout)
endfun
