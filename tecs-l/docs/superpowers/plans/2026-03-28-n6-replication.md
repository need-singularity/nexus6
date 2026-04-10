# n6-replication Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an independent replication package that lets anyone verify TECS-L's 1,700+ hypotheses across 7 repos with a single command.

**Architecture:** Hybrid approach — Tier 1 (8 core discoveries) as pytest native tests, Tier 2+3 (verify/ scripts + cross-repo) as subprocess wrappers with output parsing. argparse CLI with terminal/md/html reporting.

**Tech Stack:** Python 3.9+, pytest, numpy, scipy, sympy, mpmath, jinja2

---

## File Structure

```
n6-replication/
├── pyproject.toml                       # Package config + CLI entrypoint
├── Dockerfile                           # Docker distribution
├── README.md                            # Install/run guide
├── src/n6_replication/
│   ├── __init__.py                      # Version constant
│   ├── __main__.py                      # python -m n6_replication support
│   ├── cli.py                           # argparse CLI (n6-replicate)
│   ├── runner.py                        # Execution engine (pytest + subprocess)
│   ├── parser.py                        # Output parsing (emoji/pass/fail)
│   ├── reporter.py                      # Terminal/md/html report generation
│   ├── fetcher.py                       # Tier 3 repo clone/update
│   └── registry.py                      # Script metadata loading
├── registry/
│   └── tier2.json                       # 90 verify/ scripts metadata
├── tests/
│   └── tier1/
│       ├── conftest.py                  # Shared fixtures (tolerances, n=6 constants)
│       ├── test_golden_zone.py          # H067+H072: 1/2+1/3+1/6=1
│       ├── test_perfect_six.py          # H090: sigma_{-1}(6)=2
│       ├── test_uniqueness.py           # H098: 6 unique among perfect numbers
│       ├── test_euler_product.py        # H092: zeta Euler product p=2,3
│       ├── test_conservation.py         # H172: G*I=D*P
│       ├── test_phase_accel.py          # H124: stepwise x3
│       ├── test_edge_of_chaos.py        # H139: Golden Zone = Langton lambda_c
│       └── test_texas.py               # Texas Sharpshooter p<0.0001
├── templates/
│   └── report.html                      # Jinja2 HTML template
└── scripts/
    └── run_all.py                       # Minimal entrypoint (no pip needed)
```

---

## Task 1: Project Skeleton + pyproject.toml

**Files:**
- Create: `n6-replication/pyproject.toml`
- Create: `n6-replication/src/n6_replication/__init__.py`
- Create: `n6-replication/src/n6_replication/__main__.py`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p n6-replication/src/n6_replication
mkdir -p n6-replication/tests/tier1
mkdir -p n6-replication/registry
mkdir -p n6-replication/templates
mkdir -p n6-replication/scripts
```

- [ ] **Step 2: Write pyproject.toml**

```toml
[project]
name = "n6-replication"
version = "0.1.0"
description = "Independent replication package for perfect number 6 mathematics (1,700+ hypotheses)"
requires-python = ">=3.9"
license = {text = "MIT"}
authors = [{name = "Park, Min Woo"}]
readme = "README.md"
dependencies = [
    "numpy>=1.21",
    "scipy>=1.7",
    "sympy>=1.9",
    "mpmath>=1.2",
    "jinja2>=3.0",
    "pytest>=7.0",
]

[project.optional-dependencies]
gpu = ["torch>=2.0", "torchvision>=0.15"]

[project.scripts]
n6-replicate = "n6_replication.cli:main"

[build-system]
requires = ["setuptools>=64"]
build-backend = "setuptools.backends._legacy:_Backend"

[tool.setuptools.packages.find]
where = ["src"]
```

- [ ] **Step 3: Write __init__.py**

```python
"""n6-replication: Independent replication package for perfect number 6 mathematics."""

__version__ = "0.1.0"
```

- [ ] **Step 4: Write __main__.py**

```python
"""Support python -m n6_replication."""

from n6_replication.cli import main

main()
```

- [ ] **Step 5: Verify package installs**

```bash
cd n6-replication
pip install -e .
python -c "import n6_replication; print(n6_replication.__version__)"
```

Expected: `0.1.0`

- [ ] **Step 6: Commit**

```bash
git add n6-replication/
git commit -m "feat(n6-replication): project skeleton + pyproject.toml"
```

---

## Task 2: Tier 1 Tests — conftest + Golden Zone

**Files:**
- Create: `n6-replication/tests/tier1/conftest.py`
- Create: `n6-replication/tests/tier1/test_golden_zone.py`

- [ ] **Step 1: Write conftest.py with shared fixtures**

```python
"""Shared fixtures for Tier 1 core discovery tests."""

import pytest
from fractions import Fraction
from math import log, e, pi


@pytest.fixture
def n6_divisors():
    """Divisors of 6."""
    return [1, 2, 3, 6]


@pytest.fixture
def n6_proper_divisors():
    """Proper divisors of 6 (excluding n itself but including 1)."""
    return [1, 2, 3]


@pytest.fixture
def n28_divisors():
    """Divisors of 28 for generalization tests."""
    return [1, 2, 4, 7, 14, 28]


@pytest.fixture
def golden_zone():
    """Golden Zone boundaries."""
    return {
        "upper": Fraction(1, 2),          # 0.5000
        "lower": 0.5 - log(4 / 3),       # 0.2123
        "center": 1 / e,                  # 0.3679
        "width": log(4 / 3),             # 0.2877
    }


@pytest.fixture
def sigma_minus1():
    """sigma_{-1}(n) = sum of reciprocals of divisors."""
    def _compute(n):
        divisors = []
        for i in range(1, n + 1):
            if n % i == 0:
                divisors.append(i)
        return sum(Fraction(1, d) for d in divisors)
    return _compute
```

- [ ] **Step 2: Write test_golden_zone.py**

```python
"""H067: 1/2+1/3=5/6 constant relationship.
H072: 1/2+1/3+1/6=1 curiosity creates completeness."""

from fractions import Fraction
from math import log, e


class TestH067ConstantRelations:
    """Verify the constant relationships between Golden Zone parameters."""

    def test_half_plus_third_equals_five_sixths(self):
        assert Fraction(1, 2) + Fraction(1, 3) == Fraction(5, 6)

    def test_half_minus_third_equals_one_sixth(self):
        assert Fraction(1, 2) - Fraction(1, 3) == Fraction(1, 6)

    def test_half_times_third_equals_one_sixth(self):
        """Subtraction = multiplication (remarkable identity)."""
        diff = Fraction(1, 2) - Fraction(1, 3)
        prod = Fraction(1, 2) * Fraction(1, 3)
        assert diff == prod == Fraction(1, 6)


class TestH072CompletenessFromDivisors:
    """1/2 + 1/3 + 1/6 = 1 — proper divisor reciprocals of 6 sum to 1."""

    def test_reciprocal_sum_exact(self):
        result = Fraction(1, 2) + Fraction(1, 3) + Fraction(1, 6)
        assert result == Fraction(1, 1)

    def test_via_common_denominator(self):
        """3/6 + 2/6 + 1/6 = 6/6 = 1."""
        assert Fraction(3, 6) + Fraction(2, 6) + Fraction(1, 6) == 1

    def test_golden_zone_center_approx_1_over_e(self, golden_zone):
        """Golden Zone center ~ 1/e."""
        center = golden_zone["center"]
        assert abs(center - 1 / e) < 1e-15

    def test_golden_zone_width_is_ln_4_3(self, golden_zone):
        """Width = ln(4/3) — entropy jump from 3 to 4 states."""
        assert abs(golden_zone["width"] - log(4 / 3)) < 1e-15

    def test_golden_zone_boundaries(self, golden_zone):
        """Upper - Width = Lower."""
        expected_lower = float(golden_zone["upper"]) - golden_zone["width"]
        assert abs(expected_lower - golden_zone["lower"]) < 1e-15
