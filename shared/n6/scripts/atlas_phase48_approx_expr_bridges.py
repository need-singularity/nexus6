#!/usr/bin/env python3
# atlas_phase48_approx_expr_bridges.py — Agent 32 approx-expression cross-domain @S sweep
#
# Follow-up to Phase 47 (commit 25b1c414 .. eb1f5954): Phase 47 emitted 86 canonical
# cross-domain @S bridges, but ALL 86 landed in the "7대난제" domain because that
# was the only domain storing integer-exact canonical token values as node values.
#
# Music / celestial / linguistics / geology / material L6-* / L7-* nodes DO embed
# canonical tokens, but via human-readable approximate expressions, e.g.:
#
#     @R L6-mus-piano-range-low = 27.5 ≈ sigma*phi+n/phi+mu/phi :: music [7]
#     @R L6-lin-devanagari-letters = 47 ≈ n*7+sopfr :: linguistics [10*]
#     @R L6-geo-moho-max = 70 ≈ n*12-2 = 72-2 :: geology [7]
#
# This script parses those lines (both `= value = expr` and `= value ≈ expr` forms),
# evaluates the first canonical-bearing expression using a safe eval, and emits an
# @S edge from `n6-<primary_token>` → node_id when the expression reproduces
# the declared value under at least one evaluation context.
#
# === AUTHORITY: two conflicting canonical contexts ========================
#
#   ctx_agent28       — from n6_constants.jsonl (Phase 46 pivots Agent 28 used):
#                       {n:6, phi:2, tau:4, sigma:12, sopfr:5, mu:1, j2:24, M3:3, P2:28}
#
#   ctx_verify        — from shared/n6/verify_formulas.hexa line 28:
#                       {n:6, sigma:12, tau:4, phi:2, sopfr:5, M3:7, J2:24, P2:28, mu:1}
#                       (matches atlas.n6 `@P M3 = mertens(6) = 7` foundation line)
#
# The only live difference is M3 (3 vs 7). atlas.n6's own foundation row states
# `M3 = 7` (mertens), while n6_constants.jsonl is a pre-Mertens encoding.
#
# Handling decision:
#   * Evaluate every expression under BOTH contexts.
#   * Expression is "validated" if at least one context matches the declared value
#     within tol = max(0.05*|value|, 0.5) (same tolerance as verify_formulas.hexa).
#   * If both match → `"context":"agent28"` (prefer the Phase 46 pivot authority).
#   * If only verify matches → `"context":"verify_formulas"` (flagged so that
#     downstream auditors can decide which to canonicalize).
#   * If neither matches → no edge, row counted in `eval_mismatch_both`.
#
# Infra-only: reads atlas.n6, writes JSONL to stdout. Does NOT modify atlas.n6.
# Edge cap: 500 per run (sorted by node appearance in atlas).
#
# Regen:
#   /usr/bin/python3 shared/n6/scripts/atlas_phase48_approx_expr_bridges.py \
#       > shared/n6/atlas_phase48_approx_expr_bridges.jsonl

import json
import re
import sys
from collections import defaultdict

ATLAS = "shared/n6/atlas.n6"
EDGE_CAP = 500

# Two canonical contexts (see header)
CTX_AGENT28 = {
    "n": 6, "phi": 2, "tau": 4, "sigma": 12, "sopfr": 5,
    "mu": 1, "j2": 24, "J2": 24, "m3": 3, "M3": 3, "P2": 28,
}
CTX_VERIFY = {
    "n": 6, "sigma": 12, "tau": 4, "phi": 2, "sopfr": 5,
    "M3": 7, "m3": 7, "J2": 24, "j2": 24, "P2": 28, "mu": 1,
}

# Primary token selection priority — which n6-* becomes the edge source.
# `n` is the deepest pivot; fall back alphabetically otherwise.
PRIMARY_PRIORITY = ["n", "phi", "tau", "sigma", "sopfr", "j2", "J2",
                    "m3", "M3", "mu", "P2"]

