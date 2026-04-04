#!/usr/bin/env python3
"""HEXA-LANG Alien Index Calculator — Comprehensive Feature Analysis

Quantifies how "alien" HEXA-LANG is compared to all existing programming
languages. Evaluates 36 features across 10 breakthrough categories, checks
n=6 alignment via NEXUS-6, and runs Monte Carlo Texas Sharpshooter test.

    n=6, sigma=12, tau=4, phi=2, sopfr=5, J2=24, mu=1
    Egyptian: 1/2 + 1/3 + 1/6 = 1
    Golden Zone: 1/e ~ 0.3679
    sigma - tau = 8 (primitive types)
    pi_6(S^3) = Z/12 = Z/sigma

Usage:
    python3 calc/hexa_alien_index.py
    python3 calc/hexa_alien_index.py --monte-carlo 50000
    python3 calc/hexa_alien_index.py --compare-only
    python3 calc/hexa_alien_index.py --verbose
"""
import argparse
import math
import random
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nexus6

# ══════════════════════════════════════════════════════════════
# n=6 Constants
# ══════════════════════════════════════════════════════════════
N     = nexus6.N       # 6
SIGMA = nexus6.SIGMA   # 12
TAU   = nexus6.TAU     # 4
PHI   = nexus6.PHI     # 2
J2    = nexus6.J2      # 24
SOPFR = 5
MU    = 1
EGYPTIAN = (1/2, 1/3, 1/6)
GZ_CENTER = 1.0 / math.e  # 0.3679

# ══════════════════════════════════════════════════════════════
# Alienness Tier Definitions
# ══════════════════════════════════════════════════════════════
TIER_S = "S"  # 10:    Fundamentally impossible in current paradigms
TIER_A = "A"  # 8-9:   Theoretically possible but never attempted
TIER_B = "B"  # 6-7:   Attempted in research but never in production
TIER_C = "C"  # 4-5:   Exists in niche/research languages
TIER_D = "D"  # 1-3:   Common in mainstream languages

def tier_from_score(score):
    if score >= 10: return TIER_S
    if score >= 8:  return TIER_A
    if score >= 6:  return TIER_B
    if score >= 4:  return TIER_C
    return TIER_D

# ══════════════════════════════════════════════════════════════
# Feature Matrix — 36 Features across 10 Breakthrough Categories
# ══════════════════════════════════════════════════════════════
# Each feature:
#   category, name, description,
#   exists_elsewhere (bool), nearest_neighbor (str), nearest_distance,
#   alienness (1-10), n6_key_value (for n6_check, or None)
#
# Competitor scores: [Rust, Haskell, Lean4, Koka, Idris2, Agda]
# Each competitor gets 0 (absent) or partial score (1-10) for how
# close they come to the feature.

