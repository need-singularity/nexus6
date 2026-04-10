#!/usr/bin/env python3
"""R-chain dynamics explorer

R(n) = σ(n)φ(n) / (n τ(n))  where σ=sum of divisors, τ=# of divisors, φ=Euler totient.

R(n) < n for all n≥2 (proven). Integer R-chains: n₀ → floor(R(n₀)) → ... → 1.

Modes:
  python3 chain_explorer.py --chain 193750        # Full chain to 1
  python3 chain_explorer.py --basin 500000         # All m≤N reaching exactly 1
  python3 chain_explorer.py --orbit 193750         # Exact rational iteration
  python3 chain_explorer.py --attractors 10000     # Fixed points & cycles
  python3 chain_explorer.py --longest 10000        # Longest chain up to N
  python3 chain_explorer.py --tree 1000            # ASCII tree of all chains
  python3 chain_explorer.py --stats 10000          # Chain length statistics
"""
import argparse
import math
import sys
from fractions import Fraction
from collections import defaultdict


# ---------------------------------------------------------------------------
# Core arithmetic (exact)
# ---------------------------------------------------------------------------

def sigma(n):
    """Sum of divisors of n."""
    s = 0
    for i in range(1, int(n**0.5) + 1):
        if n % i == 0:
            s += i + (n // i if i * i != n else 0)
    return s


def tau(n):
    """Number of divisors of n."""
    t = 0
    for i in range(1, int(n**0.5) + 1):
        if n % i == 0:
            t += 1 + (1 if i * i != n else 0)
    return t


def phi(n):
    """Euler totient of n."""
    r = n
    t = n
    p = 2
    while p * p <= t:
        if t % p == 0:
            while t % p == 0:
                t //= p
            r -= r // p
        p += 1
    if t > 1:
        r -= r // t
    return r


def R_exact(n):
    """R(n) as exact Fraction. Returns None for n < 2."""
    if n < 2:
        return None
    return Fraction(sigma(n) * phi(n), n * tau(n))


def R_floor(n):
    """floor(R(n)). Returns 0 for n < 2."""
    if n < 2:
        return 0
    r = R_exact(n)
    return int(r)  # Fraction.__int__ truncates toward zero = floor for positive


# ---------------------------------------------------------------------------
# Chain computation
# ---------------------------------------------------------------------------

def chain(n):
    """Compute integer R-chain from n to termination.

    Returns list of (value, R_exact_value) pairs.
    Chain terminates when value reaches 1 or 0, or cycles.
    """
    path = []
    seen = set()
    current = n
    while current >= 2 and current not in seen:
        seen.add(current)
        r = R_exact(current)
        path.append((current, r))
        current = int(r)
    # Record the terminal value
    if current == 1:
        path.append((1, None))
    elif current == 0:
        path.append((0, None))
    elif current in seen:
        # Cycle detected — record it
        path.append((current, "CYCLE"))
    return path


def chain_values(n):
    """Just the integer sequence of the chain."""
    return [step[0] for step in chain(n)]


# ---------------------------------------------------------------------------
# Basin computation
# ---------------------------------------------------------------------------

def basin_of(target, N):
    """Find all m ≤ N whose integer R-chain passes through target."""
    results = []
    for m in range(2, N + 1):
        vals = chain_values(m)
        if target in vals and m != target:
            results.append((m, len(vals) - 1))  # (start, chain_length)
    # Always include target itself if it has a valid chain
    if 2 <= target <= N:
        vals = chain_values(target)
        results.insert(0, (target, len(vals) - 1))
    return results


# ---------------------------------------------------------------------------
# Orbit (exact rational iteration)
# ---------------------------------------------------------------------------

def orbit(n, max_steps=50):
    """Iterate R exactly (no floor), show convergence of exact rationals.

    Returns list of (step, R_exact_value, float_value).
    """
    path = []
    current = Fraction(n)
    seen = {}
    for step in range(max_steps):
        if current < 2:
            path.append((step, current, float(current), "BELOW_2"))
            break
        # R_exact needs integer input — use floor of current rational
        n_int = int(current)
        if n_int < 2:
            path.append((step, current, float(current), "BELOW_2"))
            break
        r = R_exact(n_int)
        path.append((step, current, float(current), None))
        if r in seen:
            path.append((step + 1, r, float(r), f"CYCLE_FROM_STEP_{seen[r]}"))
            break
        seen[current] = step
        current = r
    return path


# ---------------------------------------------------------------------------
# Attractors: fixed points and cycles
# ---------------------------------------------------------------------------

def find_attractors(N):
    """Find fixed points and cycles in the floor(R) map up to N."""
    fixed_points = []
    cycles = defaultdict(list)

    for n in range(2, N + 1):
        fr = R_floor(n)
        if fr == n:
            fixed_points.append(n)

    # Find cycles by iterating from each n
    cycle_set = set()
    for n in range(2, N + 1):
        visited = {}
        current = n
        step = 0
        while current >= 2 and step < 200:
            if current in visited:
                # Found a cycle
                cycle_start = visited[current]
                cycle_nodes = []
                c = current
                for s, v in sorted(visited.items(), key=lambda x: x[1]):
                    if v >= cycle_start:
                        cycle_nodes.append(s)
                cycle_key = tuple(sorted(cycle_nodes))
                if cycle_key not in cycle_set:
                    cycle_set.add(cycle_key)
                    cycles[len(cycle_nodes)].append(cycle_nodes)
                break
            visited[current] = step
            current = R_floor(current)
            step += 1

    return fixed_points, dict(cycles)


# ---------------------------------------------------------------------------
# Longest chain
# ---------------------------------------------------------------------------

def find_longest(N):
    """Find the longest R-chain for any starting m ≤ N.

    Returns sorted list of (length, start_n, chain_values).
    """
    results = []
    for m in range(2, N + 1):
        vals = chain_values(m)
        length = len(vals) - 1  # number of arrows
        results.append((length, m, vals))
    results.sort(key=lambda x: (-x[0], x[1]))
    return results


# ---------------------------------------------------------------------------
# Tree building
# ---------------------------------------------------------------------------

def build_tree(N):
    """Build predecessor tree: for each n, who maps to n via floor(R)?

    Returns dict: target -> list of sources.
    """
    children = defaultdict(list)  # parent (target) -> children (sources)
    for m in range(2, N + 1):
        fr = R_floor(m)
        if 0 <= fr <= N:
            children[fr].append(m)
    return dict(children)


def render_ascii_tree(children, root, max_depth=6, max_children=8):
    """Render tree as ASCII art."""
    lines = []

    def _render(node, prefix, is_last, depth):
        connector = "└── " if is_last else "├── "
        if depth == 0:
            lines.append(f"{node}")
        else:
            lines.append(f"{prefix}{connector}{node}")

        if depth >= max_depth:
            kids = children.get(node, [])
            if kids:
                new_prefix = prefix + ("    " if is_last else "│   ")
                lines.append(f"{new_prefix}└── ... ({len(kids)} children)")
            return

        kids = sorted(children.get(node, []))
        shown = kids[:max_children]
        omitted = len(kids) - len(shown)

        for i, child in enumerate(shown):
            is_child_last = (i == len(shown) - 1) and omitted == 0
            new_prefix = prefix + ("    " if is_last else "│   ")
            if depth == 0:
                new_prefix = ""
            _render(child, new_prefix, is_child_last, depth + 1)

        if omitted > 0:
            new_prefix = prefix + ("    " if is_last else "│   ")
            if depth == 0:
                new_prefix = ""
            lines.append(f"{new_prefix}└── ... ({omitted} more)")

    _render(root, "", True, 0)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------

def compute_stats(N):
    """Compute chain length statistics for all m ≤ N."""
    lengths = {}
    terminals = defaultdict(int)
    reaches_one = 0

    for m in range(2, N + 1):
        vals = chain_values(m)
        length = len(vals) - 1
        lengths[m] = length
        terminal = vals[-1]
        terminals[terminal] += 1
        if 1 in vals:
            reaches_one += 1

    # Length distribution
    len_counts = defaultdict(int)
    for l in lengths.values():
        len_counts[l] += 1

    return lengths, len_counts, terminals, reaches_one


def ascii_histogram(counts, title="", max_width=50):
    """Render a horizontal ASCII histogram."""
    lines = []
    if title:
        lines.append(title)
        lines.append("=" * len(title))
    if not counts:
        lines.append("  (no data)")
        return "\n".join(lines)

    max_val = max(counts.values())
    for key in sorted(counts.keys()):
        cnt = counts[key]
        bar_len = int(cnt / max_val * max_width) if max_val > 0 else 0
        bar = "█" * bar_len
        lines.append(f"  {key:>4d} │ {bar} {cnt}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

def fmt_fraction(f):
    """Format Fraction nicely."""
    if f is None:
        return "-"
    if isinstance(f, str):
        return f
    if f.denominator == 1:
        return str(f.numerator)
    return f"{f.numerator}/{f.denominator}"


def fmt_chain_arrow(vals):
    """Format chain as arrow diagram."""
    return " → ".join(str(v) for v in vals)


# ---------------------------------------------------------------------------
# Mode implementations
# ---------------------------------------------------------------------------

def mode_chain(n):
    """--chain N: show full R-chain from N to terminal."""
    print(f"\n  R-chain from n = {n}")
    print(f"  {'─' * 60}")

    path = chain(n)
    vals = [step[0] for step in path]

    # Detailed step-by-step
    for i, (val, r) in enumerate(path):
        if r is None:
            print(f"  [{i}]  n = {val}  (terminal)")
        elif r == "CYCLE":
            print(f"  [{i}]  n = {val}  (CYCLE detected)")
        else:
            s, t, p = sigma(val), tau(val), phi(val)
            print(f"  [{i}]  n = {val:>10d}   σ={s:<10d} τ={t:<6d} φ={p:<10d}"
                  f"   R = {fmt_fraction(r):>16s} = {float(r):.6f}"
                  f"   floor = {int(r)}")

    print(f"\n  Chain: {fmt_chain_arrow(vals)}")
    print(f"  Length: {len(vals) - 1} steps")


def mode_basin(N):
    """--basin N: find all m ≤ N whose chain passes through 1."""
    print(f"\n  Basin of R = 1 (exact), searching m = 2..{N}")
    print(f"  {'─' * 60}")

    results = []
    for m in range(2, N + 1):
        vals = chain_values(m)
        if 1 in vals:
            results.append((m, len(vals) - 1, vals))

    if not results:
        print("  No chains reach exactly 1.")
        return

    print(f"\n  Found {len(results)} starting values whose chain reaches 1:\n")
    print(f"  {'Start':>10s}  {'Length':>6s}  Chain")
    print(f"  {'─'*10}  {'─'*6}  {'─'*40}")
    for start, length, vals in results:
        print(f"  {start:>10d}  {length:>6d}  {fmt_chain_arrow(vals)}")

    # Show the basin as a set
    starts = [r[0] for r in results]
    print(f"\n  Basin set: {{{', '.join(str(s) for s in starts)}}}")
    print(f"  Basin size: {len(starts)}")


def mode_orbit(n, max_steps=30):
    """--orbit N: exact rational iteration."""
    print(f"\n  Exact rational orbit from n = {n}")
    print(f"  {'─' * 60}")

    path = orbit(n, max_steps)

    print(f"\n  {'Step':>4s}  {'n_int':>10s}  {'R(n) exact':>24s}  {'R(n) float':>14s}  Note")
    print(f"  {'─'*4}  {'─'*10}  {'─'*24}  {'─'*14}  {'─'*20}")
    for step, val, fval, note in path:
        n_int = int(val) if val >= 2 else int(val)
        note_str = note if note else ""
        print(f"  {step:>4d}  {n_int:>10d}  {fmt_fraction(val):>24s}  {fval:>14.8f}  {note_str}")

    # Convergence summary
    floats = [fval for _, _, fval, _ in path]
    if len(floats) >= 2:
        print(f"\n  Start: {floats[0]:.6f}")
        print(f"  End:   {floats[-1]:.6f}")
        if floats[-1] > 0:
            ratio = floats[-1] / floats[0] if floats[0] > 0 else 0
            print(f"  Contraction ratio: {ratio:.8f}")


def mode_attractors(N):
    """--attractors N: find fixed points and cycles."""
    print(f"\n  Attractors in floor(R) map, n = 2..{N}")
    print(f"  {'─' * 60}")

    fixed_points, cycles = find_attractors(N)

    print(f"\n  Fixed points (floor(R(n)) = n):")
    if fixed_points:
        for fp in fixed_points:
            r = R_exact(fp)
            print(f"    n = {fp:>8d}   R(n) = {fmt_fraction(r)} = {float(r):.6f}")
    else:
        print("    None found.")

    print(f"\n  Cycles:")
    if cycles:
        for length, cycle_list in sorted(cycles.items()):
            for cyc in cycle_list:
                arrow = " → ".join(str(c) for c in cyc)
                print(f"    Length {length}: {arrow}")
    else:
        print("    None found (all chains terminate at 0 or 1).")

    # Map summary: where does each n terminate?
    terminals = defaultdict(int)
    for n in range(2, min(N + 1, 10001)):
        vals = chain_values(n)
        terminals[vals[-1]] += 1
    print(f"\n  Terminal distribution (n ≤ {min(N, 10000)}):")
    for t in sorted(terminals.keys()):
        print(f"    terminal = {t:>4d}: {terminals[t]:>6d} chains ({100*terminals[t]/(min(N,10000)-1):.1f}%)")


def mode_longest(N, top_k=20):
    """--longest N: find longest chains up to N."""
    print(f"\n  Longest R-chains, m = 2..{N}")
    print(f"  {'─' * 60}")

    results = find_longest(N)
    shown = results[:top_k]

    print(f"\n  Top {top_k} longest chains:\n")
    print(f"  {'Rank':>4s}  {'Start':>10s}  {'Length':>6s}  Chain")
    print(f"  {'─'*4}  {'─'*10}  {'─'*6}  {'─'*50}")
    for i, (length, start, vals) in enumerate(shown):
        chain_str = fmt_chain_arrow(vals)
        if len(chain_str) > 70:
            chain_str = " → ".join(str(v) for v in vals[:4]) + " → ... → " + str(vals[-1])
        print(f"  {i+1:>4d}  {start:>10d}  {length:>6d}  {chain_str}")

    # Length histogram
    len_counts = defaultdict(int)
    for length, _, _ in results:
        len_counts[length] += 1
    print(f"\n{ascii_histogram(len_counts, '  Chain length distribution')}")


def mode_tree(N):
    """--tree N: build and display predecessor tree."""
    print(f"\n  R-chain predecessor tree, n = 2..{N}")
    print(f"  {'─' * 60}")

    children = build_tree(N)

    # Find roots that are interesting (1, 0, and any cycles)
    for root in [1, 0]:
        kids = children.get(root, [])
        if kids or root == 1:
            print(f"\n  Tree rooted at {root} ({len(kids)} direct predecessors):\n")
            tree_str = render_ascii_tree(children, root, max_depth=4, max_children=10)
            for line in tree_str.split("\n"):
                print(f"    {line}")

    # Summary statistics
    out_degree = defaultdict(int)
    for target, sources in children.items():
        out_degree[target] = len(sources)

    if out_degree:
        hub_nodes = sorted(out_degree.items(), key=lambda x: -x[1])[:10]
        print(f"\n  Hub nodes (most predecessors):")
        print(f"  {'Node':>8s}  {'#Pred':>6s}")
        for node, count in hub_nodes:
            print(f"  {node:>8d}  {count:>6d}")


def mode_stats(N):
    """--stats N: full statistics."""
    print(f"\n  R-chain statistics, n = 2..{N}")
    print(f"  {'─' * 60}")

    lengths, len_counts, terminals, reaches_one = compute_stats(N)

    total = N - 1  # n=2..N

    # Basic stats
    all_lengths = list(lengths.values())
    avg_len = sum(all_lengths) / len(all_lengths)
    max_len = max(all_lengths)
    min_len = min(all_lengths)
    max_n = [n for n, l in lengths.items() if l == max_len]

    print(f"\n  Total chains: {total}")
    print(f"  Reaches 1:    {reaches_one} ({100*reaches_one/total:.3f}%)")
    print(f"  Avg length:   {avg_len:.2f}")
    print(f"  Min length:   {min_len}")
    print(f"  Max length:   {max_len}  (from n = {', '.join(str(n) for n in max_n[:5])})")

    # Terminal distribution
    print(f"\n  Terminal values:")
    print(f"  {'Terminal':>10s}  {'Count':>8s}  {'Percent':>8s}")
    print(f"  {'─'*10}  {'─'*8}  {'─'*8}")
    for t in sorted(terminals.keys()):
        pct = 100 * terminals[t] / total
        print(f"  {t:>10d}  {terminals[t]:>8d}  {pct:>7.2f}%")

    # Chain length histogram
    print(f"\n{ascii_histogram(len_counts, '  Chain length distribution')}")

    # Convergence rate: average R(n)/n
    print(f"\n  Contraction analysis (sample):")
    print(f"  {'n':>10s}  {'R(n)':>14s}  {'R/n':>10s}  {'floor(R)':>10s}")
    print(f"  {'─'*10}  {'─'*14}  {'─'*10}  {'─'*10}")
    samples = [2, 3, 4, 5, 6, 10, 12, 24, 28, 30, 60, 120, 360, 720, 5040]
    samples = [s for s in samples if s <= N]
    for n in samples:
        r = R_exact(n)
        ratio = float(r) / n
        print(f"  {n:>10d}  {float(r):>14.4f}  {ratio:>10.6f}  {int(r):>10d}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    p = argparse.ArgumentParser(
        description="R-chain dynamics explorer: R(n) = σ(n)φ(n)/(nτ(n))",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --chain 193750          Full chain from 193750 to 1
  %(prog)s --chain 6               Chain from 6
  %(prog)s --basin 500000          Basin of 1 up to 500000
  %(prog)s --orbit 193750          Exact rational orbit
  %(prog)s --attractors 10000      Fixed points & cycles up to 10000
  %(prog)s --longest 10000         Longest chain up to 10000
  %(prog)s --tree 1000             Predecessor tree up to 1000
  %(prog)s --stats 10000           Full statistics up to 10000

Known chains for verification:
  193750 → 6048 → 120 → 6 → 1  (length 4)
  6 → 1                         (length 1)
"""
    )
    p.add_argument("--chain", type=int, metavar="N",
                   help="Compute full R-chain from N to terminal")
    p.add_argument("--basin", type=int, metavar="N",
                   help="Find all m≤N whose chain passes through 1")
    p.add_argument("--orbit", type=int, metavar="N",
                   help="Exact rational orbit iteration from N")
    p.add_argument("--attractors", type=int, metavar="N",
                   help="Find fixed points and cycles up to N")
    p.add_argument("--longest", type=int, metavar="N",
                   help="Find longest R-chain starting from any m≤N")
    p.add_argument("--tree", type=int, metavar="N",
                   help="Build predecessor tree up to N, show ASCII")
    p.add_argument("--stats", type=int, metavar="N",
                   help="Chain length statistics for m=2..N")
    p.add_argument("--top", type=int, default=20,
                   help="Number of top results to show (default 20)")
    p.add_argument("--max-steps", type=int, default=30,
                   help="Max iteration steps for --orbit (default 30)")

    args = p.parse_args()

    if args.chain is not None:
        mode_chain(args.chain)
    elif args.basin is not None:
        mode_basin(args.basin)
    elif args.orbit is not None:
        mode_orbit(args.orbit, args.max_steps)
    elif args.attractors is not None:
        mode_attractors(args.attractors)
    elif args.longest is not None:
        mode_longest(args.longest, args.top)
    elif args.tree is not None:
        mode_tree(args.tree)
    elif args.stats is not None:
        mode_stats(args.stats)
    else:
        p.print_help()


if __name__ == "__main__":
    main()
