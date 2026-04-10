# n6-replication

Independent replication package for the perfect-number-6 mathematics in [TECS-L](https://github.com/need-singularity/TECS-L).

Covers 1,700+ hypotheses across pure mathematics, physics mappings, and consciousness models.

## Quick Reproduction

### Option 1: Docker (recommended)

```bash
docker build -t n6-replication .
docker run n6-replication
```

### Option 2: Local (tier 1, no install)

```bash
pip install -r requirements.txt
pytest tests/tier1/ -v
```

### Option 3: Single command

```bash
bash run-tests.sh
```

> `run-tests.sh` runs tier 1 (pure-math identities, no package install required).
> Docker runs all tests including package-level tests.

## Quick Start

### 1. Reviewers (Docker, zero setup)

```bash
git clone https://github.com/need-singularity/TECS-L.git
cd TECS-L
docker build -f n6-replication/Dockerfile -t n6-replicate .
docker run --rm n6-replicate                       # Tier 1
docker run --rm n6-replicate run --tier 1 2        # Tier 1 + 2
```

### 2. Developers (pip install)

```bash
pip install ./n6-replication
n6-replicate run --tier 1          # Pure-math identities (~30s)
n6-replicate run --tier 1 2        # All tiers
n6-replicate report --format html  # Generate HTML report
```

### 3. Researchers (editable install)

```bash
git clone https://github.com/need-singularity/TECS-L.git
cd TECS-L
pip install -e ./n6-replication
pytest n6-replication/tests/tier1/ -v   # Run tests directly
```

### 4. Minimal (no install)

```bash
git clone https://github.com/need-singularity/TECS-L.git
cd TECS-L
pip install numpy scipy sympy mpmath pytest
python3 n6-replication/scripts/run_all.py --tier 1
```

## Verification Tiers

| Tier | Content | Scripts | Time |
|------|---------|---------|------|
| 1 | Pure-math identities (8 core discoveries) | `tests/tier1/test_*.py` | ~30s |
| 2 | Full verification suite (90 scripts) | `verify/*.py`, `frontier_*.py` | ~10min |
| 3 | GPU experiments (MoE, training) | `engines/*.py` | Hours, GPU required |

## Tier 1 Tests (8 Core Discoveries)

| Test | Hypothesis | What it checks |
|------|-----------|----------------|
| `test_perfect_six` | H090 | sigma_{-1}(6) = 2, Euler product |
| `test_golden_zone` | H067 | Zone boundaries: 1/2, 1/e, ln(4/3) |
| `test_conservation` | H172 | G*I = D*P conservation law |
| `test_euler_product` | H092 | zeta Euler product p=2,3 truncation |
| `test_uniqueness` | H098 | 6 is only perfect number with reciprocal sum = 1 |
| `test_edge_of_chaos` | H139 | Golden Zone = Langton lambda_c ~ 0.27 |
| `test_phase_accel` | H124 | Phase acceleration stepwise x3 |
| `test_texas` | H000 | Texas Sharpshooter p < 0.001 |

## CLI Reference

```
n6-replicate run [--tier 1 2] [--timeout 120]   Run verification tiers
n6-replicate fetch                                Download external data
n6-replicate report [--format html|json|text]     Generate result report
n6-replicate list                                 List available tests
```

### run_all.py (no install)

```
python3 n6-replication/scripts/run_all.py --tier 1       # Tier 1 only
python3 n6-replication/scripts/run_all.py --tier 2       # Tier 2 only
python3 n6-replication/scripts/run_all.py --timeout 60   # Custom timeout
```

## GPU Experiments (Tier 3)

Tier 3 requires a GPU and the `gpu` extra:

```bash
pip install "./n6-replication[gpu]"
```

Key experiments:
- **Golden MoE**: MNIST 97.7%, CIFAR 53.0% (vs Top-K 97.1%, 48.2%)
- **Inhibition convergence**: I -> 1/3 meta fixed point
- **Conscious LM**: Savant index measurement

## Reports

After running, generate a report:

```bash
n6-replicate report --format html -o results.html
```

Reports include pass/fail counts, per-test timing, and links to hypothesis documents.

## Project Structure

```
n6-replication/
  pyproject.toml        # Package metadata + dependencies
  Dockerfile            # One-command Docker replication
  README.md             # This file
  src/n6_replication/   # CLI, runner, reporter, fetcher, parser, registry
  tests/tier1/          # 8 pure-math pytest tests
  scripts/run_all.py    # Minimal entrypoint (no install needed)
  registry/             # Test registry (tier2.json etc.)
  templates/            # HTML report templates
  results/              # Generated reports (gitignored)
```

## License

MIT