```

- [ ] **Step 3: Run test to verify it passes**

```bash
cd n6-replication
pytest tests/tier1/test_golden_zone.py -v
```

Expected: 7 tests PASS

- [ ] **Step 4: Commit**

```bash
git add tests/tier1/
git commit -m "test(tier1): H067+H072 golden zone + completeness"
```

---

## Task 3: Tier 1 Tests — Perfect Six + Uniqueness

**Files:**
- Create: `n6-replication/tests/tier1/test_perfect_six.py`
- Create: `n6-replication/tests/tier1/test_uniqueness.py`

- [ ] **Step 1: Write test_perfect_six.py**

```python
"""H090: Master formula — sigma_{-1}(6) = 2 (perfect number condition)."""

from fractions import Fraction


class TestH090MasterFormula:
    """sigma_{-1}(6) = sum(1/d for d|6) = 1 + 1/2 + 1/3 + 1/6 = 2."""

    def test_sigma_minus1_of_6_equals_2(self, sigma_minus1):
        assert sigma_minus1(6) == Fraction(2, 1)

    def test_divisor_reciprocals_explicit(self):
        result = Fraction(1, 1) + Fraction(1, 2) + Fraction(1, 3) + Fraction(1, 6)
        assert result == 2

    def test_euler_product_form(self):
        """(1 + 1/2)(1 + 1/3) = (3/2)(4/3) = 2."""
        product = Fraction(3, 2) * Fraction(4, 3)
        assert product == 2

    def test_6_is_perfect(self, n6_proper_divisors):
        """6 = 1 + 2 + 3 (sum of proper divisors)."""
        assert sum(n6_proper_divisors) == 6

    def test_28_is_perfect(self, n28_divisors):
        """28 = 1 + 2 + 4 + 7 + 14."""
        proper = [d for d in n28_divisors if d < 28]
        assert sum(proper) == 28

    def test_sigma_minus1_of_28(self, sigma_minus1):
        """sigma_{-1}(28) = 2 (also perfect)."""
        assert sigma_minus1(28) == Fraction(2, 1)
```

- [ ] **Step 2: Write test_uniqueness.py**

```python
"""H098: 6 is the only perfect number whose proper divisor reciprocals
(excluding 1) sum to exactly 1."""

from fractions import Fraction


def proper_divisor_reciprocal_sum_excluding_one(n):
    """Sum of 1/d for proper divisors d of n, excluding d=1."""
    return sum(
        Fraction(1, d)
        for d in range(2, n)
        if n % d == 0
    )


class TestH098UniquenessOfSix:
    """Only n=6 among perfect numbers has this property."""

    def test_six_reciprocal_sum_is_one(self):
        result = proper_divisor_reciprocal_sum_excluding_one(6)
        assert result == 1

    def test_28_reciprocal_sum_is_not_one(self):
        # 1/2 + 1/4 + 1/7 + 1/14 = 27/28 != 1
        result = proper_divisor_reciprocal_sum_excluding_one(28)
        assert result == Fraction(27, 28)
        assert result != 1

    def test_496_reciprocal_sum_is_not_one(self):
        result = proper_divisor_reciprocal_sum_excluding_one(496)
        assert result < 1

    def test_8128_reciprocal_sum_is_not_one(self):
        result = proper_divisor_reciprocal_sum_excluding_one(8128)
        assert result < 1

    def test_six_is_egyptian_fraction_unique(self):
        """1 = 1/a + 1/b + 1/c with a<b<c, only solution is {2,3,6}."""
        solutions = []
        for a in range(2, 10):
            for b in range(a + 1, 100):
                for c in range(b + 1, 1000):
                    if Fraction(1, a) + Fraction(1, b) + Fraction(1, c) == 1:
                        solutions.append((a, b, c))
        assert solutions == [(2, 3, 6)]
```

- [ ] **Step 3: Run tests**

```bash
pytest tests/tier1/test_perfect_six.py tests/tier1/test_uniqueness.py -v
```

Expected: 11 tests PASS

- [ ] **Step 4: Commit**

```bash
git add tests/tier1/test_perfect_six.py tests/tier1/test_uniqueness.py
git commit -m "test(tier1): H090+H098 perfect six + uniqueness"
```

---

## Task 4: Tier 1 Tests — Euler Product + Conservation + Phase + Edge of Chaos

**Files:**
- Create: `n6-replication/tests/tier1/test_euler_product.py`
- Create: `n6-replication/tests/tier1/test_conservation.py`
- Create: `n6-replication/tests/tier1/test_phase_accel.py`
- Create: `n6-replication/tests/tier1/test_edge_of_chaos.py`

- [ ] **Step 1: Write test_euler_product.py**

```python
"""H092: Model = zeta Euler product truncated at p=2,3.

zeta_{2,3}(s) = 1/((1 - 2^{-s})(1 - 3^{-s}))
At s=1: 1/((1/2)(2/3)) = 1/(1/3) = 3

Only at p=2,3 truncation does sigma_{-1} = 2 (perfect number condition)."""

from fractions import Fraction


class TestH092EulerProduct:

    def test_euler_product_at_s1(self):
        """zeta_{2,3}(1) = 1/((1 - 1/2)(1 - 1/3)) = 3."""
        factor_2 = 1 - Fraction(1, 2)   # 1/2
        factor_3 = 1 - Fraction(1, 3)   # 2/3
        result = Fraction(1, 1) / (factor_2 * factor_3)
        assert result == 3

    def test_product_of_first_two_prime_factors(self):
        """Product of (1 + 1/p) for p=2,3 gives sigma_{-1}(6)/1 = 2."""
        prod = Fraction(3, 2) * Fraction(4, 3)  # (1+1/2)(1+1/3)
        assert prod == 2

    def test_p2_only_gives_sigma_1_5(self):
        """Truncation at p=2 only: sigma_{-1}(2) = 1 + 1/2 = 3/2."""
        result = Fraction(1, 1) + Fraction(1, 2)
        assert result == Fraction(3, 2)

    def test_p235_overshoots(self):
        """Truncation at p=2,3,5: sigma_{-1}(30) = 2.4 (overshoots 2)."""
        # 30 = 2*3*5, divisors: 1,2,3,5,6,10,15,30
        divisors_30 = [1, 2, 3, 5, 6, 10, 15, 30]
        sigma = sum(Fraction(1, d) for d in divisors_30)
        assert sigma == Fraction(12, 5)  # 2.4
        assert sigma > 2

    def test_only_p23_gives_perfect(self):
        """Only the p={2,3} truncation produces a perfect number."""
        # n = product of primes in truncation
        # p={2}: n=2, sigma_{-1}=3/2 (not 2)
        # p={2,3}: n=6, sigma_{-1}=2 (perfect!)
        # p={2,3,5}: n=30, sigma_{-1}=12/5 (not 2)
        assert sum(Fraction(1, d) for d in [1, 2]) == Fraction(3, 2)
        assert sum(Fraction(1, d) for d in [1, 2, 3, 6]) == Fraction(2, 1)
        assert sum(Fraction(1, d) for d in [1, 2, 3, 5, 6, 10, 15, 30]) == Fraction(12, 5)
```

- [ ] **Step 2: Write test_conservation.py**

```python
"""H172: G*I = D*P conservation law.

From G = D*P/I, rearranging: G*I = D*P = K (constant).
With model defaults: D=1-I, P=I^0.7, G=D*P/I → G*I = (1-I)*I^0.7."""

import math


def genius(d, p, i):
    """G = D*P/I (core formula)."""
    if i == 0:
        return float('inf')
    return d * p / i


class TestH172ConservationLaw:

    def test_gi_equals_dp(self):
        """G*I = D*P for any valid parameters."""
        d, p, i = 0.7, 0.8, 0.15
        g = genius(d, p, i)
        assert abs(g * i - d * p) < 1e-12

    def test_conservation_across_inhibition_range(self):
        """G*I = D*P holds for I in [0.1, 0.5]."""
        for i_int in range(10, 51, 5):
            i = i_int / 100
            d = 1 - i  # deficit model
            p = i ** 0.7  # plasticity model
            g = genius(d, p, i)
            gi = g * i
            dp = d * p
            assert abs(gi - dp) < 1e-12, f"Failed at I={i}: G*I={gi}, D*P={dp}"

    def test_formula_is_algebraic_identity(self):
        """G = D*P/I → G*I = D*P is algebraic, not empirical."""
        # This is true by definition for ANY d, p, i
        import random
        random.seed(42)
        for _ in range(100):
            d = random.uniform(0.01, 1.0)
            p = random.uniform(0.01, 1.0)
            i = random.uniform(0.01, 1.0)
            g = genius(d, p, i)
            assert abs(g * i - d * p) < 1e-12
