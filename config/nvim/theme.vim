
"""
" Name: pitch black.vim
"""

set background=dark
hi clear

if exists('syntax on')
    syntax reset
endif

let g:colors_name='pitch black'
set t_Co=256


" rust

" hi rustUnionContextual          guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi rustAssert                   guisp=NONE guifg=#569dd6 guibg=#000000 ctermfg=74  ctermbg=16 gui=NONE cterm=NONE
" hi rustPanic                    guisp=NONE guifg=#569dd6 guibg=#000000 ctermfg=74  ctermbg=16 gui=NONE cterm=NONE
" hi rustDefault                  guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi rustPubScopeDelim            guisp=NONE guifg=#C586C0 guibg=#000000 ctermfg=175 ctermbg=16 gui=NONE cterm=NONE
" hi rustPubScope                 guisp=NONE guifg=#C586C0 guibg=#000000 ctermfg=175 ctermbg=16 gui=NONE cterm=NONE
" hi rustExternCrateString        guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi rustIdentifier               guisp=NONE guifg=#4FCAB0 guibg=#000000 ctermfg=79  ctermbg=16 gui=NONE cterm=NONE
" hi rustFuncName                 guisp=NONE guifg=#DCDCAA guibg=#000000 ctermfg=187 ctermbg=16 gui=NONE cterm=NONE
" hi rustBoxPlacement             guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi rustBoxPlacementBalance      guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi rustMacroRepeat              guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi rustMacroRepeatCount         guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi rustMacroVariable            guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi rustModPath                  guisp=NONE guifg=#4FCAB0 guibg=#000000 ctermfg=79  ctermbg=16 gui=NONE cterm=NONE
" hi rustModPathSep               guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi rustFuncCall                 guisp=NONE guifg=#DCDCAA guibg=#000000 ctermfg=187 ctermbg=16 gui=NONE cterm=NONE
" hi rustCapsIdent                guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi rustOperator                 guisp=NONE guifg=#569dd6 guibg=#000000 ctermfg=74  ctermbg=16 gui=NONE cterm=NONE
" hi rustSigil                    guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi rustArrowCharacter           guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi rustQuestionMark             guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi rustMacro                    guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi rustEscapeError              guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi rustEscape                   guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi rustEscapeUnicode            guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi rustStringContinuation       guisp=NONE guifg=#CE9278 guibg=#000000 ctermfg=174 ctermbg=16 gui=NONE cterm=NONE
" hi rustString                   guisp=NONE guifg=#CE9278 guibg=#000000 ctermfg=174 ctermbg=16 gui=NONE cterm=NONE
" hi rustAttribute                guisp=NONE guifg=#9DDCFF guibg=#000000 ctermfg=153 ctermbg=16 gui=NONE cterm=NONE
" hi rustDerive                   guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi rustDecNumber                guisp=NONE guifg=#B5CEA9 guibg=#000000 ctermfg=151 ctermbg=16 gui=NONE cterm=NONE
" hi rustHexNumber                guisp=NONE guifg=#B5CEA9 guibg=#000000 ctermfg=151 ctermbg=16 gui=NONE cterm=NONE
" hi rustOctNumber                guisp=NONE guifg=#B5CEA9 guibg=#000000 ctermfg=151 ctermbg=16 gui=NONE cterm=NONE
" hi rustBinNumber                guisp=NONE guifg=#B5CEA9 guibg=#000000 ctermfg=151 ctermbg=16 gui=NONE cterm=NONE
" hi rustFloat                    guisp=NONE guifg=#B5CEA9 guibg=#000000 ctermfg=151 ctermbg=16 gui=NONE cterm=NONE
" hi rustLifetimeCandidate        guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi rustGenericRegion            guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi rustGenericLifetimeCandidate guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi rustLifetime                 guisp=NONE guifg=#569dd6 guibg=#000000 ctermfg=74  ctermbg=16 gui=NONE cterm=NONE
" hi rustLabel                    guisp=NONE guifg=#4FCAB0 guibg=#000000 ctermfg=79  ctermbg=16 gui=NONE cterm=NONE
" hi rustCharacterInvalid         guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi rustCharacterInvalidUnicode  guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi rustCharacter                guisp=NONE guifg=#569dd6 guibg=#000000 ctermfg=74  ctermbg=16 gui=NONE cterm=NONE
" hi rustShebang                  guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi rustCommentLine              guisp=NONE guifg=#6A9956 guibg=#000000 ctermfg=65  ctermbg=16 gui=NONE cterm=NONE
" hi rustCommentLineDoc           guisp=NONE guifg=#6A9956 guibg=#000000 ctermfg=65  ctermbg=16 gui=NONE cterm=NONE
" hi rustCommentLineDocError      guisp=NONE guifg=#F14D4C guibg=#000000 ctermfg=203 ctermbg=16 gui=bold cterm=bold
" hi rustCommentBlock             guisp=NONE guifg=#6A9956 guibg=#000000 ctermfg=65  ctermbg=16 gui=NONE cterm=NONE
" hi rustCommentBlockDoc          guisp=NONE guifg=#6A9956 guibg=#000000 ctermfg=65  ctermbg=16 gui=NONE cterm=NONE
" hi rustCommentBlockDocError     guisp=NONE guifg=#F14D4C guibg=#000000 ctermfg=203 ctermbg=16 gui=bold cterm=bold
" hi rustCommentBlockNest         guisp=NONE guifg=#6A9956 guibg=#000000 ctermfg=65  ctermbg=16 gui=NONE cterm=NONE
" hi rustCommentBlockDocNest      guisp=NONE guifg=#6A9956 guibg=#000000 ctermfg=65  ctermbg=16 gui=NONE cterm=NONE
" hi rustCommentBlockDocNestError guisp=NONE guifg=#F14D4C guibg=#000000 ctermfg=203 ctermbg=16 gui=bold cterm=bold
" hi rustFoldBraces               guisp=NONE guifg=#C586C0 guibg=#000000 ctermfg=175 ctermbg=16 gui=NONE cterm=NONE
" hi rustIdentifierPrime          guisp=NONE guifg=#4FCAB0 guibg=#000000 ctermfg=79  ctermbg=16 gui=NONE cterm=NONE
" hi rustTrait                    guisp=NONE guifg=#4FCAB0 guibg=#000000 ctermfg=79  ctermbg=16 gui=NONE cterm=NONE
" hi rustDeriveTrait              guisp=NONE guifg=#DCDCAA guibg=#000000 ctermfg=187 ctermbg=16 gui=NONE cterm=NONE
" hi rustMacroRepeatDelimiters    guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi rustNumber                   guisp=NONE guifg=#B5CEA9 guibg=#000000 ctermfg=151 ctermbg=16 gui=NONE cterm=NONE
" hi rustBoolean                  guisp=NONE guifg=#569dd6 guibg=#000000 ctermfg=74  ctermbg=16 gui=NONE cterm=NONE
" hi rustEnum                     guisp=NONE guifg=#4FCAB0 guibg=#000000 ctermfg=79  ctermbg=16 gui=NONE cterm=NONE
" hi rustEnumVariant              guisp=NONE guifg=#569dd6 guibg=#000000 ctermfg=74  ctermbg=16 gui=NONE cterm=NONE
" hi rustConstant                 guisp=NONE guifg=#569dd6 guibg=#000000 ctermfg=74  ctermbg=16 gui=NONE cterm=NONE
" hi rustSelf                     guisp=NONE guifg=#569dd6 guibg=#000000 ctermfg=74  ctermbg=16 gui=NONE cterm=NONE
" hi rustKeyword                  guisp=NONE guifg=#569dd6 guibg=#000000 ctermfg=74  ctermbg=16 gui=NONE cterm=NONE
" hi rustTypedef                  guisp=NONE guifg=#569dd6 guibg=#000000 ctermfg=74  ctermbg=16 gui=NONE cterm=NONE
" hi rustStructure                guisp=NONE guifg=#4FCAB0 guibg=#000000 ctermfg=79  ctermbg=16 gui=NONE cterm=NONE
" hi rustUnion                    guisp=NONE guifg=#4FCAB0 guibg=#000000 ctermfg=79  ctermbg=16 gui=NONE cterm=NONE
" hi rustPubScopeCrate            guisp=NONE guifg=#569dd6 guibg=#000000 ctermfg=74  ctermbg=16 gui=NONE cterm=NONE
" hi rustSuper                    guisp=NONE guifg=#569dd6 guibg=#000000 ctermfg=74  ctermbg=16 gui=NONE cterm=NONE
" hi rustReservedKeyword          guisp=NONE guifg=#F14D4C guibg=#000000 ctermfg=203 ctermbg=16 gui=bold cterm=bold
" hi rustRepeat                   guisp=NONE guifg=#C586C0 guibg=#000000 ctermfg=175 ctermbg=16 gui=NONE cterm=NONE
" hi rustConditional              guisp=NONE guifg=#C586C0 guibg=#000000 ctermfg=175 ctermbg=16 gui=NONE cterm=NONE
" hi rustFunction                 guisp=NONE guifg=#DCDCAA guibg=#000000 ctermfg=187 ctermbg=16 gui=NONE cterm=NONE
" hi rustType                     guisp=NONE guifg=#4FCAB0 guibg=#000000 ctermfg=79  ctermbg=16 gui=NONE cterm=NONE
" hi rustTodo                     guisp=NONE guifg=#569dd6 guibg=#000000 ctermfg=74  ctermbg=16 gui=NONE cterm=NONE
" hi rustStorage                  guisp=NONE guifg=#569dd6 guibg=#000000 ctermfg=74  ctermbg=16 gui=NONE cterm=NONE
" hi rustObsoleteStorage          guisp=NONE guifg=#F14D4C guibg=#000000 ctermfg=203 ctermbg=16 gui=bold cterm=bold
" hi rustInvalidBareKeyword       guisp=NONE guifg=#F14D4C guibg=#000000 ctermfg=203 ctermbg=16 gui=bold cterm=bold
" hi rustExternCrate              guisp=NONE guifg=#569dd6 guibg=#000000 ctermfg=74  ctermbg=16 gui=NONE cterm=NONE
" hi rustObsoleteExternMod        guisp=NONE guifg=#569dd6 guibg=#000000 ctermfg=74  ctermbg=16 gui=NONE cterm=NONE
" hi rustBoxPlacementParens       guisp=NONE guifg=#DCDCAA guibg=#000000 ctermfg=187 ctermbg=16 gui=NONE cterm=NONE

