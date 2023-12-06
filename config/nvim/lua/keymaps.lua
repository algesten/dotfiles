-- define common options
local opts = {
    noremap = true,      -- non-recursive
    silent = true,       -- do not show message
}

vim.keymap.set({'n', 'v', 'i'}, '<C-a>', '<Home>', opts)
vim.keymap.set({'n', 'v', 'i'}, '<C-e>', '<End>', opts)

