-- define common options
local opts = {
    noremap = true,      -- non-recursive
    silent = true,       -- do not show message
}

vim.keymap.set('n', '<C-a>', '<Home>', opts)
vim.keymap.set('n', '<C-e>', '<End>', opts)