# Map an observed token → the canonical n6-* node id slug (Phase 46 ids
# are all lowercase, so J2→j2, M3→m3).
TOKEN_TO_CONST = {
    "n": "n6-n",
    "phi": "n6-phi",
    "tau": "n6-tau",
    "sigma": "n6-sigma",
    "sopfr": "n6-sopfr",
    "mu": "n6-mu",
    "j2": "n6-j2",
    "J2": "n6-j2",
    "m3": "n6-m3",
    "M3": "n6-m3",
    "P2": "n6-P2",  # P2 has no Phase 46 pivot yet — kept for bookkeeping only
}

# Tokens that count as "canonical presence" for the row (P2/M3 flagged, s<num>
# ignored because sX are lens-symmetry tokens, not n=6 constants).
CANON_TOKENS = {"n", "phi", "tau", "sigma", "sopfr", "mu", "j2", "J2", "m3", "M3", "P2"}

# Line pattern: @<TAG> <NODE-ID> = <VALUE> [= or ≈] <EXPR> :: <DOMAIN> [<GRADE>]
LINE_RE = re.compile(
    r"^@(?P<tag>\w+)\s+"
    r"(?P<id>\S+)\s*=\s*"
    r"(?P<val>[-+]?\d+(?:\.\d+)?)\s*"
    r"(?P<sep>[=≈])\s*"
    r"(?P<expr>[^:]+?)\s*::\s*"
    r"(?P<domain>[A-Za-z_]+)\s*"
    r"\[(?P<grade>[^\]]*)\]\s*$"
)

TOKEN_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\b")


def clean_expr(raw):
    """Strip the first evaluatable clause from an expression tail.

    Mirrors verify_formulas.hexa's cleaning:
      * take content before the first `;` (further clauses are alternative readings)
      * drop a trailing parenthetical like `(근사)` / `(경험)`
      * replace `^` → `**`, `²` → `**2`, `³` → `**3`
      * bail out if ANY non-ASCII remains (likely ellipsis `...` or Korean note)
    Returns cleaned string or None if not evaluatable.
    """
    if not raw:
        return None
    s = raw.split(";")[0].strip()
    s = re.sub(r"\s*\([^)]*\)\s*$", "", s).strip()
    if not s:
        return None
    low = s.lower()
    for stopword in ("근사", "불가", "misc", "none", "convention",
                     "exact", "없음", "경험", "추정"):
        if stopword in low:
            return None
    s = s.replace("^", "**").replace("²", "**2").replace("³", "**3")
    # Drop trailing `...` (ellipsis continuation markers)
    s = s.replace("...", "")
    # Reject if any non-ASCII remains (Hangul comments, unicode math)
    if re.search(r"[^\x00-\x7f]", s):
        return None
    # Reject multi-equals (`n*7 = 42` style) — take the first clause
    if "=" in s:
        s = s.split("=")[0].strip()
    return s or None


def safe_eval(expr, ctx):
    """Eval expr under ctx. Return numeric result or None on any failure."""
    try:
        v = eval(expr, {"__builtins__": {}}, ctx)
    except Exception:
        return None
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    return None


def extract_tokens(expr):
    """Return set of alphabetic tokens present in expr (for canonical gating)."""
    return {m.group(1) for m in TOKEN_RE.finditer(expr)}


def pick_primary_token(tokens):
    """Pick highest-priority canonical token present; None if none present."""
    for tok in PRIMARY_PRIORITY:
        if tok in tokens:
            return tok
    # Fall back: alphabetically first CANON token that mapped to a n6-*
    canon_hits = sorted(t for t in tokens if t in CANON_TOKENS)
    return canon_hits[0] if canon_hits else None


def parse_atlas(path):
    """Yield parsed (node_id, value, expr_raw, domain, grade) tuples."""
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            s = line.rstrip("\n")
            if not s or not s.startswith("@"):
                continue
            if "::" not in s:
                continue
            m = LINE_RE.match(s)
            if not m:
                continue
            try:
                val = float(m.group("val"))
            except ValueError:
                continue
            yield (m.group("id"), val, m.group("expr"),
                   m.group("domain"), m.group("grade"))