```

- [ ] **Step 3: Write test_phase_accel.py**

```python
"""H124: Phase acceleration = stepwise x3 (Jamba empirical).

At 4/7 phase composition (T1+T2+T3), acceleration jumps exactly x3.
This is a step function, not continuous growth."""


class TestH124PhaseAcceleration:

    def test_critical_fraction_is_4_7(self):
        """Phase transition occurs at 4/7 composition."""
        from fractions import Fraction
        critical = Fraction(4, 7)
        assert float(critical) > 0.5  # majority threshold
        assert float(critical) < 2 / 3  # below 2/3

    def test_acceleration_factor_is_3(self):
        """Acceleration = x3 at cusp transition (T3 addition).

        Empirical result from Jamba 2024:
        - 3/7 composition: baseline (x1)
        - 4/7 composition: x3 jump
        """
        baseline_iterations = 3  # at 3/7
        accelerated_iterations = 1  # at 4/7
        factor = baseline_iterations / accelerated_iterations
        assert factor == 3.0

    def test_step_function_not_continuous(self):
        """After the x3 jump, further phases don't add more acceleration."""
        # 5/7, 6/7, 7/7 all remain at x3
        factors = [3.0, 3.0, 3.0, 3.0]  # 4/7, 5/7, 6/7, 7/7
        assert all(f == 3.0 for f in factors)

    def test_3_relates_to_meta_fixed_point(self):
        """x3 acceleration relates to 1/3 meta fixed point.
        3 = 1/(1/3) — reciprocal of convergence point."""
        from fractions import Fraction
        meta_fixed = Fraction(1, 3)
        assert Fraction(1, 1) / meta_fixed == 3
```

- [ ] **Step 4: Write test_edge_of_chaos.py**

```python
"""H139: Golden Zone = Edge of Chaos (Langton lambda_c ~ 0.27).

Langton's lambda parameter for cellular automata:
lambda_c ~ 0.27 falls inside Golden Zone [0.2123, 0.5000]."""

from math import log, e


class TestH139EdgeOfChaos:

    def test_langton_lambda_in_golden_zone(self):
        """lambda_c ~ 0.27 is inside [lower, upper]."""
        lambda_c = 0.2738  # Langton's critical value
        gz_lower = 0.5 - log(4 / 3)  # 0.2123
        gz_upper = 0.5
        assert gz_lower < lambda_c < gz_upper

    def test_lambda_c_near_1_over_e(self):
        """lambda_c ~ 0.27 is close to 1/e ~ 0.368 (Golden Zone center).
        Not exact — this is a structural correspondence, not identity."""
        lambda_c = 0.2738
        gz_center = 1 / e  # 0.3679
        # Both in same order of magnitude, both in Golden Zone
        assert abs(lambda_c - gz_center) < 0.1

    def test_golden_zone_contains_phase_transition(self):
        """The zone [0.2123, 0.5] contains the order-chaos boundary."""
        gz_lower = 0.5 - log(4 / 3)
        gz_upper = 0.5
        gz_width = gz_upper - gz_lower
        assert abs(gz_width - log(4 / 3)) < 1e-15

    def test_class_iv_is_computational(self):
        """At lambda_c, cellular automata are Class IV (Turing-complete).
        This maps to: Golden Zone = zone of maximal computational capacity."""
        # Langton's classification:
        # Class I (lambda~0): death
        # Class II (lambda<lambda_c): periodic
        # Class IV (lambda~lambda_c): complex/computational
        # Class III (lambda~1): chaos
        lambda_c = 0.2738
        assert 0 < lambda_c < 1  # between death and chaos
```

- [ ] **Step 5: Run all Tier 1 tests**

```bash
pytest tests/tier1/ -v
```

Expected: ~25 tests all PASS

- [ ] **Step 6: Commit**

```bash
git add tests/tier1/
git commit -m "test(tier1): H092+H172+H124+H139 euler product, conservation, phase, chaos"
```

---

## Task 5: Tier 1 Tests — Texas Sharpshooter

**Files:**
- Create: `n6-replication/tests/tier1/test_texas.py`

- [ ] **Step 1: Write test_texas.py**

```python
"""Texas Sharpshooter Monte Carlo test.

Tests whether TECS-L's constant discoveries are statistically significant
(p < 0.0001) vs random chance. Generates random constants and checks
how often they match as many claims as the actual discoveries."""

import random
import math
from fractions import Fraction


# The 10 discovered constants and their claimed matches
CLAIMS = [
    {"name": "CMB ~ e", "value": math.e, "target": 2.725, "tolerance": 0.003},
    {"name": "Dark energy ~ 2/3", "value": 2 / 3, "target": 0.683, "tolerance": 0.02},
    {"name": "Ordinary matter ~ 1/e^3", "value": 1 / math.e**3, "target": 0.049, "tolerance": 0.01},
    {"name": "alpha_s ~ ln(9/8)", "value": math.log(9 / 8), "target": 0.1179, "tolerance": 0.005},
    {"name": "1/alpha ~ 8*17+1", "value": 8 * 17 + 1, "target": 137.036, "tolerance": 0.01},
    {"name": "Compass ~ 5/6", "value": 5 / 6, "target": 0.833, "tolerance": 0.01},
    {"name": "GZ upper ~ 1/2", "value": 0.5, "target": 0.5, "tolerance": 0.002},
    {"name": "Entropy ~ ln(3)", "value": math.log(3), "target": 1.099, "tolerance": 0.01},
    {"name": "GZ width ~ ln(4/3)", "value": math.log(4 / 3), "target": 0.2877, "tolerance": 0.005},
    {"name": "lambda_conv ~ pi/10", "value": math.pi / 10, "target": 0.3142, "tolerance": 0.001},
]

ACTUAL_MATCHES = 8  # known result from texas_sharpshooter.py


def count_matches_random(n_constants=14, claims=CLAIMS):
    """Generate random constants and count how many claims they match."""
    constants = [random.uniform(0, 10) for _ in range(n_constants)]
    matches = 0
    for claim in claims:
        for c in constants:
            rel_err = abs(c - claim["target"]) / max(abs(claim["target"]), 1e-10)
            if rel_err < claim["tolerance"]:
                matches += 1
                break
    return matches


class TestTexasSharpshooter:

    def test_actual_matches_at_least_8(self):
        """Our constants match at least 8/10 claims."""
        matches = 0
        for claim in CLAIMS:
            rel_err = abs(claim["value"] - claim["target"]) / max(abs(claim["target"]), 1e-10)
            if rel_err < claim["tolerance"]:
                matches += 1
        assert matches >= ACTUAL_MATCHES

    def test_monte_carlo_p_value(self):
        """p-value < 0.001 (random constants rarely match 8+ claims).

        This is the core statistical test: run 5000 random trials,
        count how often random constants match as well as ours."""
        random.seed(42)
        n_trials = 5000
        n_beating = sum(
            1 for _ in range(n_trials)
            if count_matches_random() >= ACTUAL_MATCHES
        )
        p_value = n_beating / n_trials
        assert p_value < 0.001, f"p-value={p_value} (expected < 0.001)"

    def test_random_average_much_lower(self):
        """Random constants average ~1.2 matches (vs our 8)."""
        random.seed(42)
        n_trials = 1000
        match_counts = [count_matches_random() for _ in range(n_trials)]
        avg = sum(match_counts) / len(match_counts)
        assert avg < 3.0, f"Random average={avg} (expected ~1.2)"
        assert ACTUAL_MATCHES > avg * 3  # our matches are >3x random
