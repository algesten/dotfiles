vim.opt.clipboard = 'unnamedplus'   -- use system clipboard 
vim.opt.completeopt = {'menu', 'menuone', 'noselect'}

-- Tab
vim.opt.tabstop = 4                 -- number of visual spaces per TAB
vim.opt.softtabstop = 4             -- number of spacesin tab when editing
vim.opt.shiftwidth = 4              -- insert 4 spaces on a tab
vim.opt.expandtab = true            -- tabs are spaces, mainly because of python
--vim.opt.termguicolors = true        -- lots and lots of terminal colors
vim.opt.syntax = 'on'
vim.opt.hlsearch = true
vim.opt.incsearch = true
vim.opt.scrolloff = 8

vim.opt.colorcolumn = '120'

-- UI config
vim.opt.number = true               -- show absolute number
--vim.opt.relativenumber = true       -- add numbers to each line on the
vim.opt.splitbelow = true           -- open new vertical split bottom
vim.opt.splitright = true           -- open new horizontal splits right

-- Searching
vim.opt.incsearch = true            -- search as characters are entered
vim.opt.ignorecase = true           -- ignore case in searches by default
vim.opt.smartcase = true            -- but make it case sensitive if an uppercase is entered