def main():
    print("# phase48 approx-expression cross-domain @S sweep — Agent 32")
    print("# source=atlas.n6 tokens=n,phi,tau,sigma,sopfr,mu,j2,M3,P2")
    print("# contexts=agent28(M3=3)|verify_formulas(M3=7)")

    per_token_counts = defaultdict(int)
    per_domain_counts = defaultdict(int)
    per_context_counts = defaultdict(int)

    total_rows = 0
    rows_with_canon = 0
    rows_eval_mismatch_both = 0
    rows_not_cleanable = 0
    emitted = 0
    capped = False

    seen_edges = set()

    for node_id, value, expr_raw, domain, grade in parse_atlas(ATLAS):
        total_rows += 1
        expr = clean_expr(expr_raw)
        if expr is None:
            rows_not_cleanable += 1
            continue
        tokens = extract_tokens(expr)
        canon_present = tokens & CANON_TOKENS
        if not canon_present:
            continue
        rows_with_canon += 1

        v_a = safe_eval(expr, CTX_AGENT28)
        v_v = safe_eval(expr, CTX_VERIFY)
        tol = max(0.05 * abs(value), 0.5)
        match_a = v_a is not None and abs(v_a - value) <= tol
        match_v = v_v is not None and abs(v_v - value) <= tol

        if not (match_a or match_v):
            rows_eval_mismatch_both += 1
            continue

        # Prefer agent28 authority when both match. Otherwise emit under whichever
        # context succeeded (flagging the row for M3/P2 discrepancy resolution).
        ctx_label = "agent28" if match_a else "verify_formulas"

        primary = pick_primary_token(tokens)
        if primary is None:
            continue
        from_id = TOKEN_TO_CONST.get(primary)
        if not from_id:
            continue
        # n6-P2 does not yet exist as a pivot node (Phase 46 emitted 8,
        # not including P2). Skip P2-primary edges to avoid dangling references.
        if from_id == "n6-P2":
            # Re-pick the next-best canonical token if P2 was primary.
            alt = [t for t in PRIMARY_PRIORITY if t in tokens and t != "P2"]
            if not alt:
                continue
            primary = alt[0]
            from_id = TOKEN_TO_CONST[primary]

        key = (from_id, node_id, ctx_label)
        if key in seen_edges:
            continue
        seen_edges.add(key)

        if emitted >= EDGE_CAP:
            capped = True
            break

        edge = {
            "type": "edge",
            "kind": "@S",
            "from": from_id,
            "to": node_id,
            "label": "approx_expr",
            "expr": expr_raw.strip().split(";")[0].strip(),
            "value": value,
            "to_domain": domain,
            "to_grade": grade,
            "context": ctx_label,
            "confidence": 1.0,
            "source": "phase48",
            "timestamp": "2026-04-11",
        }
        print(json.dumps(edge, ensure_ascii=False))
        emitted += 1
        per_token_counts[primary] += 1
        per_domain_counts[domain] += 1
        per_context_counts[ctx_label] += 1

    # Summary comments to stderr
    print(f"# phase48 summary", file=sys.stderr)
    print(f"# total_rows_scanned={total_rows}", file=sys.stderr)
    print(f"# rows_not_cleanable={rows_not_cleanable}", file=sys.stderr)
    print(f"# rows_with_canon_tokens={rows_with_canon}", file=sys.stderr)
    print(f"# rows_eval_mismatch_both={rows_eval_mismatch_both}", file=sys.stderr)
    print(f"# edges_emitted={emitted}", file=sys.stderr)
    print(f"# cap_hit={capped}", file=sys.stderr)
    for tok, cnt in sorted(per_token_counts.items(), key=lambda x: -x[1]):
        print(f"# TOKEN-BRIDGE-COUNT {tok} {cnt}", file=sys.stderr)
    for dom, cnt in sorted(per_domain_counts.items(), key=lambda x: -x[1]):
        print(f"# DOMAIN-BRIDGE-COUNT {dom} {cnt}", file=sys.stderr)
    for ctx, cnt in sorted(per_context_counts.items(), key=lambda x: -x[1]):
        print(f"# CONTEXT-BRIDGE-COUNT {ctx} {cnt}", file=sys.stderr)


if __name__ == "__main__":
    main()
