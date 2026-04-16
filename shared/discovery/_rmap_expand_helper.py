#!/usr/bin/env python3
"""reality_map_expander helper — DISC-P8-1
Called by reality_map_expander.hexa. Not intended for direct use.
Scans 6 sources for unmapped entries and generates expansion JSONL.
"""
import json, sys, os, re
from datetime import datetime, timezone

NEXUS = os.path.join(os.environ["HOME"], "Dev", "nexus")
DISC  = os.path.join(NEXUS, "shared", "discovery")
N6    = os.path.join(NEXUS, "shared", "n6")
BT    = os.path.join(NEXUS, "shared", "bt")

MERGED   = os.path.join(DISC, "reality_map.patches.merged.jsonl")
V9       = os.path.join(DISC, "reality_map_v9.json")
EXT_T8   = os.path.join(DISC, "reality_map_extension_t8.jsonl")
EXT_T12  = os.path.join(DISC, "reality_map_t12_expansion.jsonl")
STAGING  = os.path.join(DISC, "reality_map_expansion.jsonl")

VCONSTANTS = os.path.join(DISC, "verified_constants.jsonl")
ATLAS      = os.path.join(N6, "atlas.n6")
N6K        = os.path.join(N6, "n6_knowledge.jsonl")
N6P        = os.path.join(N6, "n6_physics.jsonl")
N6C        = os.path.join(N6, "n6_constants.jsonl")
N6L        = os.path.join(N6, "n6_lenses.jsonl")
DSEEDS     = os.path.join(DISC, "domain_seeds.jsonl")
THEORY     = os.path.join(DISC, "theory_registry.jsonl")
BT_DOM     = os.path.join(BT, "bt_domains.jsonl")


def load_existing_ids():
    """Load all existing IDs from reality_map sources."""
    ids = set()

    # 1. patches.merged.jsonl
    for line in _read_jsonl(MERGED):
        ids.add(line.get("id", ""))

    # 2. v9 nodes
    try:
        with open(V9) as f:
            data = json.load(f)
        for n in data.get("nodes", []):
            if isinstance(n, dict):
                ids.add(n.get("id", ""))
    except Exception:
        pass

    # 3. extension files
    for path in [EXT_T8, EXT_T12]:
        for line in _read_jsonl(path):
            ids.add(line.get("id", ""))

    # 4. existing staging
    for line in _read_jsonl(STAGING):
        ids.add(line.get("id", ""))

    ids.discard("")
    return ids


def _read_jsonl(path):
    """Yield parsed JSON objects from a JSONL file."""
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue
    except FileNotFoundError:
        return


def _entry(eid, level, claim, measured, unit, detail, source, n6_expr,
           grade, causal, thread, origin):
    """Build a reality_map entry dict."""
    return {
        "id": eid, "level": level, "claim": claim,
        "measured": measured, "unit": unit, "detail": detail,
        "source": source, "source_url": "",
        "n6_expr": n6_expr, "grade": grade, "causal": causal,
        "thread": thread, "origin": origin, "bt_refs": [],
        "_patch_source": "reality_map_expander.hexa"
    }


# ── Source 1: verified_constants ──────────────────────────
def scan_verified_constants(existing):
    """Parse verified_constants.jsonl for PASS/EXACT entries."""
    new_entries = []
    seen = set()

    for obj in _read_jsonl(VCONSTANTS):
        st = obj.get("status", "")
        if st not in ("PASS", "EXACT"):
            continue
        name = obj.get("name", "").strip()
        if "=" not in name:
            continue
        src = obj.get("source", "")
        proj = obj.get("project", "")

        parts = name.split()
        if len(parts) < 2:
            continue
        tag = parts[0]

        eqparts = name.split("=")
        if len(eqparts) < 2:
            continue
        measured = eqparts[-1].strip()
        expr = "=".join(eqparts[1:-1]).strip() if len(eqparts) > 2 else eqparts[0].strip()
        claim = " ".join(parts[1:]).split("=")[0].strip()

        # Assign level from source path
        sl = src.lower()
        tl = tag.lower()
        level = "L5_material"
        if any(k in sl for k in ("chip", "gpu")) or \
           any(k in tl for k in ("sm-", "ma-", "is-")):
            level = "L5_architecture"
        elif any(k in sl for k in ("material", "polymer")):
            level = "L5_material"
        elif any(k in sl for k in ("environ", "climate")):
            level = "L6_climate"
        elif any(k in sl for k in ("bio", "gene", "protein")):
            level = "L4_genetic"
        elif any(k in sl for k in ("chem", "bond", "molecule")):
            level = "L3_molecule"
        elif any(k in sl for k in ("atom", "element")):
            level = "L1_atom"
        elif any(k in sl for k in ("particle", "quark")):
            level = "L0_particle"
        elif any(k in sl for k in ("astro", "cosmo")):
            level = "L6_astronomy"
        elif any(k in sl for k in ("econ", "financ")):
            level = "L6_economics"
        elif "music" in sl:
            level = "L6_music"
        elif any(k in sl for k in ("geo", "earth")):
            level = "L6_geology"
        elif "ocean" in sl:
            level = "L6_oceanography"
        elif "hyp" in proj.lower() or "mega" in tl:
            level = "L2_law"

        eid = "VC-" + tag
        if eid in seen or eid in existing:
            continue
        seen.add(eid)

        grade = "EXACT" if st == "EXACT" else "VERIFIED"
        new_entries.append(_entry(
            eid, level, claim, measured, "n6",
            "[n6-verified] " + name,
            proj + "/" + src, expr,
            grade, "DERIVED", "n6", "engineering"
        ))

    return new_entries


