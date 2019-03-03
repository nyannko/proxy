" Filetype dection
filetype on
" Load plugin with types
filetype plugin on

" Turn off vi compatible
" set nocompatible

" Enable mouse
set mouse=a

" Set spell
" set spell

" Set row number 
set nu
set relativenumber

" Delete any char
set backspace=2

" Enable syntax 
" syntax enable

" Ignore case when search
set ignorecase    
" Incremental search
set incsearch
set smartcase
" Highlight search
set hlsearch
" noh
nnoremap <Leader><space> :noh<Enter>

" Show current row and col
" set cursorline
" set cursorcolumn

" Move up/down editor lines
nnoremap j gj
nnoremap k gk

" Source .vimrc automatically
autocmd BufWritePost $MYVIMRC source $MYVIMRC

