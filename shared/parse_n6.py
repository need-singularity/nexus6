#!/usr/bin/env python3
"""parse_n6.py — .n6 Knowledge Atlas parser.

Parses the NEXUS-6 .n6 format into structured Python objects.
Usage:
    python3 parse_n6.py atlas.n6                 # summary
    python3 parse_n6.py atlas.n6 --json           # full JSON export
    python3 parse_n6.py atlas.n6 --graph          # dependency graph (DOT)
    python3 parse_n6.py atlas.n6 --verify         # check all expressions
    python3 parse_n6.py atlas.n6 --broken         # find disconnected nodes
"""

import re, json, sys, math
from pathlib import Path
from collections import defaultdict

# ── n=6 primitive namespace for eval ────────────────────────
N6 = {
    "n": 6, "sigma": 12, "phi": 2, "tau": 4, "sopfr": 5,
    "J2": 24, "mu": 1, "M3": 7, "pi": math.pi, "e": math.e,
}

TYPE_MAP = {"P": "primitive", "C": "constant", "L": "law",
            "F": "formula", "R": "relation", "S": "symmetry",
            "X": "crossing", "?": "unknown"}

RE_ENTRY = re.compile(
    r'^@([PCLFRSX?])\s+'
    r'(\w+)'
    r'(?:\s*=\s*(.+?))?'
    r'\s*::\s*(\w+)'
    r'(?:\s*\[([^\]]+)\])?'
)
RE_ATTR = re.compile(r'^\s+([-=~!|><][-=>!|>]?)\s*(.+)$')
RE_QUOTED = re.compile(r'^"(.+)"$')


def parse_n6(path):
    """Parse .n6 file into list of entry dicts."""
    entries = []
    current = None

    for line in Path(path).read_text().splitlines():
        line_stripped = line.rstrip()
        if not line_stripped or line_stripped.startswith("#"):
            continue

        m = RE_ENTRY.match(line_stripped)
        if m:
            if current:
                entries.append(current)
            typ, name, expr, domain, grade_raw = m.groups()
            grade, verified, breakthrough, hypothesis = _parse_grade(grade_raw or "")
            value = _try_eval(expr) if expr else None
            current = {
                "id": f"{typ}.{name}",
                "type": TYPE_MAP.get(typ, typ),
                "name": name,
                "expr": expr,
                "value": value,
                "domain": domain,
                "grade": grade,
                "verified": verified,
                "breakthrough": breakthrough,
                "hypothesis": hypothesis,
                "depends_on": [],
                "derives": [],
                "applications": [],
                "equivalences": [],
                "convergences": [],
                "verified_by": [],
                "breakthroughs": [],
                "statement": None,
            }
            continue

        if current is None:
            continue

        m_attr = RE_ATTR.match(line_stripped)
        if m_attr:
            op, val = m_attr.group(1), m_attr.group(2).strip()
            val = RE_QUOTED.sub(r'\1', val)  # strip quotes
            if op == "<-":
                current["depends_on"].extend(s.strip() for s in val.split(","))
            elif op == "->":
                current["derives"].extend(s.strip() for s in val.split(","))
            elif op == "=>":
                current["applications"].append(val)
            elif op == "==":
                current["equivalences"].append(val)
            elif op == "~>":
                current["convergences"].append(val)
            elif op == "|>":
                current["verified_by"].append(val)
            elif op == "!!":
                current["breakthroughs"].append(val)
        else:
            # Bare quoted string = statement
            m_q = RE_QUOTED.match(line_stripped.strip())
            if m_q and current:
                current["statement"] = m_q.group(1)

    if current:
        entries.append(current)
    return entries


def _parse_grade(raw):
    grade, verified, bt, hyp = 0, False, False, False
    raw = raw.strip()
    if "*" in raw:
        verified = True
        raw = raw.replace("*", "")
    if "!" in raw:
        bt = True
        raw = raw.replace("!", "")
    if "?" in raw:
        hyp = True
        raw = raw.replace("?", "")
    try:
        grade = int(raw) if raw else 0
    except ValueError:
        try:
            grade = float(raw) if raw else 0
        except ValueError:
            pass
    return grade, verified, bt, hyp


def _try_eval(expr):
    if not expr:
        return None
    # Extract last = value if present
    parts = expr.split("=")
    for p in reversed(parts):
        p = p.strip()
        try:
            return eval(p, {"__builtins__": {}}, N6)
        except:
            pass
    return None


# ── Analysis ────────────────────────────────────────────────