# ── Source 2: atlas.n6 @-nodes ────────────────────────────
def scan_atlas(existing):
    """Parse atlas.n6 for @-notation entries."""
    new_entries = []
    seen = set()
    pat = re.compile(r'^@(\w)\s+(\S+)\s*=\s*(.+?)\s*::\s*(\S+)\s*\[([^\]]+)\]')

    try:
        with open(ATLAS) as f:
            for line in f:
                line = line.strip()
                m = pat.match(line)
                if not m:
                    continue
                atype, aid, expr, domain, grade_raw = m.groups()
                eid = "ATL-" + aid
                if eid in seen or eid in existing:
                    continue
                seen.add(eid)

                level_map = {"P": "L0_particle", "C": "L2_law", "L": "L2_law",
                             "F": "L2_law", "R": "L2_law", "S": "L2_law",
                             "X": "L2_law", "H": "L2_law", "?": "L2_law"}
                level = level_map.get(atype, "L2_law")
                grade = "VERIFIED" if "*" in grade_raw else "HYPOTHESIS"
                if "!" in grade_raw:
                    grade = "EXACT"

                new_entries.append(_entry(
                    eid, level, f"{aid} = {expr.strip()}", expr.strip(), "n6",
                    f"[atlas.n6] @{atype} {aid} :: {domain}",
                    "shared/n6/atlas.n6", expr.strip(),
                    grade, "DERIVED", domain, "mathematical"
                ))
    except FileNotFoundError:
        pass

    return new_entries


# ── Source 3: n6_knowledge + n6_physics + n6_constants + n6_lenses ──
def scan_n6_data(existing):
    """Parse n6 JSONL data files."""
    new_entries = []
    seen = set()
    files = [
        (N6K, "N6K", "L2_law"),
        (N6P, "N6P", "L0_particle"),
        (N6C, "N6C", "L2_law"),
        (N6L, "N6L", "L2_law"),
    ]

    for path, tag, default_level in files:
        for obj in _read_jsonl(path):
            if "_schema" in obj:
                continue
            oid = obj.get("id", "") or obj.get("name", "")
            if not oid:
                continue
            eid = f"{tag}-{str(oid).replace(' ', '_')}"
            if eid in seen or eid in existing:
                continue
            seen.add(eid)

            val = obj.get("value", "")
            desc = (obj.get("desc", "") or obj.get("description", "") or
                    obj.get("statement", "") or str(oid))
            domain = obj.get("domain", "n6")
            grade = "VERIFIED" if obj.get("verified", False) else "HYPOTHESIS"
            n6_expr = obj.get("expr", "") or obj.get("latex", "") or str(val)

            new_entries.append(_entry(
                eid, default_level, desc, str(val), "n6",
                f"[{tag}] {desc}",
                f"shared/n6/{os.path.basename(path)}", n6_expr,
                grade, "DERIVED", domain, "mathematical"
            ))

    return new_entries


# ── Source 4: domain_seeds.jsonl ──────────────────────────
def scan_domain_seeds(existing):
    """Parse domain_seeds.jsonl."""
    new_entries = []
    seen = set()

    for obj in _read_jsonl(DSEEDS):
        domain = obj.get("domain", "")
        name = obj.get("name", "")
        if not domain or not name:
            continue
        eid = f"DSEED-{domain}-{name}"
        if eid in seen or eid in existing:
            continue
        seen.add(eid)

        val = obj.get("value", "")
        ref = obj.get("ref", "")
        new_entries.append(_entry(
            eid, f"L6_{domain}", ref or name, str(val), "",
            f"[domain_seed] {domain}: {name}={val}",
            "shared/discovery/domain_seeds.jsonl", "seed",
            "CONVENTION", "EMPIRICAL", domain, "natural"
        ))

    return new_entries


# ── Source 5: theory_registry.jsonl ───────────────────────
def scan_theory_registry(existing):
    """Parse theory_registry.jsonl."""
    new_entries = []
    seen = set()

    for obj in _read_jsonl(THEORY):
        name = obj.get("name", "")
        domain = obj.get("domain", "")
        if not name:
            continue
        eid = f"THR-{name}"
        if eid in seen or eid in existing:
            continue
        seen.add(eid)

        desc = obj.get("desc", "") or name
        loc = obj.get("loc", 0)
        fp = obj.get("fp", "")
        grade = "VERIFIED" if loc > 50 else "HYPOTHESIS"

        new_entries.append(_entry(
            eid, "L2_law", desc, f"{loc} LOC", "LOC",
            f"[theory_registry] {name} ({domain}) fp={fp}",
            "shared/discovery/theory_registry.jsonl",
            fp if fp else "none",
            grade, "DERIVED", domain, "mathematical"
        ))

    return new_entries