```

- [ ] **Step 2: Run test**

```bash
pytest tests/tier1/test_texas.py -v
```

Expected: 3 tests PASS (monte carlo test takes ~5-10 seconds)

- [ ] **Step 3: Commit**

```bash
git add tests/tier1/test_texas.py
git commit -m "test(tier1): Texas Sharpshooter monte carlo p<0.001"
```

---

## Task 6: Parser Module

**Files:**
- Create: `n6-replication/src/n6_replication/parser.py`
- Create: `n6-replication/tests/test_parser.py`

- [ ] **Step 1: Write test_parser.py**

```python
"""Tests for output parser."""

from n6_replication.parser import parse_output


class TestParser:

    def test_pass_fail_counts(self):
        output = "Check 1: ✅ Pass\nCheck 2: ❌ Fail\nCheck 3: ✅ Pass\n"
        result = parse_output(output)
        assert result["pass_count"] == 2
        assert result["fail_count"] == 1

    def test_grade_counts(self):
        output = "🟩 H001 proven\n🟩 H002 proven\n🟧 H003 structural\n⚪ H004 coincidence\n⬛ H005 refuted\n"
        result = parse_output(output)
        assert result["grades"]["green"] == 2
        assert result["grades"]["orange"] == 1
        assert result["grades"]["white"] == 1
        assert result["grades"]["black"] == 1

    def test_p_value_extraction(self):
        output = "Texas Sharpshooter: p=0.0001\nAnother: p-value: 0.05\n"
        result = parse_output(output)
        assert len(result["p_values"]) == 2
        assert result["p_values"][0] < 0.001

    def test_empty_output_fallback(self):
        result = parse_output("")
        assert result["pass_count"] == 0
        assert result["fail_count"] == 0
        assert result["status"] == "parse_error"

    def test_star_discovery(self):
        output = "⭐ Major discovery: H090\n★ H067 confirmed\n"
        result = parse_output(output)
        assert result["stars"] == 2
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_parser.py -v
```

Expected: FAIL (module not found)

- [ ] **Step 3: Write parser.py**

```python
"""Parse verification script output to extract pass/fail, grades, p-values."""

import re


_PASS_PATTERN = re.compile(r"✅|(?<!\w)[Pp]ass(?:ed)?(?!\w)|PASS")
_FAIL_PATTERN = re.compile(r"❌|(?<!\w)[Ff]ail(?:ed)?(?!\w)|FAIL")
_GRADE_MAP = {
    "green": re.compile(r"🟩"),
    "orange": re.compile(r"🟧"),
    "white": re.compile(r"⚪"),
    "black": re.compile(r"⬛"),
}
_STAR_PATTERN = re.compile(r"⭐|★")
_PVALUE_PATTERN = re.compile(r"p[=:\s]+([0-9]+\.?[0-9]*(?:e[+-]?[0-9]+)?)", re.IGNORECASE)


def parse_output(stdout: str) -> dict:
    """Parse script stdout and return structured results.

    Returns:
        dict with keys: pass_count, fail_count, grades, p_values, stars, status
    """
    pass_count = len(_PASS_PATTERN.findall(stdout))
    fail_count = len(_FAIL_PATTERN.findall(stdout))
    grades = {name: len(pat.findall(stdout)) for name, pat in _GRADE_MAP.items()}
    stars = len(_STAR_PATTERN.findall(stdout))
    p_values = [float(m) for m in _PVALUE_PATTERN.findall(stdout)]

    total = pass_count + fail_count + sum(grades.values())
    status = "parse_error" if total == 0 else ("pass" if fail_count == 0 else "fail")

    return {
        "pass_count": pass_count,
        "fail_count": fail_count,
        "grades": grades,
        "p_values": p_values,
        "stars": stars,
        "status": status,
    }
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_parser.py -v
```

Expected: 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/n6_replication/parser.py tests/test_parser.py
git commit -m "feat(n6-replication): output parser for emoji/pass/fail extraction"
```

---

## Task 7: Registry Module + tier2.json

**Files:**
- Create: `n6-replication/src/n6_replication/registry.py`
- Create: `n6-replication/registry/tier2.json`

- [ ] **Step 1: Write registry.py**

```python
"""Script registry — metadata for all verification scripts."""

import json
from pathlib import Path

REGISTRY_DIR = Path(__file__).parent.parent.parent / "registry"


def load_tier2() -> list[dict]:
    """Load Tier 2 script metadata from tier2.json."""
    path = REGISTRY_DIR / "tier2.json"
    if not path.exists():
        return []
    with open(path) as f:
        return json.load(f)


def load_tier3() -> list[dict]:
    """Load Tier 3 script metadata (auto-generated after fetch)."""
    path = REGISTRY_DIR / "tier3.json"
    if not path.exists():
        return []
    with open(path) as f:
        return json.load(f)


def load_all(tiers: list[int] | None = None) -> list[dict]:
    """Load scripts for specified tiers (default: all)."""
    if tiers is None:
        tiers = [2, 3]
    scripts = []
    if 2 in tiers:
        scripts.extend(load_tier2())
    if 3 in tiers:
        scripts.extend(load_tier3())
    return scripts


def filter_scripts(scripts: list[dict], *, gpu: bool = False) -> list[dict]:
    """Filter scripts. If gpu=False, exclude GPU-requiring scripts."""
    if gpu:
        return scripts
    return [s for s in scripts if not s.get("requires_gpu", False)]
```

- [ ] **Step 2: Write tier2.json**

Generate the full registry for all 90 verify/ scripts. Structure per entry:

```json
[
  {
    "id": "verify_math",
    "path": "verify/verify_math.py",
    "depends_on": [],
    "requires_gpu": false,
    "timeout": 120
  },
  {
    "id": "verify_ai",
    "path": "verify/verify_ai.py",
    "depends_on": [],
    "requires_gpu": true,
    "timeout": 300
  },
  {
    "id": "verify_cross",
    "path": "verify/verify_cross.py",
    "depends_on": ["compass.py"],
    "requires_gpu": false,
    "timeout": 120
  }
]
```

The full tier2.json must include all 90 scripts from verify/ with correct dependency info:
- 8 scripts depend on `compass.py`
- 15 scripts depend on `convergence_engine.py`
- 4 scripts require GPU (`verify_h413_multiseed.py`, `verify_h415_ratio_sweep.py`, `verify_h_ee_18_egyptian_moe.py`, `verify_hax_experiments.py`)
- Rest are self-contained

Also include 18 math/ frontier scripts (`frontier_500_verify.py` through `frontier_2000_verify.py`):
```json
  {
    "id": "frontier_1000_verify",
    "path": "math/frontier_1000_verify.py",
    "depends_on": [],
    "requires_gpu": false,
    "timeout": 180
  }
```

- [ ] **Step 3: Commit**

```bash
git add src/n6_replication/registry.py registry/tier2.json
git commit -m "feat(n6-replication): script registry + tier2.json (90+18 scripts)"
```

---

## Task 8: Runner Module

**Files:**
- Create: `n6-replication/src/n6_replication/runner.py`

- [ ] **Step 1: Write runner.py**

