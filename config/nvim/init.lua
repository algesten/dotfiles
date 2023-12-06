vim.cmd('source ~/.config/nvim/theme.vim')
vim.cmd('source ~/.config/nvim/plug.vim')

require('options')
require('keymaps')

local Plug = vim.fn['plug#']
vim.call('plug#begin', vim.fn.stdpath('data') .. '/plugged')

-- Highlight bad whitespace
Plug('ntpeters/vim-better-whitespace')

-- LSP Support
Plug('neovim/nvim-lspconfig')

-- Autocompletion
Plug('hrsh7th/nvim-cmp')
Plug('hrsh7th/cmp-nvim-lsp')
Plug('L3MON4D3/LuaSnip')

Plug('VonHeikemen/lsp-zero.nvim', { branch = 'v3.x' })

vim.call('plug#end')

-- Start language server
local lsp_zero = require('lsp-zero')
lsp_zero.on_attach(function(client, bufnr)
    -- see :help lsp-zero-keybindings
    -- to learn the available actions
    lsp_zero.default_keymaps({ buffer = bufnr })
end)

--require 'lspconfig'.lua_ls.setup {}
require 'lspconfig'.rust_analyzer.setup {
    settings = {
        ['rust-analyzer'] = {
            imports = {
                granularity = {
                    enforce = true,
                    group = 'module'
                }
            },
            cargo = {
                buildScripts = {
                    enable = true
                }
            }
        }
    }
}

-- rustfmt on save
vim.cmd [[autocmd BufWritePre <buffer> lua vim.lsp.buf.format()]]