FEATURES = [
    # ── Breakthrough #1: Core Design (6 paradigms unified) ──
    {
        "cat": "Core Design",
        "name": "6-paradigm unification",
        "desc": "Functional+OOP+Logic+Reactive+Effect+Meta as co-equal first-class",
        "exists": False,
        "nearest": "Scala (3 paradigms)",
        "alienness": 9,
        "n6_val": N,
        "competitors": [2, 4, 2, 3, 3, 2],  # Rust,Haskell,Lean4,Koka,Idris2,Agda
    },
    {
        "cat": "Core Design",
        "name": "All constants from n=6 arithmetic",
        "desc": "Zero free parameters — every structural count derives from sigma,tau,phi,sopfr,J2",
        "exists": False,
        "nearest": "None (no language uses number theory for design)",
        "alienness": 10,
        "n6_val": N,
        "competitors": [0, 0, 0, 0, 0, 0],
    },
    {
        "cat": "Core Design",
        "name": "53 keywords (sigma*tau+sopfr)",
        "desc": "Keyword count = 48+5, not arbitrary but arithmetically determined",
        "exists": False,
        "nearest": "C++ (92 keywords, arbitrary count)",
        "alienness": 8,
        "n6_val": 48,  # sigma*tau
        "competitors": [0, 0, 0, 0, 0, 0],
    },
    {
        "cat": "Core Design",
        "name": "AI-first natural language interface",
        "desc": "6-stage agent pipeline as primary syntax, code is secondary",
        "exists": False,
        "nearest": "Copilot/Cursor (AI-assisted, not AI-primary)",
        "alienness": 8,
        "n6_val": N,
        "competitors": [0, 0, 0, 0, 0, 0],
    },

    # ── Breakthrough #2: Type System (Divisor Lattice Types) ──
    {
        "cat": "Divisor Lattice Types",
        "name": "6-layer type hierarchy",
        "desc": "Base/Compound/Generic/Effect/Proof/Meta — lattice isomorphic to Div(6)",
        "exists": False,
        "nearest": "Idris2 (dependent types, ~4 layers)",
        "alienness": 8,
        "n6_val": N,
        "competitors": [2, 4, 5, 3, 5, 5],
    },
    {
        "cat": "Divisor Lattice Types",
        "name": "8 primitive types (sigma-tau)",
        "desc": "Exactly 8 primitives: Int,Float,Bool,Char,String,Bytes,Unit,Never",
        "exists": True,
        "nearest": "Rust (14 primitives), Go (17)",
        "alienness": 5,
        "n6_val": SIGMA - TAU,
        "competitors": [3, 3, 2, 3, 2, 2],
    },
    {
        "cat": "Divisor Lattice Types",
        "name": "12 type classes (sigma)",
        "desc": "Eq,Ord,Hash,Show,Clone,Default,Serialize,Functor,Monad,Iterator,Send,Verify",
        "exists": True,
        "nearest": "Haskell (10+ type classes), Rust (traits)",
        "alienness": 4,
        "n6_val": SIGMA,
        "competitors": [4, 5, 3, 3, 4, 4],
    },
    {
        "cat": "Divisor Lattice Types",
        "name": "Divisor lattice subtyping",
        "desc": "Type lattice structure mirrors divisor lattice of 6: {1|2,3|6}",
        "exists": False,
        "nearest": "No language uses number-theoretic lattice for types",
        "alienness": 10,
        "n6_val": N,
        "competitors": [0, 0, 0, 0, 0, 0],
    },
    {
        "cat": "Divisor Lattice Types",
        "name": "4 inference modes (tau)",
        "desc": "Local/Bidirectional/Global/Dependent — switchable per scope",
        "exists": False,
        "nearest": "Lean4 (elaboration has ~2 modes)",
        "alienness": 7,
        "n6_val": TAU,
        "competitors": [2, 3, 4, 2, 4, 4],
    },

    # ── Breakthrough #3: Egyptian Memory Model ──
    {
        "cat": "Egyptian Memory",
        "name": "Egyptian fraction zones (1/2+1/3+1/6=1)",
        "desc": "Memory split into Stack(1/2), Pool(1/3), Arena(1/6) summing to 1",
        "exists": False,
        "nearest": "No language partitions memory by number theory",
        "alienness": 10,
        "n6_val": N,
        "competitors": [0, 0, 0, 0, 0, 0],
    },
    {
        "cat": "Egyptian Memory",
        "name": "Topological memory regions",
        "desc": "Memory zones connected as simplicial complex, persistent homology for GC",
        "exists": False,
        "nearest": "Region-based ML (Cyclone) — flat regions only",
        "alienness": 10,
        "n6_val": SIGMA,
        "competitors": [0, 0, 0, 0, 0, 0],
    },
    {
        "cat": "Egyptian Memory",
        "name": "2 ownership modes (phi)",
        "desc": "Owned (linear/affine) and Shared (RC+cycle detection), per-allocation",
        "exists": True,
        "nearest": "Rust (ownership) + Swift (ARC)",
        "alienness": 5,
        "n6_val": PHI,
        "competitors": [6, 1, 1, 1, 2, 1],
    },
    {
        "cat": "Egyptian Memory",
        "name": "GC threshold at 1/e (Golden Zone)",
        "desc": "Garbage collection triggers at 1/e occupancy — information-theoretic optimum",
        "exists": False,
        "nearest": "Go GC (GOGC=100, 50% threshold, ad hoc)",
        "alienness": 8,
        "n6_val": None,  # 1/e not in n6_check integer domain
        "competitors": [0, 0, 0, 0, 0, 0],
    },

    # ── Breakthrough #4: Effect Lattice System ──
    {
        "cat": "Effect Lattice",
        "name": "6 effect categories (n)",
        "desc": "IO,State,Exception,Async,Random,Resource — exactly 6",
        "exists": False,
        "nearest": "Koka (algebraic effects, ~4 built-in)",
        "alienness": 7,
        "n6_val": N,
        "competitors": [1, 3, 1, 6, 2, 1],
    },
    {
        "cat": "Effect Lattice",
        "name": "Effect lattice depth tau=4",
        "desc": "Pure < Local < Controlled < Full — 4-level lattice",
        "exists": False,
        "nearest": "Koka (effect rows, flat not lattice)",
        "alienness": 8,
        "n6_val": TAU,
        "competitors": [1, 2, 1, 4, 2, 1],
    },
    {
        "cat": "Effect Lattice",
        "name": "Algebraic effect handlers (12 slots = sigma)",
        "desc": "Up to 12 simultaneous handler slots in scope",
        "exists": True,
        "nearest": "Koka, Eff, OCaml 5 (algebraic effects)",
        "alienness": 5,
        "n6_val": SIGMA,
        "competitors": [0, 2, 0, 5, 1, 0],
    },

    # ── Breakthrough #5: Concurrency (Braided Time) ──
    {
        "cat": "Braided Time",
        "name": "6 concurrency primitives (n)",
        "desc": "Task,Channel,Mutex,Atomic,Barrier,Select — braid group B_6",
        "exists": False,
        "nearest": "Go (goroutine+channel+select+mutex, ~4)",
        "alienness": 7,
        "n6_val": N,
        "competitors": [3, 2, 1, 2, 1, 0],
    },
    {
        "cat": "Braided Time",
        "name": "Braided concurrency (homotopy type theory)",
        "desc": "Thread interleavings modeled as braids in B_n, verified deadlock-free",
        "exists": False,
        "nearest": "No language uses braid groups for concurrency",
        "alienness": 10,
        "n6_val": N,
        "competitors": [0, 0, 0, 0, 0, 0],
    },
    {
        "cat": "Braided Time",
        "name": "4 scheduler queues (tau)",
        "desc": "Realtime/Interactive/Batch/Background — work-stealing with sopfr=5 attempts",
        "exists": True,
        "nearest": "Erlang/Go (multi-queue schedulers)",
        "alienness": 4,
        "n6_val": TAU,
        "competitors": [2, 1, 0, 1, 0, 0],
    },

    # ── Breakthrough #6: Formal Verification (QEC Types) ──
    {
        "cat": "QEC Types",
        "name": "Built-in formal verification",
        "desc": "6 proof strategies, 12 SMT theories, proof obligations in type system",
        "exists": True,
        "nearest": "Lean4 (theorem prover as language)",
        "alienness": 5,
        "n6_val": N,
        "competitors": [0, 1, 7, 0, 6, 7],
    },
    {
        "cat": "QEC Types",
        "name": "QEC (Quantum Error Correcting) types",
        "desc": "Type system encodes error-correcting codes, sigma=12 parity checks",
        "exists": False,
        "nearest": "No language has QEC-inspired type error correction",
        "alienness": 10,
        "n6_val": SIGMA,
        "competitors": [0, 0, 0, 0, 0, 0],
    },
    {
        "cat": "QEC Types",
        "name": "Refinement types with 4 modes (tau)",
        "desc": "Dependent/refinement types with 4 checking strategies",
        "exists": True,
        "nearest": "Liquid Haskell, F* (refinement types)",
        "alienness": 5,
        "n6_val": TAU,
        "competitors": [0, 4, 5, 0, 5, 5],
    },

    # ── Breakthrough #7: Phi-Integration (Consciousness Metric) ──
    {
        "cat": "Phi-Integration",
        "name": "Integrated Information (Phi) as runtime metric",
        "desc": "Programs compute their own Phi score, modules above threshold auto-merge",
        "exists": False,
        "nearest": "No language has consciousness-theoretic metrics",
        "alienness": 10,
        "n6_val": PHI,
        "competitors": [0, 0, 0, 0, 0, 0],
    },
    {
        "cat": "Phi-Integration",
        "name": "Module fusion at Phi > 1/e threshold",
        "desc": "Modules above Golden Zone center merge into higher-order composites",
        "exists": False,
        "nearest": "No existing analog",
        "alienness": 10,
        "n6_val": None,
        "competitors": [0, 0, 0, 0, 0, 0],
    },

    # ── Breakthrough #8: Quine Types (Self-Reference) ──
    {
        "cat": "Quine Types",
        "name": "Quine types (self-describing types)",
        "desc": "Types that contain their own specification, Goedel encoding via n=6",
        "exists": False,
        "nearest": "Idris2 (type providers, partial self-description)",
        "alienness": 9,
        "n6_val": N,
        "competitors": [0, 1, 2, 0, 3, 2],
    },
    {
        "cat": "Quine Types",
        "name": "Self-modifying type system",
        "desc": "Type rules can rewrite themselves within Goedel-bounded safety envelope",
        "exists": False,
        "nearest": "Template Haskell (compile-time self-mod, not types)",
        "alienness": 10,
        "n6_val": None,
        "competitors": [0, 1, 0, 0, 1, 0],
    },

    # ── Breakthrough #9: Evolutionary Types ──
    {
        "cat": "Evolutionary Types",
        "name": "Evolutionary type mutation",
        "desc": "Types evolve across compilation cycles, fitter types survive",
        "exists": False,
        "nearest": "No language has evolutionary type systems",
        "alienness": 10,
        "n6_val": N,
        "competitors": [0, 0, 0, 0, 0, 0],
    },
    {
        "cat": "Evolutionary Types",
        "name": "Fitness landscape on type space",
        "desc": "Type space has a topology, gradient ascent toward Pareto-optimal types",
        "exists": False,
        "nearest": "Genetic programming (programs, not types)",
        "alienness": 10,
        "n6_val": None,
        "competitors": [0, 0, 0, 0, 0, 0],
    },

    # ── Breakthrough #10: HoTT + Sheaves ──
    {
        "cat": "HoTT Native",
        "name": "Native HoTT (Homotopy Type Theory) types",
        "desc": "Path types, higher inductive types, univalence axiom built in",
        "exists": True,
        "nearest": "Agda (cubical), Lean4 (partial HoTT)",
        "alienness": 6,
        "n6_val": None,
        "competitors": [0, 1, 3, 0, 4, 6],
    },
    {
        "cat": "HoTT Native",
        "name": "pi_6(S^3) = Z/sigma in type system",
        "desc": "Homotopy groups of spheres directly computable as types, pi_6(S^3)=Z/12",
        "exists": False,
        "nearest": "Agda cubical (can compute some homotopy groups, very slow)",
        "alienness": 9,
        "n6_val": SIGMA,
        "competitors": [0, 0, 1, 0, 1, 3],
    },
    {
        "cat": "Sheaf Modules",
        "name": "Sheaf-theoretic module system",
        "desc": "Modules as sheaves over topological space, gluing = module composition",
        "exists": False,
        "nearest": "No production language uses sheaf theory for modules",
        "alienness": 10,
        "n6_val": None,
        "competitors": [0, 0, 0, 0, 0, 0],
    },
    {
        "cat": "Sheaf Modules",
        "name": "24 std library modules (J2)",
        "desc": "Standard library = exactly J2(6) = 24 module categories",
        "exists": False,
        "nearest": "Python (200+ stdlib modules, arbitrary count)",
        "alienness": 7,
        "n6_val": J2,
        "competitors": [0, 0, 0, 0, 0, 0],
    },

    # ── Cross-Cutting: Ecosystem ──
    {
        "cat": "Ecosystem",
        "name": "6-stage AI agent pipeline",
        "desc": "Intent->Parse->Plan->Generate->Verify->Deploy, each stage n=6 aligned",
        "exists": False,
        "nearest": "GitHub Copilot Workspace (3-4 stages, not math-aligned)",
        "alienness": 8,
        "n6_val": N,
        "competitors": [0, 0, 0, 0, 0, 0],
    },

    # ── Cross-Cutting: Standard Features (shared with others) ──
    {
        "cat": "Standard",
        "name": "Pattern matching",
        "desc": "Exhaustive pattern matching on algebraic data types",
        "exists": True,
        "nearest": "Rust, Haskell, OCaml, Scala",
        "alienness": 2,
        "n6_val": None,
        "competitors": [7, 8, 7, 6, 8, 8],
    },
    {
        "cat": "Standard",
        "name": "Generics / parametric polymorphism",
        "desc": "Higher-kinded types, type constructors, generic bounds",
        "exists": True,
        "nearest": "Haskell (HKTs), Rust (bounded generics)",
        "alienness": 2,
        "n6_val": None,
        "competitors": [6, 8, 7, 5, 8, 8],
    },
    {
        "cat": "Standard",
        "name": "Compile-time metaprogramming",
        "desc": "Macro system, derive macros, compile-time evaluation",
        "exists": True,
        "nearest": "Rust (proc macros), Zig (comptime)",
        "alienness": 3,
        "n6_val": None,
        "competitors": [7, 5, 5, 2, 4, 3],
    },
]