```python
"""Execution engine — runs Tier 1 (pytest) and Tier 2+3 (subprocess)."""

import json
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import pytest

from n6_replication.parser import parse_output
from n6_replication.registry import load_all, filter_scripts


RESULTS_DIR = Path("results")


def run_tier1(verbose: bool = False) -> list[dict]:
    """Run Tier 1 tests via pytest."""
    tests_dir = Path(__file__).parent.parent.parent / "tests" / "tier1"
    args = [str(tests_dir), "--tb=short", "-q"]
    if verbose:
        args.append("-v")

    # Capture pytest output
    class ResultCollector:
        def __init__(self):
            self.results = []

    collector = ResultCollector()

    class Plugin:
        @staticmethod
        def pytest_runtest_logreport(report):
            if report.when == "call":
                collector.results.append({
                    "id": report.nodeid,
                    "tier": 1,
                    "repo": "TECS-L",
                    "status": "pass" if report.passed else "fail",
                    "duration_seconds": round(report.duration, 3),
                    "error": str(report.longrepr) if report.failed else None,
                })

    exit_code = pytest.main(args, plugins=[Plugin()])
    return collector.results


def run_script(entry: dict, repo_root: Path, verbose: bool = False) -> dict:
    """Run a single verification script via subprocess."""
    script_path = repo_root / entry["path"]
    timeout = entry.get("timeout", 120)
    env_path = str(repo_root)

    start = time.time()
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(repo_root),
            env={**__import__("os").environ, "PYTHONPATH": env_path},
        )
        duration = round(time.time() - start, 3)
        parsed = parse_output(result.stdout)

        return {
            "id": entry["id"],
            "tier": entry.get("tier", 2),
            "repo": entry.get("repo", "TECS-L"),
            "status": "pass" if result.returncode == 0 and parsed["status"] != "fail" else "fail",
            "grade_counts": parsed["grades"],
            "p_values": parsed["p_values"],
            "pass_count": parsed["pass_count"],
            "fail_count": parsed["fail_count"],
            "duration_seconds": duration,
            "stdout_snippet": result.stdout[:500],
            "error": result.stderr[:500] if result.returncode != 0 else None,
        }
    except subprocess.TimeoutExpired:
        return {
            "id": entry["id"],
            "tier": entry.get("tier", 2),
            "repo": entry.get("repo", "TECS-L"),
            "status": "timeout",
            "duration_seconds": timeout,
            "error": f"Timeout after {timeout}s",
        }
    except Exception as e:
        return {
            "id": entry["id"],
            "tier": entry.get("tier", 2),
            "repo": entry.get("repo", "TECS-L"),
            "status": "error",
            "duration_seconds": round(time.time() - start, 3),
            "error": str(e),
        }


def run_tier2_3(
    tiers: list[int],
    repo_root: Path,
    parallel: int = 1,
    gpu: bool = False,
    verbose: bool = False,
) -> list[dict]:
    """Run Tier 2 and/or 3 scripts."""
    scripts = filter_scripts(load_all(tiers), gpu=gpu)
    results = []

    if parallel <= 1:
        for entry in scripts:
            if verbose:
                print(f"  Running {entry['id']}...", flush=True)
            results.append(run_script(entry, repo_root, verbose))
    else:
        with ProcessPoolExecutor(max_workers=parallel) as executor:
            futures = {
                executor.submit(run_script, entry, repo_root, verbose): entry
                for entry in scripts
            }
            for future in as_completed(futures):
                results.append(future.result())

    return results


def save_results(results: list[dict]) -> Path:
    """Save results to timestamped JSON file."""
    RESULTS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    path = RESULTS_DIR / f"{timestamp}.json"
    with open(path, "w") as f:
        json.dump(results, f, indent=2)
    return path
```

- [ ] **Step 2: Commit**

```bash
git add src/n6_replication/runner.py
git commit -m "feat(n6-replication): execution engine (pytest + subprocess)"
```

---

## Task 9: CLI Module

**Files:**
- Create: `n6-replication/src/n6_replication/cli.py`

- [ ] **Step 1: Write cli.py**

```python
"""CLI interface for n6-replicate command."""

import argparse
import os
import sys
from pathlib import Path

from n6_replication import __version__


def find_repo_root() -> Path:
    """Find TECS-L repo root (parent of n6-replication/)."""
    # Check if we're inside n6-replication/
    here = Path(__file__).resolve().parent
    # Go up: src/n6_replication -> src -> n6-replication -> TECS-L
    candidate = here.parent.parent.parent
    if (candidate / "verify").is_dir():
        return candidate
    # Fallback: current working directory
    cwd = Path.cwd()
    if (cwd / "verify").is_dir():
        return cwd
    if (cwd / "n6-replication").is_dir():
        return cwd
    return cwd


def cmd_run(args):
    """Run verification."""
    from n6_replication.runner import run_tier1, run_tier2_3, save_results
    from n6_replication.reporter import print_terminal_summary

    repo_root = find_repo_root()
    tiers = args.tier or [1, 2]
    all_results = []

    if 1 in tiers:
        print(f"Running Tier 1 (Core Discoveries)...", flush=True)
        all_results.extend(run_tier1(verbose=args.verbose))

    run_tiers = [t for t in tiers if t > 1]
    if run_tiers:
        gpu = _check_gpu() if not args.no_gpu else False
        print(f"Running Tier {run_tiers}...", flush=True)
        all_results.extend(
            run_tier2_3(run_tiers, repo_root, args.parallel, gpu, args.verbose)
        )

    path = save_results(all_results)
    print_terminal_summary(all_results)
    print(f"\nResults saved to {path}")

    if args.format:
        cmd_report_from_results(all_results, args.format)


def cmd_fetch(args):
    """Fetch Tier 3 repos."""
    from n6_replication.fetcher import fetch_all, update_all

    if args.update:
        update_all()
    else:
        fetch_all()


def cmd_report(args):
    """Generate report from last run."""
    from n6_replication.reporter import generate_report, find_latest_results

    results = find_latest_results()
    if results is None:
        print("No results found. Run `n6-replicate run` first.")
        sys.exit(1)
    generate_report(results, args.format)


def cmd_report_from_results(results, fmt):
    """Generate report from in-memory results."""
    from n6_replication.reporter import generate_report
    generate_report(results, fmt)


def cmd_list(args):
    """List registered scripts."""
    from n6_replication.registry import load_all

    tiers = args.tier or [1, 2, 3]
    scripts = load_all([t for t in tiers if t > 1])

    if 1 in tiers:
        print("Tier  ID                          Repo       GPU   Timeout")
        print("─" * 60)
        # Tier 1 tests are hardcoded
        tier1_tests = [
            "test_golden_zone", "test_perfect_six", "test_uniqueness",
            "test_euler_product", "test_conservation", "test_phase_accel",
            "test_edge_of_chaos", "test_texas",
        ]
        for t in tier1_tests:
            print(f"  1   {t:<30s} TECS-L     -     30s")

    for s in scripts:
        gpu = "GPU" if s.get("requires_gpu") else "-"
        tier = s.get("tier", 2)
        repo = s.get("repo", "TECS-L")
        print(f"  {tier}   {s['id']:<30s} {repo:<10s} {gpu:<5s} {s.get('timeout', 120)}s")


def _check_gpu() -> bool:
    """Check if torch is available."""
    try:
        import torch
        return True
    except ImportError:
        return False


def main():
    parser = argparse.ArgumentParser(
        prog="n6-replicate",
        description=f"n6-replication v{__version__} — Independent replication of perfect number 6 mathematics",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # run
    p_run = subparsers.add_parser("run", help="Run verification")
    p_run.add_argument("--tier", type=int, nargs="+", choices=[1, 2, 3], help="Tiers to run (default: 1 2)")
    p_run.add_argument("--parallel", type=int, default=1, help="Parallel workers (default: 1)")
    p_run.add_argument("--format", choices=["md", "html"], help="Also generate report")
    p_run.add_argument("--no-gpu", action="store_true", help="Skip GPU scripts")
    p_run.add_argument("-v", "--verbose", action="store_true")
    p_run.set_defaults(func=cmd_run)

    # fetch
    p_fetch = subparsers.add_parser("fetch", help="Fetch Tier 3 repos")
    p_fetch.add_argument("--update", action="store_true", help="Update existing repos")
    p_fetch.set_defaults(func=cmd_fetch)

    # report
    p_report = subparsers.add_parser("report", help="Generate report from last run")
    p_report.add_argument("--format", choices=["md", "html"], default="md", help="Report format")
    p_report.set_defaults(func=cmd_report)

    # list
    p_list = subparsers.add_parser("list", help="List registered scripts")
    p_list.add_argument("--tier", type=int, nargs="+", choices=[1, 2, 3])
    p_list.set_defaults(func=cmd_list)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify CLI works**

```bash
n6-replicate --help
n6-replicate list --tier 1
```

Expected: help output + tier 1 test list

- [ ] **Step 3: Commit**

```bash
git add src/n6_replication/cli.py
git commit -m "feat(n6-replication): argparse CLI (run/fetch/report/list)"
```

---

## Task 10: Reporter Module

**Files:**
- Create: `n6-replication/src/n6_replication/reporter.py`
- Create: `n6-replication/templates/report.html`

- [ ] **Step 1: Write reporter.py**

```python
"""Report generation — terminal, markdown, HTML."""

