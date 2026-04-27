# tabletop_blackhole

BEC analog Hawking-temperature simulator (Steinhauer 2014). Stdlib only.
n=6 anchors locked: B_trap=48T, L_h=10um, c_s=48mm/s, T_H=0.5nK.

## Import example

```python
from modules.tabletop_blackhole import simulate, n6_anchors

print(n6_anchors()["T_H_nK"])  # 0.5
out = simulate(N_atoms=4.8e7, B_trap=48.0, c_sound_mm_s=48.0,
               v_flow_mm_s=96.0, L_horizon_um=10.0, T_BEC_nK=4.1667)
print(out["T_H_nK"], out["falsifier_status"])
```

## Sample run

```
$ python tabletop_blackhole.py
{
  "T_H_nK": 0.5,
  "falsifier_status": "PASS:n6-locked",
  "lifetime_consistent": true,
  "n_phonon_modes": 4,
  "tau_BH_ms": 20.0
}
```

## Self-test

```
$ python tabletop_blackhole.py --self-test
... __TABLETOP_BLACKHOLE__ PASS
```

## Falsifiers

- B_trap != sigma*tau (48 T) -> OFFLOCK flagged
- L_horizon != sigma-phi (10 um) -> OFFLOCK flagged
- c_sound != sigma*tau (48 mm/s) -> OFFLOCK flagged
- T_H != sigma/(tau*n) (0.5 nK) -> OFFLOCK flagged
- N_atoms <= 0 or L_horizon <= 0 -> ValueError
- lifetime_consistent flips False if T_H * n_modes contradicts tau_BH

## Reference

n=6 closure per `domains/physics/tabletop-blackhole/tabletop-blackhole.md`
TBHL-01..08.
