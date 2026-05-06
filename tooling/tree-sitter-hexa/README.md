# tree-sitter-hexa

Seed tree-sitter grammar for the **hexa-lang** DSL used inside `nexus`
(`n6/*.hexa`, `mk2_hexa/**/*.hexa`).

The goal is **structural recognition without an LSP** — syntax
highlighting, symbol jumping, and AST queries in every editor that speaks
tree-sitter (Neovim, Helix, Zed, VS Code via `vscode-tree-sitter`) plus AI
agents that introspect the AST.

Coverage target: ~70-80% of patterns observed in production hexa code.

## What is recognised

- Module-level `let` / `fn` declarations and CLI entry blocks.
- Block statements: `let`, `return`, `if`/`else`, `while`, `for`,
  `try`/`catch`, assignment, expression-statement.
- Expressions: identifiers, integer/float/string/bool/array literals,
  calls, member access, index, unary/binary operators, parenthesised.
- Type annotations: `i64` `i32` `u64` `u32` `f64` `f32` `string` `bool`,
  array types `[T]`, named types.
- Line comments + lint annotation comments
  (`// @allow-bare-exec`, `// @allow-silent-catch`,
  `// @allow-silent-exit`) which receive a dedicated `@comment.note`
  capture.

## What is **not** recognised (out of scope for the seed)

- Generics / type parameters
- Macros
- Complex pattern matching (only flat `if`/`else` chains)
- Trait/impl blocks
- The `>=` / `<=` lint rule (project convention forbids them; the grammar
  still accepts them so external snippets do not red-line — the
  `nexus check` lint enforces the rule)

## Files

```
tooling/tree-sitter-hexa/
├── grammar.js              # tree-sitter grammar (~270 LOC)
├── package.json
├── README.md               # this file
├── queries/
│   ├── highlights.scm      # editor syntax highlighting
│   ├── locals.scm          # scope/definition resolution
│   └── tags.scm            # ctags-style symbol index
└── test/corpus/
    └── basic.txt           # 9 round-trip parser tests
```

## Build

```sh
# 1. install the tree-sitter CLI (one-time, user-local)
npm install -g tree-sitter-cli         # or:  brew install tree-sitter

# 2. install dev deps + generate the C parser
cd tooling/tree-sitter-hexa
npm install
npx tree-sitter generate

# 3. run the test corpus
npx tree-sitter test
```

`tree-sitter generate` emits `src/parser.c` (and on first invocation
`src/grammar.json`, `src/node-types.json`). These files are **not**
checked in — regenerate them locally.

## Use

### Neovim (nvim-treesitter)

```lua
local parsers = require('nvim-treesitter.parsers').get_parser_configs()
parsers.hexa = {
  install_info = {
    url      = '/Users/ghost/core/nexus/tooling/tree-sitter-hexa', -- or git URL
    files    = { 'src/parser.c' },
    branch   = 'main',
    generate = true,
  },
  filetype = 'hexa',
}
vim.filetype.add({ extension = { hexa = 'hexa' } })
-- :TSInstall hexa
```

### Helix

Add to `~/.config/helix/languages.toml`:

```toml
[[language]]
name = "hexa"
scope = "source.hexa"
file-types = ["hexa"]
roots = []
comment-token = "//"

[[grammar]]
name = "hexa"
source = { path = "/Users/ghost/core/nexus/tooling/tree-sitter-hexa" }
```

Then `hx --grammar fetch && hx --grammar build`.

### Zed

Drop the directory into a Zed extension that registers a
`languages/hexa/config.toml` pointing at this grammar.

### VS Code

Use any of the `vscode-tree-sitter`-style extensions and point the
grammar path at this directory; the queries in `queries/` provide the
highlighting captures.

## Validating without the CLI

If you cannot install the tree-sitter CLI you can still review the seed:

- `grammar.js` is plain CommonJS; `node -e "require('./grammar.js')"`
  loads it successfully iff the rule shape is syntactically valid.
- `queries/*.scm` are S-expressions; any tree-sitter-aware editor will
  reject malformed captures on load.

## Status

Seed (v0.1.0). Iterate as new hexa idioms appear in `n6/` and
`mk2_hexa/`. Report mis-parses by adding a failing case to
`test/corpus/basic.txt` and extending `grammar.js` minimally.