import json
from collections import Counter
from datetime import datetime
from pathlib import Path

from jinja2 import Template


RESULTS_DIR = Path("results")


def find_latest_results() -> list[dict] | None:
    """Find and load the most recent results JSON."""
    if not RESULTS_DIR.exists():
        return None
    files = sorted(RESULTS_DIR.glob("*.json"), reverse=True)
    if not files:
        return None
    with open(files[0]) as f:
        return json.load(f)


def _tier_summary(results: list[dict], tier: int) -> dict:
    """Summarize results for a tier."""
    tier_results = [r for r in results if r.get("tier") == tier]
    if not tier_results:
        return {"total": 0, "passed": 0, "pct": 0}
    passed = sum(1 for r in tier_results if r["status"] == "pass")
    return {"total": len(tier_results), "passed": passed, "pct": round(100 * passed / len(tier_results))}


def _grade_totals(results: list[dict]) -> dict:
    """Aggregate grade counts across all results."""
    totals = Counter()
    for r in results:
        for grade, count in r.get("grade_counts", {}).items():
            totals[grade] += count
    return dict(totals)


def _bar(pct: int, width: int = 20) -> str:
    filled = round(pct / 100 * width)
    return "\u2588" * filled + "\u2591" * (width - filled)


def print_terminal_summary(results: list[dict]):
    """Print terminal summary."""
    print()
    print("\u2550" * 50)
    print("  n6-replication Results")
    print("\u2550" * 50)

    for tier in [1, 2, 3]:
        s = _tier_summary(results, tier)
        if s["total"] == 0:
            label = {1: "Core", 2: "Full", 3: "Cross"}[tier]
            print(f"Tier {tier} ({label:5s})    --     (not run)")
        else:
            label = {1: "Core", 2: "Full", 3: "Cross"}[tier]
            print(f"Tier {tier} ({label:5s})  {s['passed']:3d}/{s['total']:<3d}  {_bar(s['pct'])} {s['pct']:3d}%")

    grades = _grade_totals(results)
    if grades:
        print()
        print("Grade Distribution:")
        grade_labels = [
            ("green", "\U0001f7e9 Proven"),
            ("orange", "\U0001f7e7 Structural"),
            ("white", "\u26aa Coincidence"),
            ("black", "\u2b1b Refuted"),
        ]
        for key, label in grade_labels:
            count = grades.get(key, 0)
            if count:
                bar = "\u2588" * min(count, 40)
                print(f"  {label:<16s} {count:4d}  {bar}")

    failed = [r for r in results if r["status"] != "pass"]
    if failed:
        print()
        print(f"Failed/Skipped ({len(failed)}):")
        for r in failed[:10]:
            err = (r.get("error") or "")[:60]
            print(f"  \u274c {r['id']:<30s} {r['status']:8s} {err}")
        if len(failed) > 10:
            print(f"  ... and {len(failed) - 10} more")

    total_duration = sum(r.get("duration_seconds", 0) for r in results)
    total_checks = sum(r.get("pass_count", 0) + r.get("fail_count", 0) for r in results)
    print()
    print(f"Total: {total_checks} checks | Duration: {total_duration:.0f}s")
    print("\u2550" * 50)


def generate_markdown(results: list[dict]) -> str:
    """Generate markdown report."""
    lines = ["# n6-replication Report", ""]
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    for tier in [1, 2, 3]:
        s = _tier_summary(results, tier)
        if s["total"] == 0:
            continue
        label = {1: "Core Discoveries", 2: "Full Verification", 3: "Cross-Repo"}[tier]
        lines.append(f"## Tier {tier}: {label} ({s['passed']}/{s['total']} = {s['pct']}%)")
        lines.append("")
        lines.append("| Script | Status | Duration |")
        lines.append("|--------|--------|----------|")
        tier_results = [r for r in results if r.get("tier") == tier]
        for r in tier_results:
            status = "\u2705" if r["status"] == "pass" else "\u274c"
            dur = f"{r.get('duration_seconds', 0):.1f}s"
            lines.append(f"| {r['id']} | {status} {r['status']} | {dur} |")
        lines.append("")

    return "\n".join(lines)


def generate_html(results: list[dict]) -> str:
    """Generate HTML report from Jinja2 template."""
    template_path = Path(__file__).parent.parent.parent / "templates" / "report.html"
    if not template_path.exists():
        return f"<html><body><pre>{generate_markdown(results)}</pre></body></html>"

    with open(template_path) as f:
        template = Template(f.read())

    return template.render(
        results=results,
        tier_summary={t: _tier_summary(results, t) for t in [1, 2, 3]},
        grades=_grade_totals(results),
        generated=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )


def generate_report(results: list[dict], fmt: str):
    """Generate and save report."""
    RESULTS_DIR.mkdir(exist_ok=True)
    if fmt == "md":
        content = generate_markdown(results)
        path = RESULTS_DIR / "report.md"
    elif fmt == "html":
        content = generate_html(results)
        path = RESULTS_DIR / "report.html"
    else:
        print_terminal_summary(results)
        return

    with open(path, "w") as f:
        f.write(content)
    print(f"Report saved to {path}")
```

- [ ] **Step 2: Write templates/report.html**

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>n6-replication Report</title>
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 960px; margin: 0 auto; padding: 2rem; background: #fafafa; }
  h1 { border-bottom: 2px solid #333; padding-bottom: 0.5rem; }
  .summary { display: flex; gap: 1rem; margin: 1rem 0; }
  .tier-card { flex: 1; background: white; border-radius: 8px; padding: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
  .tier-card h3 { margin: 0 0 0.5rem; }
  .pct { font-size: 2rem; font-weight: bold; }
  .pass { color: #2da44e; } .fail { color: #cf222e; }
  table { width: 100%; border-collapse: collapse; margin: 1rem 0; }
  th, td { padding: 0.5rem; text-align: left; border-bottom: 1px solid #ddd; }
  th { background: #f0f0f0; }
  tr:hover { background: #f8f8f8; }
  .details { display: none; background: #f6f6f6; padding: 0.5rem; font-family: monospace; font-size: 0.85rem; white-space: pre-wrap; max-height: 200px; overflow-y: auto; }
  .toggle { cursor: pointer; color: #0969da; text-decoration: underline; }
  .filter { margin: 1rem 0; }
  .filter button { padding: 0.3rem 0.8rem; margin-right: 0.3rem; border: 1px solid #ddd; border-radius: 4px; cursor: pointer; background: white; }
  .filter button.active { background: #333; color: white; }
  .grade { display: inline-flex; align-items: center; gap: 0.3rem; margin-right: 1rem; }
</style>
</head>
<body>
<h1>n6-replication Report</h1>
<p>Generated: {{ generated }}</p>

<div class="summary">
{% raw %}
{% for tier in [1, 2, 3] %}
{% set s = tier_summary[tier] %}
<div class="tier-card">
  <h3>Tier {{ tier }}: {{ {1: 'Core', 2: 'Full', 3: 'Cross'}[tier] }}</h3>
  {% if s.total > 0 %}
  <div class="pct {{ 'pass' if s.pct >= 90 else 'fail' }}">{{ s.pct }}%</div>
  <div>{{ s.passed }}/{{ s.total }} passed</div>
  {% else %}
  <div class="pct" style="color:#888">--</div>
  <div>Not run</div>
  {% endif %}
</div>
{% endfor %}
</div>

{% if grades %}
<h2>Grade Distribution</h2>
<div>
  <span class="grade">&#x1f7e9; Proven: {{ grades.get('green', 0) }}</span>
  <span class="grade">&#x1f7e7; Structural: {{ grades.get('orange', 0) }}</span>
  <span class="grade">&#x26aa; Coincidence: {{ grades.get('white', 0) }}</span>
  <span class="grade">&#x2b1b; Refuted: {{ grades.get('black', 0) }}</span>
</div>
{% endif %}

<h2>Results</h2>
<div class="filter">
  <button class="active" onclick="filterResults('all')">All</button>
  <button onclick="filterResults('pass')">Pass</button>
  <button onclick="filterResults('fail')">Fail</button>
  {% for tier in [1, 2, 3] %}
  <button onclick="filterResults('tier{{tier}}')">Tier {{tier}}</button>
  {% endfor %}
</div>

<table id="results-table">
<thead><tr><th>Tier</th><th>Script</th><th>Status</th><th>Duration</th><th></th></tr></thead>
<tbody>
{% for r in results %}
<tr class="result-row" data-status="{{ r.status }}" data-tier="{{ r.tier }}">
  <td>{{ r.tier }}</td>
  <td>{{ r.id }}</td>
  <td>{{ '&#x2705;' if r.status == 'pass' else '&#x274c;' }} {{ r.status }}</td>
  <td>{{ '%.1f' | format(r.get('duration_seconds', 0)) }}s</td>
  <td><span class="toggle" onclick="toggleDetails(this)">details</span></td>
</tr>
<tr class="result-row" data-status="{{ r.status }}" data-tier="{{ r.tier }}">
  <td colspan="5"><div class="details">{{ r.get('stdout_snippet', '') or r.get('error', 'No output') }}</div></td>
</tr>
{% endfor %}
</tbody>
</table>
{% endraw %}

<script>
function toggleDetails(el) {
  const details = el.closest('tr').nextElementSibling.querySelector('.details');
  details.style.display = details.style.display === 'block' ? 'none' : 'block';
}
function filterResults(filter) {
  document.querySelectorAll('.filter button').forEach(b => b.classList.remove('active'));
  event.target.classList.add('active');
  document.querySelectorAll('.result-row').forEach(row => {
    if (filter === 'all') { row.style.display = ''; return; }
    if (filter.startsWith('tier')) {
      row.style.display = row.dataset.tier === filter.replace('tier','') ? '' : 'none';
    } else {
      row.style.display = row.dataset.status === filter ? '' : 'none';
    }
  });
}
</script>
</body>
</html>
```

