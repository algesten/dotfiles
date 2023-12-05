require('options')
require('keymaps')
vim.cmd('source ~/.config/nvim/plug.vim')
vim.cmd('source ~/.config/nvim/packages.vim')
--vim.cmd('PlugInstall')

local lsp_zero = require('lsp-zero')

lsp_zero.on_attach(function(client, bufnr)
  -- see :help lsp-zero-keybindings
  -- to learn the available actions
  lsp_zero.default_keymaps({buffer = bufnr})
end)

require'lspconfig'.rust_analyzer.setup{}

