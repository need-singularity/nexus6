# n6-replication: Independent Replication Package

**Date:** 2026-03-28
**Status:** Approved
**Goal:** Anyone can verify TECS-L discoveries with minimal effort

---

## 1. Overview

Independent replication package for the TECS-L project's 1,700+ hypotheses across 7 repositories. Three tiers of verification, three output formats, three installation methods.

### Target Users (layered)

| User | Need | Path |
|------|------|------|
| Reviewer/Examiner | "Does it reproduce?" — minimum effort | `docker run n6-replication` |
| Developer | `pip install` + one command | `pip install n6-replication && n6-replicate run` |
| Researcher | Deep dive, modify, explore | `pip install -e ./n6-replication` + pytest |

### Key Decisions

| Item | Decision |
|------|----------|
| Name | n6-replication |
| Scope | 7 repos (Tier 1/2/3) |
| Tier 1 | pytest native, 8 Major Discoveries |
| Tier 2 | subprocess wrapper, verify/ 90 scripts |
| Tier 3 | `n6-replicate fetch` for 6 external repos |
| GPU | `[gpu]` extras, skip without torch |
| Reports | terminal + md + html |
| Distribution | pip (PyPI) + Docker |
| CLI | argparse-based `n6-replicate` command + `python -m n6_replication` |
| Repo integration | Hybrid (Tier 1+2 embedded, Tier 3 on-demand fetch) |

---

## 2. Package Structure

```
n6-replication/                    # New directory at TECS-L root
├── pyproject.toml                 # pip install + CLI entrypoint
├── Dockerfile                     # docker run n6-replication
├── README.md                      # Install/run guide (per user type)
├── src/n6_replication/
│   ├── __init__.py                # Version, constants
│   ├── __main__.py                # python -m n6_replication support
│   ├── cli.py                     # `n6-replicate` CLI (argparse)
│   ├── runner.py                  # Script execution engine
│   ├── parser.py                  # Output parsing (emoji/pass/fail extraction)
│   ├── reporter.py                # Terminal/md/html report generation
│   ├── fetcher.py                 # Tier 3 repo auto-clone
│   └── registry.py                # Script metadata + discovery
├── registry/
│   ├── tier2.json                 # 90 verify/ scripts metadata
│   └── tier3.json                 # Auto-generated after fetch
├── tests/
│   └── tier1/
│       ├── conftest.py            # Tolerance fixtures
│       ├── test_golden_zone.py    # H067: 1/2+1/3+1/6=1, 1/e center
│       ├── test_perfect_six.py    # H090: sigma_{-1}(6)=2, master formula
│       ├── test_uniqueness.py     # H098: 6 is unique perfect number with reciprocal sum=1
│       ├── test_euler_product.py  # H092: zeta Euler product p=2,3 truncation
│       ├── test_conservation.py   # H172: G*I=D*P conservation law
│       ├── test_phase_accel.py    # H124: Phase acceleration stepwise x3
│       ├── test_edge_of_chaos.py  # H139: Golden Zone = Langton lambda_c
│       └── test_texas.py          # Texas Sharpshooter p<0.0001
├── templates/
│   └── report.html                # Jinja2 HTML report template
└── scripts/
    └── run_all.py                 # Minimal entrypoint: python run_all.py (argparse, no click dependency)
```

---

## 3. CLI Interface

```bash
# Core commands
n6-replicate run                          # Run Tier 1+2
n6-replicate run --tier 1                 # Core only (~5min)
n6-replicate run --tier 2                 # verify/ full (~30min)
n6-replicate run --tier 3                 # Cross-repo (requires fetch)
n6-replicate run --parallel 4             # Parallel execution

# Tier 3 management
n6-replicate fetch                        # Clone 6 repos to ~/.n6-replication/repos/
n6-replicate fetch --update               # Pull latest

# Reports
n6-replicate report                       # Terminal summary of last run
n6-replicate report --format md           # Generate results/report.md
n6-replicate report --format html         # Generate results/report.html

# Discovery
n6-replicate list                         # List all registered scripts
n6-replicate list --tier 1                # List by tier

# Also works as module
python -m n6_replication run --tier 1
```

