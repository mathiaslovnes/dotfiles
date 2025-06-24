" === .ideavimrc ===

" Basic settings
set number              " Show line numbers
set relativenumber      " Show relative line numbers
set clipboard=unnamedplus   " Use system clipboard
set hlsearch            " Highlight search results
set ignorecase smartcase " Smarter search


" === Line movement bindings ===
" Move current line down with Shift+J
nnoremap J :m .+1<CR>==

" Move current line up with Shift+K
nnoremap K :m .-2<CR>==

" Visual mode movement of selected lines
vnoremap J :m '>+1<CR>gv=gv
vnoremap K :m '<-2<CR>gv=gv

" === Leader key ===
let mapleader = " "

"" Example leader binding: clear search highlight
nnoremap <leader><space> :nohlsearch<CR>

" === remap split window to also close the original split window



" Map leader d to delete without copying to clipboard
nnoremap <leader>d "_d

" === Paste without overwriting register ===
xnoremap p "_dP

" Center cursor on screen when moving half page up/down
nnoremap <C-u> <C-u>zz
nnoremap <C-d> <C-d>zz

" === Clear search highlight with ESC ===
nnoremap <Esc> :nohlsearch<CR>

" === remap <leader>af to select entire function
nnoremap <leader>af {V}

nnoremap <CR> o<ESC>
nnoremap <leader><CR> O<ESC>

" Center screen when searching with 'n' or 'N'
nnoremap n nzzzv
nnoremap N Nzzzv


" Set tab indentation to 2 spaces
set tabstop=2
set shiftwidth=2
set expandtab

" Enable smart indent
set smartindent
set autoindent

" Keep cursor 8 lines from top/bottom while scrolling
set scrolloff=15

" Optional: show line numbers
set number
set relativenumber

" Remap U to toggle uppercase
nnoremap U ~

" Move 5 lines up and down with ctrl + j/k
nnoremap <C-j> 5j
nnoremap <C-k> 5k

" Remap H and L to go to the start and end of line
nnoremap H ^
nnoremap L $

" Ctrl + hjkl for moving between splits
nnoremap <C-h> <C-w>h
nnoremap <C-j> <C-w>j
nnoremap <C-k> <C-w>k
nnoremap <C-l> <C-w>l

" Keep visual selection after indent
vnoremap < <gv
vnoremap > >gv

" Center screen after hitting G and gg
nnoremap G Gzz
nnoremap gg ggzz

" Open config with <leader>ev
nnoremap <leader>ev :e ~/.ideavimrc<CR>
nnoremap <leader>lv :source ~/.ideavimrc<CR>
nnoremap <leader>q :wq<CR>

" Make <leader>w swap split views
nnoremap <leader>w <C-w>w

" Remap backspace
nnoremap <BS> a<BS><Esc>
nnoremap <C-x> a<BS><Esc>

" Shift + Enter makes a new line without moving cursor
nnoremap <S-CR> :call append(line('.') - 1, '')<CR>

" === END ===


