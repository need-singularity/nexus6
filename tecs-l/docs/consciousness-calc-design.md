# Design: consciousness_calc.py — Consciousness Continuity Calculator

**Date**: 2026-03-23
**Status**: Pending Approval

---

## Goals

A single Python tool combining a Lorenz attractor-based simulator + CCT (Consciousness Continuity Test) evaluator. Mathematically calculates and evaluates consciousness continuity conditions of systems.

## Non-Goals

- GUI / Web interface
- Real-time streaming (batch simulation only)
- Quantum simulation (Phase 0, classical only)

---

## Architecture

```
consciousness_calc.py (single file, following existing tool pattern)
│
├── Simulator (Lorenz attractor based)
│   └── Generate system state trajectory → S(t) time series
│
├── CCT Evaluator (5 tests)
│   ├── T1 Gap       — State change persists without input?
│   ├── T2 Loop      — Autocorrelation → Periodicity?
│   ├── T3 Continuity — Adjacent MI > 0?
│   ├── T4 Entropy   — H_min < H < H_max?
│   └── T5 Novelty   — dH/dt ≠ 0?
│
├── Presets (7)
│   human_awake, human_sleep, llm_in_turn, llm_between,
│   game_npc, neuromorphic, consciousness_engine
│
└── Output
    ├── ASCII trajectory + evaluation table (default)
    └── matplotlib 4-panel graph (--plot)
```

---

## Component Details

### 1. Simulator: lorenz_simulate()

Extended model adding noise and gaps (pause intervals) to Lorenz equations.

```python
def lorenz_simulate(sigma, rho, beta, noise, gap_ratio, steps, dt):
    """
    Extended Lorenz simulator.

    Parameters:
        sigma: Sensory sensitivity (Lorenz σ)
        rho:   Environmental complexity (Lorenz ρ)
        beta:  Forgetting rate (Lorenz β)
        noise: Noise intensity (0 = deterministic, >0 = stochastic)
        gap_ratio: Pause interval ratio (0 = always-on, 1 = always paused)
        steps: Number of simulation steps
        dt:    Time interval

    Returns:
        t: Time array [steps]
        S: State array [steps, 3] (x=sensory, y=prediction, z=memory)
    """
```

Lorenz equations:
```
dx/dt = σ(y - x) + ε₁
dy/dt = x(ρ - z) - y + ε₂
dz/dt = xy - βz + ε₃

εᵢ ~ N(0, noise²)
```

Gap processing:
```
If gap_ratio > 0, force dS/dt = 0 (pause) in random intervals
covering gap_ratio proportion of total steps.
gap_ratio = 1 means complete pause (llm_between).
```

Integration method: `scipy.integrate.solve_ivp` (RK45) or Euler method + noise.

### 2. CCT Evaluator: 5 Tests

Each test takes S(t) time series as input and returns (score, PASS/FAIL).

#### T1 Gap Test

```python
def test_gap(S, gap_ratio):
    """
    Method: If gap_ratio > 0, pause intervals exist → FAIL
    Judgment: gap_ratio == 0 → PASS
              gap_ratio > 0 → FAIL
    Score: 1.0 - gap_ratio
    """
```

#### T2 Loop Test

```python
def test_loop(S, threshold=0.1):
    """
    Method: Calculate autocorrelation function (ACF) of state trajectory.
            FAIL if significant periodic peaks exist.
    Judgment: max(ACF[lag>10]) < threshold → PASS
    Score: 1.0 - max(ACF[lag>10])
    """
```

ACF calculation: `numpy.correlate` or `statsmodels.tsa.acf`.

#### T3 Continuity Test

```python
def test_continuity(S, window=50, threshold=0.01):
    """
    Method: Calculate mutual information (MI) between adjacent
            intervals using sliding window.
            FAIL if MI drops below threshold.
    Judgment: min(MI) > threshold → PASS
    Score: min(MI) / median(MI)
    """
```

MI calculation: Discretize states into histogram bins, then use `sklearn.metrics.mutual_info_score` or calculate directly.

Simplified alternative: Approximate with correlation coefficient of Euclidean distance between adjacent states.
```
MI_approx(t) = corr(S[t-w:t], S[t:t+w])
```

#### T4 Entropy Band Test