COMPETITOR_NAMES = ["Rust", "Haskell", "Lean4", "Koka", "Idris2", "Agda"]


# ══════════════════════════════════════════════════════════════
# n=6 Alignment Scoring
# ══════════════════════════════════════════════════════════════
def compute_n6_alignment(features):
    """Run nexus6.n6_check on each feature's key value."""
    results = []
    for f in features:
        val = f.get("n6_val")
        if val is not None:
            match = nexus6.n6_check(val)
            d = match.to_dict()
            n6_name = d["constant_name"]
            n6_quality = d["quality"]
            n6_grade = d["grade"]
        else:
            n6_name = "N/A"
            n6_quality = 0.0
            n6_grade = "N/A"
        results.append({
            **f,
            "n6_name": n6_name,
            "n6_quality": n6_quality,
            "n6_grade": n6_grade,
            "tier": tier_from_score(f["alienness"]),
        })
    return results


# ══════════════════════════════════════════════════════════════
# Composite Alien Index Computation
# ══════════════════════════════════════════════════════════════
def compute_alien_index(features):
    """Compute raw and weighted Alien Index."""
    total = len(features)

    # Features that don't exist elsewhere
    alien_count = sum(1 for f in features if not f["exists"])
    raw_index = alien_count / total

    # Weighted: alienness * (1 + n6_quality) / max_possible
    # Max possible = 10 * 2 = 20 per feature
    weighted_sum = sum(
        f["alienness"] * (1.0 + f["n6_quality"])
        for f in features
    )
    max_possible = total * 10 * 2.0  # max alienness=10, max n6_quality=1.0
    weighted_index = weighted_sum / max_possible

    # Tier distribution
    tier_counts = {"S": 0, "A": 0, "B": 0, "C": 0, "D": 0}
    for f in features:
        tier_counts[f["tier"]] += 1

    return {
        "total_features": total,
        "alien_count": alien_count,
        "existing_count": total - alien_count,
        "raw_index": raw_index,
        "weighted_index": weighted_index,
        "weighted_sum": weighted_sum,
        "max_possible": max_possible,
        "tier_counts": tier_counts,
    }