def build_graph(entries):
    """Build adjacency from depends_on + derives."""
    graph = defaultdict(set)   # parent -> children
    reverse = defaultdict(set) # child -> parents
    names = {e["name"]: e for e in entries}
    for e in entries:
        for dep in e["depends_on"]:
            graph[dep].add(e["name"])
            reverse[e["name"]].add(dep)
        for der in e["derives"]:
            graph[e["name"]].add(der)
            reverse[der].add(e["name"])
    return graph, reverse, names


def find_broken(entries):
    """Find nodes with unresolved dependencies."""
    known = {e["name"] for e in entries}
    broken = []
    for e in entries:
        for dep in e["depends_on"]:
            if dep not in known:
                broken.append((e["name"], dep))
    return broken


def verify_all(entries):
    """Verify all expressions evaluate correctly."""
    results = []
    for e in entries:
        if e["expr"] and e["value"] is not None:
            expected = _try_eval(e["expr"])
            if expected is not None:
                ok = abs(expected - e["value"]) < 1e-9 if isinstance(expected, float) else expected == e["value"]
                results.append((e["name"], e["expr"], e["value"], expected, ok))
    return results


def summary(entries):
    """Print atlas summary."""
    by_type = defaultdict(list)
    by_domain = defaultdict(list)
    for e in entries:
        by_type[e["type"]].append(e)
        by_domain[e["domain"]].append(e)

    total = len(entries)
    verified = sum(1 for e in entries if e["verified"])
    bts = sum(1 for e in entries if e["breakthrough"])
    hyps = sum(1 for e in entries if e["hypothesis"])
    deps = sum(len(e["depends_on"]) for e in entries)
    apps = sum(len(e["applications"]) for e in entries)

    print(f"""
  ╔══════════════════════════════════════════╗
  ║     NEXUS-6 Knowledge Atlas (.n6)        ║
  ╠══════════════════════════════════════════╣
  ║  Total entries:    {total:>4}                  ║
  ║  Verified:         {verified:>4}  ({verified*100//max(total,1)}%)            ║
  ║  Breakthroughs:    {bts:>4}                  ║
  ║  Hypotheses:       {hyps:>4}                  ║
  ║  Dependencies:     {deps:>4}                  ║
  ║  Applications:     {apps:>4}                  ║
  ╠══════════════════════════════════════════╣""")

    for t in ["primitive","constant","law","formula","relation","crossing","unknown"]:
        if t in by_type:
            print(f"  ║  @{t[0].upper():<12} {len(by_type[t]):>4}                  ║")

    print(f"  ╠══════════════════════════════════════════╣")
    for d, items in sorted(by_domain.items(), key=lambda x: -len(x[1])):
        g_avg = sum(e["grade"] for e in items) / max(len(items), 1)
        print(f"  ║  {d:<16} {len(items):>3} entries  avg={g_avg:.1f}  ║")
    print(f"  ╚══════════════════════════════════════════╝")

    broken = find_broken(entries)
    if broken:
        print(f"\n  ⚠ Broken links ({len(broken)}):")
        for name, dep in broken:
            print(f"    {name} <- {dep} (not found)")


def to_dot(entries):
    """Export DOT graph."""
    graph, _, names = build_graph(entries)
    print("digraph n6_atlas {")
    print("  rankdir=BT;")
    print('  node [shape=box, fontname="Menlo"];')
    colors = {"primitive":"#2196F3","constant":"#4CAF50","law":"#FF9800",
              "formula":"#9C27B0","relation":"#607D8B","crossing":"#F44336","unknown":"#999"}
    for e in entries:
        c = colors.get(e["type"], "#999")
        label = f"{e['name']}\\n{e.get('value','')}"
        style = "filled" if e["verified"] else "dashed"
        print(f'  "{e["name"]}" [label="{label}", fillcolor="{c}", style="{style}", fontcolor="white"];')
    for parent, children in graph.items():
        for child in children:
            print(f'  "{parent}" -> "{child}";')
    print("}")


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print("Usage: parse_n6.py <file.n6> [--json|--graph|--verify|--broken]")
        sys.exit(1)

    path = args[0]
    entries = parse_n6(path)

    if "--json" in args:
        print(json.dumps(entries, indent=2, ensure_ascii=False, default=str))
    elif "--graph" in args:
        to_dot(entries)
    elif "--verify" in args:
        results = verify_all(entries)
        for name, expr, val, expected, ok in results:
            mark = "✅" if ok else "❌"
            print(f"  {mark} {name}: {expr} = {val} (expected {expected})")
        passed = sum(1 for *_, ok in results if ok)
        print(f"\n  {passed}/{len(results)} passed")
    elif "--broken" in args:
        broken = find_broken(entries)
        if broken:
            for name, dep in broken:
                print(f"  ❌ {name} <- {dep}")
        else:
            print("  ✅ No broken links")
    else:
        summary(entries)