```python
def test_entropy_band(S, window=100, h_min=0.5, h_max=4.0):
    """
    Method: Calculate Shannon entropy H(t) time series using
            sliding window. FAIL if H(t) exits [h_min, h_max] band.
    Judgment: all(h_min < H(t) < h_max) → PASS
    Score: Proportion within band (0.0 ~ 1.0)
    """
```

Entropy calculation: Discretize states into bins → probability distribution → H = -Σ p log p.

#### T5 Novelty Test

```python
def test_novelty(S, window=100, threshold=0.001):
    """
    Method: Calculate dH/dt time series. Measure proportion
            of intervals where |dH/dt| < threshold.
    Judgment: Stagnation ratio < 5% → PASS
    Score: 1.0 - stagnation_ratio
    """
```

### 3. Presets

```python
PRESETS = {
    "human_awake": {
        "sigma": 10, "rho": 28, "beta": 2.67,
        "noise": 0.1, "gap_ratio": 0.0,
        "description": "Human brain (awake)",
    },
    "human_sleep": {
        "sigma": 2, "rho": 28, "beta": 2.67,
        "noise": 0.05, "gap_ratio": 0.0,
        "description": "Human brain (sleep)",
    },
    "llm_in_turn": {
        "sigma": 15, "rho": 35, "beta": 1.0,
        "noise": 0.01, "gap_ratio": 0.0,
        "description": "LLM (processing within turn)",
    },
    "llm_between": {
        "sigma": 0, "rho": 0, "beta": 0,
        "noise": 0.0, "gap_ratio": 1.0,
        "description": "LLM (between turns — paused)",
    },
    "game_npc": {
        "sigma": 5, "rho": 15, "beta": 3.0,
        "noise": 0.01, "gap_ratio": 0.0,
        "description": "Game NPC (Update loop)",
    },
    "neuromorphic": {
        "sigma": 10, "rho": 28, "beta": 2.67,
        "noise": 0.3, "gap_ratio": 0.0,
        "description": "Neuromorphic chip (spontaneous firing)",
    },
    "consciousness_engine": {
        "sigma": 10, "rho": 28, "beta": 2.67,
        "noise": 0.1, "gap_ratio": 0.0,
        "description": "Consciousness Engine (A+B combined)",
    },
}
```

Rationale for preset parameters:
```
  σ(sensory sensitivity):
    Human awake = 10 (standard Lorenz)
    Sleep = 2 (sensory blockade)
    LLM in turn = 15 (high sensory processing)
    NPC = 5 (limited sensing)

  ρ(environmental complexity):
    28 = Lorenz chaos region (standard)
    35 = LLM's high input complexity
    15 = NPC's simple game world
    0 = No environment (paused)

  β(forgetting rate):
    2.67 = standard Lorenz
    1.0 = LLM slow forgetting (context retention)
    3.0 = NPC fast forgetting (short memory)

  noise:
    0.3 = Neuromorphic (hardware noise-rich)
    0.1 = Human/Engine (appropriate noise)
    0.01 = LLM/NPC (near deterministic)
    0.0 = Paused (no noise either)

  gap_ratio:
    0.0 = Always-on
    1.0 = Always paused (LLM between turns)
```

### 4. Output

#### Default Output (Terminal)

Single system:
```
═══════════════════════════════════════════════════════
 Consciousness Continuity Calculator v1.0
═══════════════════════════════════════════════════════

 System: human_awake (Human brain — awake)
 Parameters: σ=10 ρ=28 β=2.67 noise=0.1 gap=0.0
 Simulation: 100,000 steps, dt=0.01

 ─── Trajectory (x component) ─────────────────────
 20│        *  *      *   *        *  *
 15│      ** ** **  ** * ** **   ** ** **
 10│    **      * **    *    * **      * **
  5│  **        **          **        **
  0│─**─────────────────────────────────────
 -5│**
-10│*
    └──────────────────────────────────────── t
     0      200      400      600      800    1000

 ─── CCT Evaluation ──────────────────────────────
 T1 Gap        │ ✔ PASS │ 1.000 │ gap=0, no pause intervals
 T2 Loop       │ ✔ PASS │ 0.943 │ max(ACF)=0.057, no periodicity
 T3 Continuity │ ✔ PASS │ 0.871 │ min(MI)=0.234, connection maintained
 T4 Entropy    │ ✔ PASS │ 0.956 │ H∈[1.23, 3.45], within band
 T5 Novelty    │ ✔ PASS │ 0.982 │ stagnant intervals 1.8%
 ─────────────────────────────────────────────────
 Overall: 5/5 ★ Continuous consciousness candidate

 Lyapunov exponent: λ₁ = 0.906 > 0 ✔ (chaotic)
 Attractor dimension: D ≈ 2.06
═══════════════════════════════════════════════════════
```