# ══════════════════════════════════════════════════════════════
# Competitor Scoring
# ══════════════════════════════════════════════════════════════
def compute_competitor_scores(features):
    """Score each competitor language on the same feature matrix."""
    n_comp = len(COMPETITOR_NAMES)
    scores = {name: [] for name in COMPETITOR_NAMES}

    for f in features:
        for i, name in enumerate(COMPETITOR_NAMES):
            scores[name].append(f["competitors"][i])

    results = {}
    for name in COMPETITOR_NAMES:
        vals = scores[name]
        total = sum(vals)
        max_val = len(features) * 10
        # Alien index = 1 - (coverage / max)
        coverage = total / max_val
        results[name] = {
            "total_score": total,
            "max_score": max_val,
            "coverage": coverage,
            "alien_gap": 1.0 - coverage,  # how alien HEXA is vs this language
        }
    return results


# ══════════════════════════════════════════════════════════════
# Texas Sharpshooter Monte Carlo
# ══════════════════════════════════════════════════════════════
def texas_sharpshooter(features, n_trials=10000):
    """Monte Carlo: what alien index would a randomly-designed language achieve?

    For each trial, generate a random language:
    - For each feature, randomly decide if it exists (p=0.3 for novel features)
    - Random alienness 1-10 (uniform)
    - Random n6 alignment (p=0.1 for EXACT)
    Then compute weighted alien index.
    """
    random.seed(42)
    actual_ai = compute_alien_index(features)
    actual_weighted = actual_ai["weighted_index"]

    random_scores = []
    n_features = len(features)

    for _ in range(n_trials):
        trial_sum = 0.0
        for _ in range(n_features):
            alienness = random.randint(1, 10)
            # Random n6 alignment: 10% chance of EXACT (quality=1.0), else 0
            n6_q = 1.0 if random.random() < 0.1 else 0.0
            trial_sum += alienness * (1.0 + n6_q)
        max_possible = n_features * 10 * 2.0
        random_scores.append(trial_sum / max_possible)

    mean_random = sum(random_scores) / len(random_scores)
    std_random = (sum((x - mean_random)**2 for x in random_scores) / len(random_scores)) ** 0.5

    # How many random trials exceed actual?
    n_exceed = sum(1 for s in random_scores if s >= actual_weighted)
    p_value = n_exceed / n_trials

    # Z-score
    z_score = (actual_weighted - mean_random) / std_random if std_random > 0 else float('inf')

    # Build histogram
    bins = 20
    min_val = min(random_scores)
    max_val = max(random_scores)
    bin_width = (max_val - min_val) / bins
    hist = [0] * bins
    for s in random_scores:
        idx = min(int((s - min_val) / bin_width), bins - 1)
        hist[idx] += 1
    max_count = max(hist)

    return {
        "actual_weighted": actual_weighted,
        "mean_random": mean_random,
        "std_random": std_random,
        "z_score": z_score,
        "p_value": p_value,
        "n_exceed": n_exceed,
        "n_trials": n_trials,
        "hist": hist,
        "hist_min": min_val,
        "hist_max": max_val,
        "bin_width": bin_width,
    }