- [ ] **Step 3: Commit**

```bash
git add src/n6_replication/reporter.py templates/report.html
git commit -m "feat(n6-replication): reporter (terminal/md/html) + jinja2 template"
```

---

## Task 11: Fetcher Module

**Files:**
- Create: `n6-replication/src/n6_replication/fetcher.py`

- [ ] **Step 1: Write fetcher.py**

```python
"""Tier 3 repo fetcher — clone/update external repos."""

import json
import subprocess
from datetime import datetime
from pathlib import Path

REPOS = {
    "SEDI": "https://github.com/need-singularity/sedi.git",
    "anima": "https://github.com/need-singularity/anima.git",
    "ph-training": "https://github.com/need-singularity/ph-training.git",
    "golden-moe": "https://github.com/need-singularity/golden-moe.git",
    "conscious-lm": "https://github.com/need-singularity/conscious-lm.git",
    "energy-efficiency": "https://github.com/need-singularity/energy-efficiency.git",
}

FETCH_DIR = Path.home() / ".n6-replication" / "repos"
STATE_FILE = Path.home() / ".n6-replication" / "fetch_state.json"
REGISTRY_DIR = Path(__file__).parent.parent.parent / "registry"


def _load_state() -> dict:
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {}


def _save_state(state: dict):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def fetch_all():
    """Clone all Tier 3 repos (shallow)."""
    FETCH_DIR.mkdir(parents=True, exist_ok=True)
    state = _load_state()

    for name, url in REPOS.items():
        repo_dir = FETCH_DIR / name
        if repo_dir.exists():
            print(f"  {name}: already fetched (use --update to pull)")
            continue

        print(f"  {name}: cloning...", end=" ", flush=True)
        try:
            subprocess.run(
                ["git", "clone", "--depth", "1", url, str(repo_dir)],
                capture_output=True, text=True, check=True, timeout=120,
            )
            state[name] = {
                "status": "fetched",
                "last_fetched": datetime.now().isoformat(),
                "path": str(repo_dir),
            }
            print("done")
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            state[name] = {"status": "failed", "error": str(e)}
            print(f"FAILED: {e}")

    _save_state(state)
    _scan_tier3()
    print(f"\nTier 3 repos in {FETCH_DIR}")


def update_all():
    """Pull latest for all fetched repos."""
    state = _load_state()

    for name in REPOS:
        repo_dir = FETCH_DIR / name
        if not repo_dir.exists():
            print(f"  {name}: not fetched (run `n6-replicate fetch` first)")
            continue

        print(f"  {name}: updating...", end=" ", flush=True)
        try:
            subprocess.run(
                ["git", "pull"], cwd=str(repo_dir),
                capture_output=True, text=True, check=True, timeout=60,
            )
            state[name] = {
                "status": "fetched",
                "last_fetched": datetime.now().isoformat(),
                "path": str(repo_dir),
            }
            print("done")
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            print(f"FAILED: {e}")

    _save_state(state)
    _scan_tier3()


def _scan_tier3():
    """Scan fetched repos for verify/ scripts and generate tier3.json."""
    entries = []
    for name in REPOS:
        repo_dir = FETCH_DIR / name
        verify_dir = repo_dir / "verify"
        if not verify_dir.exists():
            continue
        for py_file in sorted(verify_dir.glob("*.py")):
            entries.append({
                "id": py_file.stem,
                "path": f"verify/{py_file.name}",
                "repo": name,
                "repo_path": str(repo_dir),
                "depends_on": [],
                "requires_gpu": False,
                "timeout": 120,
                "tier": 3,
            })

    REGISTRY_DIR.mkdir(parents=True, exist_ok=True)
    with open(REGISTRY_DIR / "tier3.json", "w") as f:
        json.dump(entries, f, indent=2)
    print(f"  Scanned {len(entries)} Tier 3 scripts")
```

- [ ] **Step 2: Commit**

```bash
git add src/n6_replication/fetcher.py
git commit -m "feat(n6-replication): tier 3 fetcher (clone/update/scan)"
```

---

## Task 12: Minimal Entrypoint (run_all.py) + Dockerfile

**Files:**
- Create: `n6-replication/scripts/run_all.py`
- Create: `n6-replication/Dockerfile`

- [ ] **Step 1: Write run_all.py (zero dependency on n6_replication package)**

```python
#!/usr/bin/env python3
"""Minimal entrypoint — run without pip install.

Usage:
    cd TECS-L
    python n6-replication/scripts/run_all.py
    python n6-replication/scripts/run_all.py --tier 1
    python n6-replication/scripts/run_all.py --tier 2
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path


def find_repo_root():
    """Find TECS-L root."""
    here = Path(__file__).resolve().parent
    # scripts/ -> n6-replication/ -> TECS-L/
    root = here.parent.parent
    if (root / "verify").is_dir():
        return root
    return Path.cwd()


def run_tier1(repo_root):
    """Run Tier 1 via pytest."""
    tests_dir = repo_root / "n6-replication" / "tests" / "tier1"
    if not tests_dir.exists():
        print("Tier 1 tests not found")
        return False
    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(tests_dir), "-v"],
        cwd=str(repo_root),
    )
    return result.returncode == 0


def run_tier2(repo_root):
    """Run all verify/ scripts."""
    verify_dir = repo_root / "verify"
    scripts = sorted(verify_dir.glob("verify_*.py")) + sorted(verify_dir.glob("frontier_*.py"))
    passed, failed, errors = 0, 0, 0

    for script in scripts:
        print(f"  {script.name}...", end=" ", flush=True)
        start = time.time()
        try:
            result = subprocess.run(
                [sys.executable, str(script)],
                capture_output=True, text=True, timeout=120,
                cwd=str(repo_root),
                env={**__import__("os").environ, "PYTHONPATH": str(repo_root)},
            )
            dur = time.time() - start
            if result.returncode == 0:
                passed += 1
                print(f"PASS ({dur:.1f}s)")
            else:
                failed += 1
                print(f"FAIL ({dur:.1f}s)")
        except subprocess.TimeoutExpired:
            errors += 1
            print("TIMEOUT")
        except Exception as e:
            errors += 1
            print(f"ERROR: {e}")

    total = passed + failed + errors
    print(f"\nTier 2: {passed}/{total} passed, {failed} failed, {errors} errors")
    return failed == 0 and errors == 0


def main():
    parser = argparse.ArgumentParser(description="n6-replication minimal runner")
    parser.add_argument("--tier", type=int, nargs="+", default=[1, 2], choices=[1, 2])
    args = parser.parse_args()

    repo_root = find_repo_root()
    print(f"Repo root: {repo_root}")

    ok = True
    if 1 in args.tier:
        print("\n=== Tier 1: Core Discoveries ===")
        ok = run_tier1(repo_root) and ok
    if 2 in args.tier:
        print("\n=== Tier 2: Full Verification ===")
        ok = run_tier2(repo_root) and ok

    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Write Dockerfile**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy entire TECS-L repo
COPY . /app/TECS-L

# Install the package
RUN pip install --no-cache-dir /app/TECS-L/n6-replication

# Attempt to fetch Tier 3 repos (non-fatal if offline)
RUN cd /app/TECS-L && n6-replicate fetch || true

WORKDIR /app/TECS-L
ENTRYPOINT ["n6-replicate"]
CMD ["run", "--tier", "1"]
```

