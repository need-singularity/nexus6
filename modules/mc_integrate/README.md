# nexus.modules.mc_integrate

ANU-seeded Monte Carlo integrator
(source: `~/core/n6-architecture/experiments/anu_mc_verification/anu_mc_verify.hexa`).

LCG = Numerical Recipes:  `s = (1664525 * s + 1013904223) mod 2^31`.
Acceptance gates (verbatim): `PASS` if `|MC - analytical| < 1e-3`;
`NEAR` if `< 1e-2`; else `FAIL`.

## API

```python
from nexus.modules.mc_integrate import (
    estimate, estimate_constant, compare_rng,
)

r = estimate(lambda x: 2.0 * x[0], dim=1, n_samples=10_000,
             rng='urandom', analytical=1.0)
# {value, abs_err, rel_err, runtime_s, gate, samples, rng_used}

r = estimate_constant('catalan', n_samples=1_000_000, rng='anu')
# adds {name, analytical}

cmp = compare_rng(integrand, dim=1, n_samples=10000, n_trials=6)
# {anu_mean, anu_std, urandom_mean, urandom_std, t_stat, indistinguishable}
```

Named constants: `catalan`, `zeta3`, `euler_gamma`, `pi5_times_n6`.

ANU bootstrap: shells out to `~/core/nexus/sim_bridge/godel_q/anu_source.hexa`;
falls back to `os.urandom(16)` then to a deterministic seed.

## CLI

```sh
python -m nexus.modules.mc_integrate.cli --constant catalan --N 100000 --rng anu
python -m nexus.modules.mc_integrate.cli --compare zeta3 --N 50000 --trials 6
```

## Self-test

```sh
python -m nexus.modules.mc_integrate.mc_integrate --self-test
```

Prints `__MC_INTEGRATE__ PASS` on success.