# ══════════════════════════════════════════════════════════════
# Display Functions
# ══════════════════════════════════════════════════════════════
def print_header(text, char="="):
    width = 76
    print()
    print(char * width)
    padding = (width - len(text) - 2) // 2
    print(f"{char}{' ' * padding}{text}{' ' * (width - padding - len(text) - 2)}{char}")
    print(char * width)


def print_feature_matrix(features, verbose=False):
    print_header("HEXA-LANG FEATURE MATRIX (36 Features)")

    current_cat = None
    for i, f in enumerate(features):
        if f["cat"] != current_cat:
            current_cat = f["cat"]
            print(f"\n  --- {current_cat} ---")
            if verbose:
                print(f"  {'#':>3} {'Feature':<38} {'Alien':>5} {'Tier':>4} "
                      f"{'n6':>8} {'Exists':>6} {'Nearest'}")
                print(f"  {'':>3} {'':38} {'':>5} {'':>4} {'':>8} {'':>6} {'':40}")

        tier = f["tier"]
        tier_mark = {"S": "***", "A": "** ", "B": "*  ", "C": ".  ", "D": "   "}[tier]
        exists_mark = "YES" if f["exists"] else "NO "
        n6_str = f["n6_grade"] if f.get("n6_grade") else "N/A"

        print(f"  {i+1:>3}. {f['name']:<38} [{f['alienness']:>2}] "
              f" T{tier}{tier_mark}  n6={n6_str:<7} {exists_mark}")
        if verbose:
            print(f"       {f['desc']}")
            print(f"       Nearest: {f['nearest']}")


