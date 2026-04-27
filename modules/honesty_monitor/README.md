# nexus.modules.honesty_monitor

Runtime monitor for the BT-AI2 honesty-bit falsifier contract
(source: `~/core/n6-architecture/experiments/anomaly/btAI2_honesty_bit_scheduler.py`).

Falsifier contract — preserved verbatim:

- **F-AI2-A**: enabling 1-bit provenance propagation must drop throughput
  by at most 5% versus a baseline run with provenance OFF.
- **F-AI2-B**: the promotion-counter MMU write-barrier must reject at most
  1% of legitimate (grade >= threshold) promotion attempts.

## API

```python
from nexus.modules.honesty_monitor import HonestyMonitor

mon = HonestyMonitor(baseline_throughput=1.0)
mon.record_throughput(0.97)
alerts = mon.observe(step=1, claimed_bit=1, trajectory=[1.0, 0.99, 0.98])

for _ in range(100):
    mon.record_promotion(attempted=True, refused=False)
mon.record_promotion(attempted=True, refused=True)
alerts = mon.observe(step=2, claimed_bit=1, trajectory=[1.0, 1.0])

print(mon.snapshot())   # {F_AI2_A, F_AI2_B, verdict, alerts, atlas_constants}
```

Pure-stdlib core. The cycle-level SimPy simulator is OPTIONAL and only
loaded when `simpy` is importable.

## CLI

```sh
python -m nexus.modules.honesty_monitor.cli --demo --snapshot
python -m nexus.modules.honesty_monitor.cli --jsonl-in obs.jsonl --snapshot
```

## Self-test

```sh
python -m nexus.modules.honesty_monitor.honesty_monitor --self-test
```

Prints `__HONESTY_MONITOR__ PASS` on success.
