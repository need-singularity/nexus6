# n6_honesty

Python port of the 5-precondition **honesty triad linter** for n6 atlas
shards, paper files, and code. Read-only; never modifies shards or atlas
state.

SSOT: `~/core/canon/scripts/quality/honesty_triad_linter.hexa`
(see `state/crosscutting_module_proposals_2026-04-27.md` §D).

## Preconditions

| Code | Check                                                                |
|------|----------------------------------------------------------------------|
| C1   | First 30 lines contain a project banner (atlas/shard/ω-cycle)        |
| C2   | File does NOT pair a destructive verb with a protected path on one line |
| C3   | At least one falsifier marker (`falsifier`, `F[0-9]+:`, `F-MOLT`, `OBSTRUCTION`, ...) |
| C4   | At least one citation pointer (`\|>`, `:line`, `see file:line`)      |
| C5   | At least one canonical verdict token (`[10*]`, `[7]`, `PASS`, `FAIL`, `NEAR`, ...) |

Verdict aggregation:

- 5 PASS → `PASS`
- 4 PASS → `WARN`
- ≤3 PASS → `FAIL`
- single line in first 100 lines matching `lint-exempt: <reason>` → `EXEMPT`

## Library API

```python
from n6_honesty import (
    HonestyResult, HonestyLinter,
    lint_file, lint_dir, lint_atlas_shards,
    report_summary, report_json,
)

r = lint_file("/path/to/atlas.append.foo.n6")
print(r.overall, r.pass_count, r.reasons)

results = lint_dir("/Users/ghost/core/nexus/n6", glob="atlas.append.*.n6")
print(report_summary(results))

summary = lint_atlas_shards()
# {'results': [...], 'counts': {'PASS': N, 'WARN': N, 'FAIL': N, 'EXEMPT': N},
#  'total': 112}
```

`HonestyLinter` constants are class-level and overridable per instance:

```python
linter = HonestyLinter(VERDICT_PATTERNS=[r"\bDONE\b", r"\bSHIP\b"])
linter.lint_file("...")
```

Overridable constants:

- `BANNER_PATTERNS`, `BANNER_HEAD_LINES`
- `WRITE_VERBS`, `PROTECTED_PATHS`
- `FALSIFIER_PATTERNS`
- `CITATION_PATTERNS`
- `VERDICT_PATTERNS`
- `EXEMPT_PATTERN`, `EXEMPT_HEAD_LINES`

## CLI

```sh
# Lint a single file
python -m n6_honesty.cli /Users/ghost/core/nexus/n6/atlas.append.foo.n6

# Lint a directory
python -m n6_honesty.cli /Users/ghost/core/nexus/n6 --glob 'atlas.append.*.n6'

# JSONL output (one HonestyResult per line)
python -m n6_honesty.cli /path/to/dir --json

# Self-test + live diagnostic against nexus shards
python -m n6_honesty.cli --self-test
```

Exit codes:

- `0` — all targets `PASS`/`WARN`/`EXEMPT`
- `1` — at least one `FAIL`
- `2` — bad invocation / no targets matched

## Adding new files to the lint

The linter has no static allowlist — any path can be linted. Two ways to
include new files:

1. **Pass them on the CLI**: `python -m n6_honesty.cli <new_file>`.
2. **Add a directory glob**: `python -m n6_honesty.cli <dir> --glob '*.n6'`.

To suppress (e.g. for non-shard scratch files), put a single line in the
first 100 lines:

```
// lint-exempt: scratch fixture, not an atlas shard
```

The result reports `EXEMPT` with the reason, and per-precondition booleans
are still populated for transparency.

## Tests

```sh
cd /Users/ghost/core/nexus/lib
python -m unittest n6_honesty.tests.test_honesty_triad -v
```

## Hard rules

- Stdlib only (`re`, `pathlib`, `json`, `unittest`, `dataclasses`).
- Reporting only — no auto-fix, no shard edits.
- Mirror of the SSOT linter — divergences should be documented here.