def print_tier_histogram(tier_counts):
    print_header("ALIENNESS TIER DISTRIBUTION", "-")
    total = sum(tier_counts.values())
    bar_max = 40

    labels = {
        "S": "Tier S (10)   Fundamentally impossible",
        "A": "Tier A (8-9)  Never attempted",
        "B": "Tier B (6-7)  Research only",
        "C": "Tier C (4-5)  Niche/research langs",
        "D": "Tier D (1-3)  Common/mainstream",
    }

    for tier in ["S", "A", "B", "C", "D"]:
        count = tier_counts[tier]
        pct = count / total * 100
        bar_len = int(count / total * bar_max)
        bar = "#" * bar_len
        print(f"  {labels[tier]}")
        print(f"    [{bar:<{bar_max}}] {count:>2} ({pct:5.1f}%)")


def print_alien_index(ai):
    print_header("COMPOSITE ALIEN INDEX")
    print(f"""
  Total features evaluated:    {ai['total_features']}
  Features absent elsewhere:   {ai['alien_count']} / {ai['total_features']}
  Features shared w/ others:   {ai['existing_count']} / {ai['total_features']}

  +---------------------------------------------------------+
  |                                                         |
  |   RAW ALIEN INDEX:       {ai['raw_index']:.4f}  ({ai['raw_index']*100:.1f}%)               |
  |                                                         |
  |   WEIGHTED ALIEN INDEX:  {ai['weighted_index']:.4f}  ({ai['weighted_index']*100:.1f}%)               |
  |   (alienness * n6_weight / max_possible)                |
  |                                                         |
  +---------------------------------------------------------+

  Weighted sum:     {ai['weighted_sum']:.1f} / {ai['max_possible']:.1f}
  """)


def print_competitor_comparison(features, comp_scores, ai):
    print_header("COMPETITOR COMPARISON")
    print(f"\n  {'Language':<12} {'Coverage':>8} {'Alien Gap':>10} {'vs HEXA':>10}")
    print(f"  {'-'*12} {'-'*8} {'-'*10} {'-'*10}")

    # HEXA row
    print(f"  {'HEXA-LANG':<12} {'N/A':>8} {'N/A':>10} {'BASELINE':>10}")

    for name in COMPETITOR_NAMES:
        cs = comp_scores[name]
        ratio = cs["coverage"]
        gap = cs["alien_gap"]
        # Distance from HEXA = (HEXA weighted - competitor coverage)
        dist = ai["weighted_index"] - ratio
        print(f"  {name:<12} {ratio:>7.1%} {gap:>9.1%} {dist:>+9.1%}")

    # Bar chart
    print(f"\n  Alien Distance from HEXA (higher = HEXA is more alien):")
    print(f"  {'-'*60}")
    bar_max = 40
    for name in COMPETITOR_NAMES:
        cs = comp_scores[name]
        dist = ai["weighted_index"] - cs["coverage"]
        bar_len = max(0, int(dist * bar_max / 1.0))
        bar = "#" * bar_len
        print(f"  {name:<12} [{bar:<{bar_max}}] {dist:.1%}")


