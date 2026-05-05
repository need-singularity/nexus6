# multiverse_nav

Bostrom branch-probability simulator over sigma^2=144 Everett branches.
Stdlib + optional `hexa` shell-out for ANU QRNG seeding.

## Import example

```python
from modules.multiverse_nav import simulate

out = simulate(n_trials=2000, seed_source="urandom",
               branching_rule="uniform")
print(out["branch_id_chosen"], out["trilemma_term"],
      out["chi2_pvalue"], out["falsifier_status"])
```

## Sample run

```
$ python multiverse_nav.py --n_trials 2000
{
  "anu_seed_hex": null,
  "branch_id_chosen": 73,
  "branching_rule": "uniform",
  "chi2_pvalue": 0.41,
  "chi2_uniform": 144.7,
  "empirical_dist": {"top_42": 0.012, ...},
  "falsifier_status": "PASS:uniform",
  "n_trials": 2000,
  "seed_source_effective": "urandom",
  "trilemma_term": "P2"
}
```

## ANU bridge

`seed_source="anu"` shells out to
`/Users/ghost/core/nexus/sim_bridge/godel_q/anu_source.hexa` via the `hexa`
CLI.  On any failure the simulator silently falls back to `os.urandom` and
sets `anu_seed_hex: None`, `seed_source_effective: "urandom-fallback"`.

## Self-test

```
$ python multiverse_nav.py --self-test
... __MULTIVERSE_NAV__ PASS
```

## Falsifiers

- chi^2 vs uniform-over-144 null at p<0.001 -> `falsifier_status: FAIL:bias-detected`
- branch_id outside [0, 144) -> impossible by construction (rejection sampling)
- n_trials < 1, unknown seed_source / branching_rule -> ValueError
- ANU bridge unreachable -> graceful urandom fallback (anu_seed_hex None)

## Reference

n=6 closure per `domains/physics/multiverse-nav/multiverse-nav.md` MULT-01..06.