" misc

" hi ColorColumn      guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi Conceal          guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi Cursor           guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi lCursor          guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi CursorIM         guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi CursorColumn     guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi CursorLine       guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi Directory        guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi DiffAdd          guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi DiffChange       guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi DiffDelete       guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi DiffText         guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi EndOfBuffer      guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi ErrorMsg         guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi VertSplit        guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi Folded           guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi FoldColumn       guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi SignColumn       guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi IncSearch        guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi LineNr           guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi LineNrAbove      guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi LineNrBelow      guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi CursorLineNr     guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi MatchParen       guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi ModeMsg          guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi MoreMsg          guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi NonText          guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi Pmenu            guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi PmenuSel         guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi PmenuSbar        guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi PmenuThumb       guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi Question         guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi QuickFixLine     guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi Search           guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi SpecialKey       guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi SpellBad         guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi SpellCap         guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi SpellLocal       guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi SpellRare        guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi StatusLine       guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi StatusLineNC     guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi StatusLineTerm   guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi StatusLineTermNC guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi TabLine          guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi TabLineFill      guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi TabLineSel       guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi Terminal         guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi Title            guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi Visual           guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi VisualNOS        guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi WarningMsg       guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
" hi WildMenu         guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE

" major

hi Normal     guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
hi Comment    guisp=NONE guifg=#6A9956 guibg=#000000 ctermfg=65  ctermbg=16 gui=NONE cterm=NONE
hi Constant   guisp=NONE guifg=#569dd6 guibg=#000000 ctermfg=74  ctermbg=16 gui=NONE cterm=NONE
hi Identifier guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
hi Statement  guisp=NONE guifg=#569dd6 guibg=#000000 ctermfg=74  ctermbg=16 gui=NONE cterm=NONE
hi PreProc    guisp=NONE guifg=#4FCAB0 guibg=#000000 ctermfg=79  ctermbg=16 gui=NONE cterm=NONE
hi Type       guisp=NONE guifg=#4FCAB0 guibg=#000000 ctermfg=79  ctermbg=16 gui=NONE cterm=NONE
hi Special    guisp=NONE guifg=#C586C0 guibg=#000000 ctermfg=175 ctermbg=16 gui=NONE cterm=NONE
hi Underlined guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
hi Ignore     guisp=NONE guifg=#dfdfdf guibg=#000000 ctermfg=254 ctermbg=16 gui=NONE cterm=NONE
hi Error      guisp=NONE guifg=#F14D4C guibg=#000000 ctermfg=203 ctermbg=16 gui=bold cterm=bold
hi Todo       guisp=NONE guifg=#569dd6 guibg=#000000 ctermfg=74  ctermbg=16 gui=NONE cterm=NONE