# ── Source 6: bt_domains cross-reference ──────────────────
def scan_bt_domains(existing):
    """Parse bt_domains.jsonl."""
    new_entries = []
    seen = set()

    for obj in _read_jsonl(BT_DOM):
        domain = obj.get("domain", "")
        keywords = obj.get("keywords", [])
        if not domain:
            continue
        eid = f"BTD-{domain}"
        if eid in seen or eid in existing:
            continue
        seen.add(eid)

        kwstr = ", ".join(keywords[:5])
        new_entries.append(_entry(
            eid, "L2_law", f"BT domain: {domain}",
            str(len(keywords)), "keywords",
            f"[bt_domains] {domain}: {kwstr}",
            "shared/bt/bt_domains.jsonl", "bt_domain",
            "CONVENTION", "DERIVED", domain, "engineering"
        ))

    return new_entries


# ── Merge staging into merged ─────────────────────────────
def merge_staging():
    """Append staging entries to merged, with final dedup."""
    try:
        staging_lines = list(_read_jsonl(STAGING))
    except FileNotFoundError:
        print(json.dumps({"action": "merge", "status": "skip",
                          "reason": "staging empty"}))
        return

    if not staging_lines:
        print(json.dumps({"action": "merge", "status": "skip",
                          "reason": "staging empty"}))
        return

    # Load existing merged IDs
    existing = set()
    for obj in _read_jsonl(MERGED):
        existing.add(obj.get("id", ""))

    before = sum(1 for _ in _read_jsonl(MERGED))
    added = 0
    with open(MERGED, "a") as out:
        for obj in staging_lines:
            eid = obj.get("id", "")
            if eid in existing:
                continue
            existing.add(eid)
            out.write(json.dumps(obj, ensure_ascii=False) + "\n")
            added += 1

    after = before + added
    print(json.dumps({"action": "merge", "status": "done",
                      "before": before, "after": after, "added": added}))


# ── Main ──────────────────────────────────────────────────
def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "missing subcommand"}))
        sys.exit(1)

    subcmd = sys.argv[1]
    merge_flag = "--merge" in sys.argv

    if subcmd == "status":
        existing = load_existing_ids()
        merged_count = sum(1 for _ in _read_jsonl(MERGED))
        try:
            with open(V9) as f:
                v9_count = len(json.load(f).get("nodes", []))
        except Exception:
            v9_count = 0
        t8_count = sum(1 for _ in _read_jsonl(EXT_T8))
        t12_count = sum(1 for _ in _read_jsonl(EXT_T12))
        staging_count = sum(1 for _ in _read_jsonl(STAGING))
        total = len(existing)
        print(json.dumps({
            "status": "ok", "merged": merged_count,
            "v9_nodes": v9_count, "ext_t8": t8_count,
            "ext_t12": t12_count, "staging": staging_count,
            "unique_ids": total, "target": 7500,
            "gap": 7500 - total
        }))
        return

    if subcmd in ("scan", "expand"):
        do_write = subcmd == "expand"

        if do_write:
            # Clear staging
            with open(STAGING, "w") as f:
                pass

        existing = load_existing_ids()
        print(json.dumps({"phase": "loaded_existing",
                          "unique_ids": len(existing)}))

        sources = [
            ("verified_constants", scan_verified_constants),
            ("atlas.n6", scan_atlas),
            ("n6_data", scan_n6_data),
            ("domain_seeds", scan_domain_seeds),
            ("theory_registry", scan_theory_registry),
            ("bt_domains", scan_bt_domains),
        ]

        total_new = 0
        all_new = []
        for name, scanner in sources:
            entries = scanner(existing)
            count = len(entries)
            total_new += count
            all_new.extend(entries)
            # Add new IDs to existing so later sources dedup
            for e in entries:
                existing.add(e["id"])
            print(json.dumps({"source": name, "new": count}))

        if do_write and all_new:
            with open(STAGING, "w") as f:
                for e in all_new:
                    f.write(json.dumps(e, ensure_ascii=False) + "\n")

        projected = len(existing)
        print(json.dumps({
            "summary": {
                "existing": projected - total_new,
                "total_new": total_new,
                "projected": projected,
                "target": 7500,
                "gap_remaining": 7500 - projected,
                "mode": subcmd
            }
        }))

        if do_write and merge_flag:
            merge_staging()

        return

    print(json.dumps({"error": f"unknown subcommand: {subcmd}"}))
    sys.exit(1)


if __name__ == "__main__":
    main()