---

## 4. Execution Engine (runner.py)

### Tier 1: pytest native

- Runs `pytest.main()` on `tests/tier1/`
- Each test directly asserts mathematical identities
- No external script dependency
- JSON result via pytest-json-report or custom plugin

### Tier 2+3: subprocess wrapper

- Reads script list from `registry/*.json`
- For each script:
  1. Set `PYTHONPATH` to repo root
  2. `subprocess.run()` with timeout (default 120s)
  3. Capture stdout/stderr
  4. Parse output via `parser.py`
  5. Record result to JSON
- Fail-continue: one script failure does not stop others
- GPU scripts: check `torch` importable, skip with message if not

### Parallel execution

- `--parallel N` flag, default = `cpu_count() // 2`
- `concurrent.futures.ProcessPoolExecutor`
- Scripts sharing root modules (compass, convergence_engine) run serially to avoid import conflicts
- Independent scripts run in parallel

### Result persistence

- Each run: `results/YYYY-MM-DD-HHMMSS.json`
- Schema per script:
  ```json
  {
    "id": "verify_math",
    "tier": 2,
    "repo": "TECS-L",
    "status": "pass|fail|skip|error|parse_error",
    "grade_counts": {"green": 12, "orange": 3, "white": 0, "black": 0},
    "p_value": 0.0001,
    "duration_seconds": 14.2,
    "stdout_snippet": "first 500 chars...",
    "error": null
  }
  ```

---

## 5. Parser (parser.py)

Extracts from stdout:

| Pattern | Regex | Meaning |
|---------|-------|---------|
| Pass | `✅\|Pass\|PASS\|pass` | Individual check passed |
| Fail | `❌\|Fail\|FAIL\|fail` | Individual check failed |
| Grade green | `🟩` | Proven/exact |
| Grade orange | `🟧` | Structural (p<0.05) |
| Grade white | `⚪` | Coincidence |
| Grade black | `⬛` | Refuted |
| Grade star | `⭐\|★` | Major discovery |
| p-value | `p[=: ]+([0-9.e-]+)` | Statistical significance |

Fallback: if no patterns found, use exit code (0=pass, nonzero=fail).

---

## 6. Reporter (reporter.py)

### Terminal (default)

```
══════════════════════════════════════════
  n6-replication Results  v0.1.0
══════════════════════════════════════════
Tier 1 (Core)      8/8   ████████████████████ 100%
Tier 2 (Full)     84/90  ████████████████░░░░  93%
Tier 3 (Cross)    --     (not fetched)

Grade Distribution:
  🟩 Proven       54   ██████████████████
  🟧 Structural   28   █████████
  ⚪ Coincidence    6   ██
  ⬛ Refuted        2   █

Failed Scripts (6):
  ❌ verify_ai.py          — torch not installed (skipped)
  ❌ verify_h481.py        — timeout (120s)
  ...

Total: 1,247 checks | Duration: 24m 31s
══════════════════════════════════════════
```

### Markdown (--format md)

- `results/report.md`
- Tier sections with script-level pass/fail table
- Failed scripts include error snippet
- Grade distribution table
- Copy-paste ready for GitHub issues/PRs

### HTML (--format html)

- Jinja2 template from `templates/report.html`
- Filter by tier, grade, status
- Collapsible detail (click to expand stdout)
- Style: similar to math_atlas.html
- Self-contained single file (CSS/JS inline)

---

## 7. Fetcher (fetcher.py)

### Repo registry

```python
REPOS = {
    "SEDI":              "https://github.com/need-singularity/sedi.git",
    "anima":             "https://github.com/need-singularity/anima.git",
    "ph-training":       "https://github.com/need-singularity/ph-training.git",
    "golden-moe":        "https://github.com/need-singularity/golden-moe.git",
    "conscious-lm":      "https://github.com/need-singularity/conscious-lm.git",
    "energy-efficiency": "https://github.com/need-singularity/energy-efficiency.git",
}
```

