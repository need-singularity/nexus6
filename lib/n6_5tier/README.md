# n6.5tier_template

Generator + validator for the **L0-L4 / sigma-tau-phi-sopfr** pattern that
threads through n=6-architecture domain `.md` files (~137 candidates).

The convention every domain file follows:

| tier | anchor | n=6 value |
|------|--------|-----------|
| L0 base   | n=6 DOF        | n = 6 |
| L1 core   | sigma=12 ch    | sigma(6) = 12 |
| L2 ctrl   | tau=4 red      | tau(6) = 4 |
| L3 integ  | phi=2 sym      | phi(6) = 2 |
| L4 apply  | sopfr=5 protect| sopfr(6) = 5 |

Plus 7 mandatory sections (§1 WHY, §2 COMPARE, §3 REQUIRES, §4 STRUCT,
§5 FLOW, §6 EVOLVE, §7 VERIFY) and a stdlib-only Python check block in §7
that defines `sigma(n)`, `tau(n)`, `sopfr(n)` and asserts the perfect-number
identity `sigma(n) == 2 * n` at n=6.

## Quick start

```bash
# generate a new domain skeleton (prints to stdout)
python -m n6_5tier.cli generate \
    --name "Quantum Foo" --slug quantum-foo \
    --summary "Quantum Foo - n=6 derived design." \
    --requires cosmology --requires quantum-computer

# write to a folder
python -m n6_5tier.cli generate \
    --name "Quantum Foo" --slug quantum-foo \
    --out ./out_demo

# validate an existing domain .md
python -m n6_5tier.cli validate \
    ~/core/n6-architecture/domains/physics/cosmology/cosmology.md

# walk a tree
python -m n6_5tier.cli validate-dir \
    ~/core/n6-architecture/domains/

# run module self-test
python -m n6_5tier.cli --self-test
```

## Python API

```python
from n6_5tier import generate, validate, validate_dir

text = generate({
    "name": "Quantum Foo",
    "slug": "quantum-foo",
    "one_line_summary": "Quantum Foo — n=6 derived.",
    "l0_dof_basis": "SE(3) 6-DOF",
    "l1_channel_basis": "12 RF channels",
    "l2_redundancy_basis": "tau=4 quad redundancy",
    "l3_symmetry_basis": "phi=2 bilateral",
    "l4_protection_basis": "sopfr=5 shielding tiers",
})

result = validate("/path/to/domain.md")
print(result.grade, result.n6_anchor_count, result.sections_missing)
```

## Validator grading

- **PASS** — all 7 mandatory sections present, L0-L4 table in §4, canonical
  Python check (sigma+tau+sopfr defs and the perfect-number assert),
  ≥5 explicit `sigma`/`tau`/`phi`/`sopfr` references, falsifier list mentioned.
- **WARN** — 1 mandatory section missing OR Python check incomplete OR
  falsifier list missing OR <5 anchor references.
- **FAIL** — ≥2 mandatory sections missing, or no L0-L4 table, or <3
  anchor references.

## Tests

```bash
cd /Users/ghost/core/nexus/lib
python -m unittest n6_5tier.tests.test_template -v
```

## Files

- `template.py` — `generate(spec) -> str`
- `validator.py` — `validate(md_path) -> ValidationResult`, `validate_dir(root)`
- `cli.py` — CLI front-end + `--self-test`
- `data/section_skeletons.json` — tier definitions and section ordering as data
- `data/exemplar_cosmology.md` — read-only fixture (canonical exemplar)
- `tests/test_template.py` — round-trip + corruption + exemplar tests

## Hard guarantees

- Stdlib only.
- Validator is read-only — never modifies any domain file or atlas.
- Generator never writes unless `--out` is supplied.
