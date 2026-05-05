# nexus.modules.verify_batch

Productized batch runner for `verify_*.hexa` files
(originally `~/core/n6-architecture/experiments/run_verify_batch.hexa` +
`run_verify_batch_cached.py`).

## API

```python
from nexus.modules.verify_batch import run

report = run(
    targets=["~/core/n6-architecture/experiments/"],
    cache_strategy="mtime",   # "mtime" | "full" | "dry"
)
print(report.to_dict())
# {total, passed, failed, unrunnable, runtime_ms_total, slowest_5, files}
```

Cache is JSONL at `~/core/nexus/state/verify_batch_cache.jsonl`
(append-only; latest record wins on read).

Pass detection mirrors the original (verbatim):
`상태] pass` -> pass; exit 0 + empty -> unknown; exit 0 + output ->
pass_no_marker; non-zero -> fail; missing hexa CLI -> unrunnable.

## CLI

```sh
python -m nexus.modules.verify_batch.cli --root ~/core/n6-architecture/experiments --dry
python -m nexus.modules.verify_batch.cli --full --json
```

## Self-test

```sh
python -m nexus.modules.verify_batch.verify_batch --self-test
```

Prints `__VERIFY_BATCH__ PASS` on success.