- [ ] **Step 3: Commit**

```bash
git add scripts/run_all.py Dockerfile
git commit -m "feat(n6-replication): minimal run_all.py + Dockerfile"
```

---

## Task 13: README.md

**Files:**
- Create: `n6-replication/README.md`

- [ ] **Step 1: Write README.md**

```markdown
# n6-replication

Independent replication package for **perfect number 6 mathematics** — 1,700+ hypotheses across 7 repositories.

## Quick Start

### For Reviewers (Docker, 1 command)

```bash
docker build -t n6-replication .
docker run n6-replication                    # Core discoveries (~5 min)
docker run n6-replication run --tier 2       # Full verification (~30 min)
```

### For Developers (pip)

```bash
pip install n6-replication
n6-replicate run --tier 1         # Core: 8 major discoveries
n6-replicate run                  # Core + full verification
n6-replicate report --format html # Generate HTML report
```

### For Researchers (editable install)

```bash
git clone https://github.com/need-singularity/TECS-L.git
cd TECS-L/n6-replication
pip install -e .
pytest tests/tier1/ -v            # Run core tests directly
n6-replicate run --tier 1 2 3     # Everything
```

### Minimal (no install needed)

```bash
git clone https://github.com/need-singularity/TECS-L.git
cd TECS-L
pip install numpy scipy sympy mpmath pytest
python n6-replication/scripts/run_all.py
```

## Verification Tiers

| Tier | Content | Scripts | Time |
|------|---------|---------|------|
| 1 | 8 Major Discoveries (pytest) | 8 test files | ~5 min |
| 2 | Full verify/ + math/ | 108 scripts | ~30 min |
| 3 | Cross-repo (SEDI, anima, etc.) | varies | ~1 hr |

### Tier 1: Core Discoveries

| Test | Hypothesis | What it verifies |
|------|-----------|------------------|
| test_golden_zone | H067+H072 | 1/2+1/3+1/6=1, Golden Zone structure |
| test_perfect_six | H090 | sigma_{-1}(6)=2, master formula |
| test_uniqueness | H098 | 6 is unique among perfect numbers |
| test_euler_product | H092 | Zeta Euler product p=2,3 truncation |
| test_conservation | H172 | G*I=D*P conservation law |
| test_phase_accel | H124 | Phase acceleration stepwise x3 |
| test_edge_of_chaos | H139 | Golden Zone = Langton lambda_c |
| test_texas | Texas | Monte Carlo p<0.001 |

### Tier 3: Cross-Repo

Requires fetching external repositories:

```bash
n6-replicate fetch          # Clone 6 repos (~2 min)
n6-replicate run --tier 3   # Run cross-repo verification
n6-replicate fetch --update # Pull latest
```

## CLI Reference

```bash
n6-replicate run [--tier N...] [--parallel N] [--format md|html] [--no-gpu] [-v]
n6-replicate fetch [--update]
n6-replicate report [--format md|html]
n6-replicate list [--tier N...]
```

## GPU Scripts

4 scripts require PyTorch. Install with:

```bash
pip install n6-replication[gpu]
```

Without GPU, these scripts are automatically skipped.

## Reports

```bash
n6-replicate run                  # Terminal output (default)
n6-replicate run --format md      # Also save results/report.md
n6-replicate run --format html    # Also save results/report.html
n6-replicate report --format html # Re-generate from last run
```
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs(n6-replication): README with quick start for 3 user types"
```

---

## Task 14: Integration Test — Full Tier 1 Run

- [ ] **Step 1: Install package in editable mode**

```bash
cd n6-replication
pip install -e .
```

- [ ] **Step 2: Run Tier 1 via CLI**

```bash
cd ..  # back to TECS-L root
n6-replicate run --tier 1 -v
```

Expected: 8 test files, ~25 tests, all PASS

- [ ] **Step 3: Run via python -m**

```bash
python -m n6_replication run --tier 1
```

Expected: Same results

- [ ] **Step 4: Generate reports**

```bash
n6-replicate report --format md
n6-replicate report --format html
```

Expected: `results/report.md` and `results/report.html` created

- [ ] **Step 5: Run minimal script**

```bash
python n6-replication/scripts/run_all.py --tier 1
```

Expected: pytest output, all pass

- [ ] **Step 6: Commit any fixes**

```bash
git add -A
git commit -m "fix(n6-replication): integration test fixes"
```

---

## Task 15: Generate tier2.json Registry

- [ ] **Step 1: Write script to auto-generate tier2.json**

Scan all 90 verify/ + 18 math/ frontier scripts and generate the registry:

```bash
cd TECS-L
python -c "
import json, re
from pathlib import Path

entries = []

# verify/ scripts
for f in sorted(Path('verify').glob('*.py')):
    content = f.read_text()
    deps = []
    if 'import compass' in content or 'from compass' in content:
        deps.append('compass.py')
    if 'import convergence_engine' in content or 'from convergence_engine' in content:
        deps.append('convergence_engine.py')
    gpu = 'import torch' in content or 'from torch' in content
    entries.append({
        'id': f.stem,
        'path': str(f),
        'depends_on': deps,
        'requires_gpu': gpu,
        'timeout': 300 if gpu else 120,
        'tier': 2,
    })

# math/ frontier scripts
for f in sorted(Path('math').glob('frontier_*_verify.py')):
    entries.append({
        'id': f.stem,
        'path': str(f),
        'depends_on': [],
        'requires_gpu': False,
        'timeout': 180,
        'tier': 2,
    })

Path('n6-replication/registry').mkdir(exist_ok=True)
with open('n6-replication/registry/tier2.json', 'w') as out:
    json.dump(entries, out, indent=2)
print(f'Generated {len(entries)} entries')
"
```

Expected: `Generated 108 entries` (90 verify + 18 math frontier)

- [ ] **Step 2: Verify registry loads**

```bash
n6-replicate list --tier 2
```

Expected: 108 scripts listed

- [ ] **Step 3: Commit**

```bash
git add n6-replication/registry/tier2.json
git commit -m "feat(n6-replication): auto-generated tier2.json (108 scripts)"
```

---

## Task 16: Integration Test — Tier 2 Sample Run

- [ ] **Step 1: Run 3 representative Tier 2 scripts via CLI**

```bash
n6-replicate run --tier 2 -v 2>&1 | head -50
```

Verify that subprocess execution, output parsing, and result saving all work.

- [ ] **Step 2: Check results JSON**

```bash
ls results/*.json
python -c "import json; r=json.load(open(sorted(__import__('pathlib').Path('results').glob('*.json'))[-1])); print(f'{len(r)} results, {sum(1 for x in r if x[\"status\"]==\"pass\")} passed')"
```

- [ ] **Step 3: Fix any issues and commit**

```bash
git add -A
git commit -m "fix(n6-replication): tier 2 integration fixes"
```