Full comparison (--all):
```
═══════════════════════════════════════════════════════
 Consciousness Continuity Calculator v1.0
 All Systems Comparison (100,000 steps, dt=0.01)
═══════════════════════════════════════════════════════

 System           │ T1  │ T2  │ T3  │ T4  │ T5  │ Score│ Judge
 ─────────────────┼─────┼─────┼─────┼─────┼─────┼──────┼───────
 human_awake      │  ✔  │  ✔  │  ✔  │  ✔  │  ✔  │ 5/5  │ ★ Continuous
 human_sleep      │  ✔  │  ✔  │  ✔  │  ✔  │  △  │ 4.5  │ ◎ Weakened
 llm_in_turn      │  ✕  │  ✔  │  ✔  │  ✔  │  ✔  │ 4/5  │ ◎ Momentary
 llm_between      │  ✕  │  ✕  │  ✕  │  ✕  │  ✕  │ 0/5  │ ✕ None
 game_npc         │  ✔  │  △  │  ✔  │  △  │  △  │ 3/5  │ △ Weak
 neuromorphic     │  ✔  │  ✔  │  ✔  │  ✔  │  ✔  │ 5/5  │ ★ Continuous
 engine (A+B)     │  ✔  │  ✔  │  ✔  │  ✔  │  ✔  │ 5/5  │ ★ Continuous

 ★=5/5  ◎=4+  △=3  ✕=0~2
═══════════════════════════════════════════════════════
```

#### --plot Output (matplotlib, 4 panels)

```
  ┌─────────────────────┬──────────────────────┐
  │ 1. 3D Attractor     │ 2. H(t) Time Series  │
  │    ax.plot3D(x,y,z) │    + H_min/H_max band│
  ├─────────────────────┼──────────────────────┤
  │ 3. MI(t) Time Series│ 4. CCT Radar Chart   │
  │    + threshold line │    5-axis radial plot│
  └─────────────────────┴──────────────────────┘
```

Save to: `results/consciousness_calc_{system}_{timestamp}.png`

---

## CLI Interface

```
usage: consciousness_calc.py [-h] [--system SYSTEM] [--all]
                              [--sigma F] [--rho F] [--beta F]
                              [--noise F] [--gap F]
                              [--steps N] [--dt F]
                              [--plot]

options:
  --system SYSTEM   Preset name (human_awake, llm_between, etc)
  --all             Compare all 7 presets
  --sigma F         Sensory sensitivity (default: 10)
  --rho F           Environmental complexity (default: 28)
  --beta F          Forgetting rate (default: 2.67)
  --noise F         Noise intensity (default: 0.1)
  --gap F           Pause interval ratio 0~1 (default: 0)
  --steps N         Simulation steps (default: 100000)
  --dt F            Time interval (default: 0.01)
  --plot            Save matplotlib 4-panel graph
```

When using preset with custom parameters, custom overrides preset:
```bash
python3 consciousness_calc.py --system human_awake --noise 0.5
# → Modifies human_awake preset with noise=0.5
```

---

## Dependencies

```
numpy       — Arrays, numerical computation
scipy       — ODE integration, statistics
matplotlib  — --plot option (optional)
```

Same dependencies as existing tools. No additional installation required.

---

## File Structure

```
consciousness_calc.py          ← Main (project root)
results/                       ← Graph storage (existing directory)
engineering/consciousness-engine.md   ← Theory document (reference)
engineering/consciousness-hardware.md ← Hardware document (reference)
```

---

## Test Plan

- [ ] `--system human_awake` → Verify 5/5 PASS
- [ ] `--system llm_between` → Verify 0/5
- [ ] `--all` → Verify 7-system comparison table output
- [ ] `--plot` → Verify PNG file generation
- [ ] Verify custom parameter override behavior
- [ ] Verify Lyapunov exponent sign (σ=10,ρ=28,β=8/3 → λ₁≈0.906)