" minor

hi String         guisp=NONE guifg=#CE9278 guibg=#000000 ctermfg=174 ctermbg=16 gui=NONE cterm=NONE
hi Character      guisp=NONE guifg=#569dd6 guibg=#000000 ctermfg=74  ctermbg=16 gui=NONE cterm=NONE
hi Number         guisp=NONE guifg=#B5CEA9 guibg=#000000 ctermfg=151 ctermbg=16 gui=NONE cterm=NONE
hi Boolean        guisp=NONE guifg=#569dd6 guibg=#000000 ctermfg=74  ctermbg=16 gui=NONE cterm=NONE
hi Float          guisp=NONE guifg=#B5CEA9 guibg=#000000 ctermfg=151 ctermbg=16 gui=NONE cterm=NONE
hi Function       guisp=NONE guifg=#DCDCAA guibg=#000000 ctermfg=187 ctermbg=16 gui=NONE cterm=NONE
hi Conditional    guisp=NONE guifg=#C586C0 guibg=#000000 ctermfg=175 ctermbg=16 gui=NONE cterm=NONE
hi Repeat         guisp=NONE guifg=#569dd6 guibg=#000000 ctermfg=74  ctermbg=16 gui=NONE cterm=NONE
hi Label          guisp=NONE guifg=#4FCAB0 guibg=#000000 ctermfg=79  ctermbg=16 gui=NONE cterm=NONE
hi Operator       guisp=NONE guifg=#569dd6 guibg=#000000 ctermfg=74  ctermbg=16 gui=NONE cterm=NONE
hi Keyword        guisp=NONE guifg=#569dd6 guibg=#000000 ctermfg=74  ctermbg=16 gui=NONE cterm=NONE
hi Exception      guisp=NONE guifg=#569dd6 guibg=#000000 ctermfg=74  ctermbg=16 gui=NONE cterm=NONE
hi Include        guisp=NONE guifg=#4FCAB0 guibg=#000000 ctermfg=79  ctermbg=16 gui=NONE cterm=NONE
hi Define         guisp=NONE guifg=#4FCAB0 guibg=#000000 ctermfg=79  ctermbg=16 gui=NONE cterm=NONE
hi Macro          guisp=NONE guifg=#4FCAB0 guibg=#000000 ctermfg=79  ctermbg=16 gui=NONE cterm=NONE
hi PreCondit      guisp=NONE guifg=#4FCAB0 guibg=#000000 ctermfg=79  ctermbg=16 gui=NONE cterm=NONE
hi StorageClass   guisp=NONE guifg=#4FCAB0 guibg=#000000 ctermfg=79  ctermbg=16 gui=NONE cterm=NONE
hi Structure      guisp=NONE guifg=#4FCAB0 guibg=#000000 ctermfg=79  ctermbg=16 gui=NONE cterm=NONE
hi Typedef        guisp=NONE guifg=#4FCAB0 guibg=#000000 ctermfg=79  ctermbg=16 gui=NONE cterm=NONE
hi SpecialChar    guisp=NONE guifg=#6A9956 guibg=#000000 ctermfg=65  ctermbg=16 gui=NONE cterm=NONE
hi Tag            guisp=NONE guifg=#6A9956 guibg=#000000 ctermfg=65  ctermbg=16 gui=NONE cterm=NONE
hi Delimiter      guisp=NONE guifg=#C586C0 guibg=#000000 ctermfg=175 ctermbg=16 gui=NONE cterm=NONE
hi SpecialComment guisp=NONE guifg=#6A9956 guibg=#000000 ctermfg=65  ctermbg=16 gui=NONE cterm=NONE
hi Debug          guisp=NONE guifg=#6A9956 guibg=#000000 ctermfg=65  ctermbg=16 gui=NONE cterm=NONE