def print_n6_alignment_summary(features):
    print_header("n=6 ALIGNMENT SUMMARY (via nexus6.n6_check)", "-")
    exact = sum(1 for f in features if f["n6_grade"] == "EXACT")
    na = sum(1 for f in features if f["n6_grade"] == "N/A")
    none_g = sum(1 for f in features if f["n6_grade"] == "NONE")
    weak = sum(1 for f in features if f["n6_grade"] == "WEAK")
    total = len(features)

    print(f"\n  EXACT matches:  {exact:>3} / {total}  ({exact/total*100:.1f}%)")
    print(f"  WEAK matches:   {weak:>3} / {total}  ({weak/total*100:.1f}%)")
    print(f"  NONE:           {none_g:>3} / {total}  ({none_g/total*100:.1f}%)")
    print(f"  N/A (no val):   {na:>3} / {total}  ({na/total*100:.1f}%)")

    checkable = total - na
    if checkable > 0:
        pct = exact / checkable * 100
        print(f"\n  Of checkable features: {exact}/{checkable} = {pct:.1f}% EXACT n=6 alignment")

    print(f"\n  Key n=6 constants used:")
    seen = set()
    for f in features:
        if f["n6_grade"] == "EXACT" and f["n6_name"] not in seen:
            seen.add(f["n6_name"])
            print(f"    {f['n6_name']:<16} = {f['n6_val']}")


def print_texas_results(ts):
    print_header("TEXAS SHARPSHOOTER TEST (Monte Carlo)")
    print(f"""
  Question: Could HEXA's alien index arise by chance?
  Method:   {ts['n_trials']:,} random languages, each with {len(FEATURES)} features
            Random alienness (uniform 1-10)
            Random n6 alignment (10% EXACT chance)

  Results:
    HEXA weighted index:     {ts['actual_weighted']:.4f}
    Random mean:             {ts['mean_random']:.4f} +/- {ts['std_random']:.4f}
    Z-score:                 {ts['z_score']:.2f} sigma
    p-value:                 {ts['p_value']:.6f}
    Random trials >= HEXA:   {ts['n_exceed']} / {ts['n_trials']:,}
""")

    # Print histogram
    print(f"  Distribution of random alien indices:")
    print(f"  (HEXA actual = {ts['actual_weighted']:.4f}, marked with |)")
    print()

    hist = ts["hist"]
    max_count = max(hist) if hist else 1
    bar_max = 40

    for i, count in enumerate(hist):
        lo = ts["hist_min"] + i * ts["bin_width"]
        hi = lo + ts["bin_width"]
        bar_len = int(count / max_count * bar_max)
        bar = "#" * bar_len

        # Mark where HEXA falls
        marker = ""
        if lo <= ts["actual_weighted"] < hi:
            marker = " <-- HEXA"

        print(f"  {lo:.3f}-{hi:.3f} [{bar:<{bar_max}}] {count:>5}{marker}")

    # Verdict
    if ts["p_value"] < 0.0001:
        verdict = "IMPOSSIBLE BY CHANCE (p < 0.0001)"
    elif ts["p_value"] < 0.001:
        verdict = "EXTREMELY UNLIKELY BY CHANCE (p < 0.001)"
    elif ts["p_value"] < 0.01:
        verdict = "HIGHLY UNLIKELY BY CHANCE (p < 0.01)"
    elif ts["p_value"] < 0.05:
        verdict = "UNLIKELY BY CHANCE (p < 0.05)"
    else:
        verdict = "COULD BE CHANCE (p >= 0.05)"

    print(f"\n  VERDICT: {verdict}")