### Behavior

- `n6-replicate fetch`:
  - Clone to `~/.n6-replication/repos/{name}/` (shallow, `--depth 1`)
  - Scan each repo's `verify/` directory
  - Auto-generate `registry/tier3.json`
  - Print status: fetched/failed per repo

- `n6-replicate fetch --update`:
  - `git pull` on existing clones
  - Re-scan and update registry

- Status tracking:
  - `~/.n6-replication/fetch_state.json`: repo → {status, last_fetched, commit_hash}

---

## 8. Registry (registry.py)

### Schema (per script)

```json
{
    "id": "verify_math",
    "tier": 2,
    "path": "verify/verify_math.py",
    "repo": "TECS-L",
    "requires_gpu": false,
    "depends_on": ["compass.py", "convergence_engine.py"],
    "timeout": 120,
    "expected_grades": {"green": 12, "orange": 3}
}
```

### Discovery

- Tier 1: pytest auto-discovery from `tests/tier1/`
- Tier 2: static `registry/tier2.json` (90 scripts, manually curated)
- Tier 3: dynamic scan after `fetch` → `registry/tier3.json` auto-generated

### `n6-replicate list` output

```
Tier  ID                        Repo     GPU   Timeout
──────────────────────────────────────────────────────
  1   test_golden_zone          TECS-L   -     30s
  1   test_perfect_six          TECS-L   -     30s
  2   verify_math               TECS-L   -     120s
  2   verify_ai                 TECS-L   GPU   300s
  3   verify_cern_combined      SEDI     -     120s
```

---

## 9. Distribution

### pyproject.toml

```toml
[project]
name = "n6-replication"
version = "0.1.0"
description = "Independent replication package for perfect number 6 mathematics"
requires-python = ">=3.9"
license = {text = "MIT"}
authors = [{name = "Park, Min Woo"}]
dependencies = [
    "numpy>=1.21",
    "scipy>=1.7",
    "sympy>=1.9",
    "mpmath>=1.2",
    "jinja2>=3.0",
]

[project.optional-dependencies]
gpu = ["torch>=2.0", "torchvision>=0.15"]

[project.scripts]
n6-replicate = "n6_replication.cli:main"

[build-system]
requires = ["setuptools>=64"]
build-backend = "setuptools.backends._legacy:_Backend"
```

### Dockerfile

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . /app/TECS-L
RUN pip install --no-cache-dir /app/TECS-L/n6-replication
RUN cd /app/TECS-L && n6-replicate fetch || true
ENTRYPOINT ["n6-replicate"]
CMD ["run", "--tier", "1"]
```

### Installation methods

```bash
# A) Minimal — run_all.py
git clone https://github.com/need-singularity/TECS-L.git
cd TECS-L
pip install numpy scipy sympy mpmath
python n6-replication/scripts/run_all.py

# B) pip
pip install n6-replication
n6-replicate run --tier 1

# C) Docker
docker run ghcr.io/need-singularity/n6-replication
docker run ghcr.io/need-singularity/n6-replication run --tier 2
```

---

## 10. Implementation Priority

| Phase | Content | Estimated Files |
|-------|---------|----------------|
| Phase 1 | pyproject.toml + cli.py + runner.py (Tier 1 only) + tests/tier1/ | 12 files |
| Phase 2 | parser.py + registry + tier2.json (Tier 2) | 4 files |
| Phase 3 | reporter.py (terminal + md + html) + templates/ | 3 files |
| Phase 4 | fetcher.py + Tier 3 integration | 2 files |
| Phase 5 | Dockerfile + README.md + run_all.py | 3 files |
| Phase 6 | PyPI publish + Docker image push | config only |

Total: ~24 files, 6 phases.