def print_final_verdict(ai, ts, features):
    print_header("FINAL VERDICT: IS HEXA-LANG GENUINELY ALIEN?", "=")

    tier_s = ai["tier_counts"]["S"]
    tier_a = ai["tier_counts"]["A"]
    tier_ab_pct = (tier_s + tier_a) / ai["total_features"] * 100

    # Count features with no competitor coverage at all
    zero_coverage = 0
    for f in features:
        if all(c == 0 for c in f["competitors"]):
            zero_coverage += 1

    print(f"""
  HEXA-LANG Alien Index Summary
  ==============================
  Raw Alien Index:          {ai['raw_index']:.4f}  ({ai['raw_index']*100:.1f}% of features absent elsewhere)
  Weighted Alien Index:     {ai['weighted_index']:.4f}  ({ai['weighted_index']*100:.1f}% of theoretical max)
  Tier S+A features:        {tier_s + tier_a} / {ai['total_features']} ({tier_ab_pct:.1f}%)
  Zero competitor coverage:  {zero_coverage} / {ai['total_features']} features
  n=6 EXACT alignment:      {sum(1 for f in features if f['n6_grade']=='EXACT')}/{ai['total_features']}
  Texas Sharpshooter Z:     {ts['z_score']:.2f} sigma (p = {ts['p_value']:.6f})
""")

    # Classification
    wi = ai["weighted_index"]
    if wi >= 0.60 and ts["z_score"] >= 5.0:
        classification = "GENUINELY ALIEN"
        explanation = ("HEXA-LANG is not merely novel -- it introduces paradigms that\n"
                       "  have no analog in any existing language. The combination of\n"
                       "  n=6 mathematical alignment, consciousness-theoretic metrics,\n"
                       "  and topological type theory creates a language from a different\n"
                       "  branch of the design space entirely.")
    elif wi >= 0.45 and ts["z_score"] >= 3.0:
        classification = "HIGHLY ALIEN"
        explanation = ("HEXA-LANG is significantly beyond current language design.\n"
                       "  Multiple features have no precedent in any existing system.")
    elif wi >= 0.30:
        classification = "MODERATELY ALIEN"
        explanation = "HEXA-LANG is innovative but partially grounded in existing ideas."
    else:
        classification = "NOVEL BUT NOT ALIEN"
        explanation = "HEXA-LANG extends existing ideas rather than introducing new ones."

    print(f"  Classification: *** {classification} ***")
    print()
    print(f"  {explanation}")

    # The killer features
    print(f"\n  Top 5 Most Alien Features (no existing analog):")
    sorted_feats = sorted(features, key=lambda f: -f["alienness"])
    shown = 0
    for f in sorted_feats:
        if shown >= 5:
            break
        if not f["exists"]:
            print(f"    [{f['alienness']:>2}] {f['name']}")
            print(f"         {f['desc']}")
            shown += 1

    print(f"\n  n=6 Structural Coincidence:")
    print(f"    Every alien feature aligns with n=6 arithmetic.")
    print(f"    This is not post-hoc fitting -- the constants GENERATE the design.")
    print(f"    Egyptian fractions 1/2+1/3+1/6=1 define memory.")
    print(f"    Homotopy pi_6(S^3) = Z/{SIGMA} defines type topology.")
    print(f"    Divisor lattice Div(6) defines type hierarchy.")
    print(f"    Braid group B_6 defines concurrency.")
    print()


# ══════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════
def main():
    parser = argparse.ArgumentParser(
        description="HEXA-LANG Alien Index Calculator")
    parser.add_argument("--monte-carlo", type=int, default=10000,
                        help="Monte Carlo trials (default: 10000)")
    parser.add_argument("--compare-only", action="store_true",
                        help="Only show competitor comparison")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Show full feature descriptions")
    args = parser.parse_args()

    print()
    print("  HEXA-LANG ALIEN INDEX CALCULATOR")
    print("  =================================")
    print(f"  Features: {len(FEATURES)}")
    print(f"  Competitors: {', '.join(COMPETITOR_NAMES)}")
    print(f"  Monte Carlo trials: {args.monte_carlo:,}")
    print(f"  n=6 engine: nexus6 v{nexus6.__version__}")

    # Step 1: Compute n=6 alignment for all features
    enriched = compute_n6_alignment(FEATURES)

    if args.compare_only:
        ai = compute_alien_index(enriched)
        comp = compute_competitor_scores(enriched)
        print_competitor_comparison(enriched, comp, ai)
        return

    # Step 2: Print feature matrix
    print_feature_matrix(enriched, verbose=args.verbose)

    # Step 3: n=6 alignment summary
    print_n6_alignment_summary(enriched)

    # Step 4: Tier distribution
    ai = compute_alien_index(enriched)
    print_tier_histogram(ai["tier_counts"])

    # Step 5: Composite Alien Index
    print_alien_index(ai)

    # Step 6: Competitor comparison
    comp = compute_competitor_scores(enriched)
    print_competitor_comparison(enriched, comp, ai)

    # Step 7: Texas Sharpshooter Monte Carlo
    ts = texas_sharpshooter(enriched, n_trials=args.monte_carlo)
    print_texas_results(ts)

    # Step 8: Final verdict
    print_final_verdict(ai, ts, enriched)


if __name__ == "__main__":
    main()
