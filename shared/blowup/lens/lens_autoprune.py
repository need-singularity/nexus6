#!/usr/bin/env python3
# @hexa-first-exempt — hexa stage1 runtime bug 우회 (LENS-P2 precedent)
"""
lens_autoprune.py — LENS-P3-1

자율 프루닝 루프: lens_registry.json 전 렌즈에 대해 consensus score를 계산하고,
score < 0.6 렌즈를 lens_archive.jsonl 로 이관, registry에서 제거.

Scheme: score = mean(f_antonym_pair_not_drift, f_category_consistent, f_status_implemented)
  - f_antonym_pair_not_drift: 1.0 if lens is not in any detected drift antonym_pair else 0.0
  - f_category_consistent: 1.0 if derived_from-grouped category is majority(==top), else ratio
  - f_status_implemented: {implemented: 1.0, derived: 0.85, synthesized: 0.7, forged: 0.55, other: 0.5}

CLI:
  python3 lens_autoprune.py [--dry-run] [--registry PATH] [--archive PATH]
                            [--threshold 0.6] [--out EVIDENCE_PATH]
"""

import json
import os
import sys
import tempfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path("/Users/ghost/Dev/nexus")
REG_PATH = ROOT / "shared/config/lens_registry.json"
ARCHIVE_PATH = ROOT / "shared/blowup/lens/lens_archive.jsonl"
EVIDENCE_PATH = ROOT / "shared/discovery/lens_p3_1_autoprune_2026-04-14.json"
THRESHOLD = 0.6
SCHEME_NAME = "mean3_antonym_category_status"


# Reuse drift antonym pairs from lens_drift_checker
try:
    sys.path.insert(0, str(ROOT / "shared/blowup/lens"))
    from lens_drift_checker import (
        ANTONYM_PAIRS,
        tokenize_name,
        detect_antonym_pairs,
    )
except Exception as e:
    print(f"[autoprune] WARN: failed to import lens_drift_checker ({e}); using inline fallback")
    ANTONYM_PAIRS = [
        ("entropy", "neg_entropy"), ("linear", "nonlinear"), ("local", "global"),
        ("discrete", "continuous"), ("stable", "unstable"), ("deterministic", "stochastic"),
        ("symmetric", "asymmetric"), ("classical", "quantum"), ("static", "dynamic"),
        ("reversible", "irreversible"), ("growth", "decay"), ("convergent", "divergent"),
        ("bounded", "unbounded"), ("finite", "infinite"), ("coherent", "decoherent"),
        ("pure", "mixed"), ("forward", "reverse"), ("attractor", "repeller"),
        ("positive", "negative"), ("increase", "decrease"), ("minimal", "maximal"),
        ("compression", "expansion"), ("coupled", "decoupled"), ("ordered", "disordered"),
    ]

    def tokenize_name(name):
        return [t for t in name.lower().replace("-", "_").split("_") if t]

    def detect_antonym_pairs(lenses):  # minimal fallback
        pairs = []
        toks = [(l, set(tokenize_name(l["name"]))) for l in lenses]
        seen = set()
        for i, (a, a_t) in enumerate(toks):
            for a_kw, b_kw in ANTONYM_PAIRS:
                if a_kw not in a_t or b_kw in a_t:
                    continue
                for j, (b, b_t) in enumerate(toks):
                    if i == j or b_kw not in b_t or a_kw in b_t:
                        continue
                    overlap = (a_t & b_t) - {a_kw, b_kw}
                    if not overlap:
                        continue
                    key = tuple(sorted([a["name"], b["name"]]))
                    if key in seen:
                        continue
                    seen.add(key)
                    pairs.append({"lens_a": a["name"], "lens_b": b["name"]})
        return pairs


STATUS_SCORE = {
    "implemented": 1.0,
    "derived": 0.85,
    "synthesized": 0.7,
    "forged": 0.55,
}


def build_drift_lens_set(lenses):
    """Return set of lens names that are in a detected antonym_pair (i.e., drifting)."""
    pairs = detect_antonym_pairs(lenses)
    drifting = set()
    for p in pairs:
        drifting.add(p.get("lens_a"))
        drifting.add(p.get("lens_b"))
    drifting.discard(None)
    return drifting, len(pairs)


def build_category_consistency(lenses):
    """For each derived_from source, compute dominant category share per lens.

    f_category_consistent(lens) =
      if lens has no derived_from → 1.0 (no cross-source drift possible)
      else size_of_lens_category_in_group / total_group_size
      (i.e., 1.0 if group is monolithic on lens's category, <1 if conflicting)
    """
    by_source = defaultdict(list)
    for l in lenses:
        src = l.get("derived_from")
        if src:
            by_source[src].append(l)

    score_by_name = {}
    for l in lenses:
        src = l.get("derived_from")
        if not src:
            score_by_name[l["name"]] = 1.0
            continue
        group = by_source[src]
        cats = Counter(x.get("category") for x in group)
        total = sum(cats.values())
        my_cat_count = cats[l.get("category")]
        score_by_name[l["name"]] = my_cat_count / total if total else 1.0
    return score_by_name


def compute_scores(lenses):
    drifting_names, drift_pair_count = build_drift_lens_set(lenses)
    cat_scores = build_category_consistency(lenses)

    scored = []
    for l in lenses:
        name = l["name"]
        f_anti = 0.0 if name in drifting_names else 1.0
        f_cat = cat_scores.get(name, 1.0)
        f_status = STATUS_SCORE.get(l.get("status"), 0.5)
        score = (f_anti + f_cat + f_status) / 3.0
        scored.append({
            "name": name,
            "category": l.get("category"),
            "status": l.get("status"),
            "derived_from": l.get("derived_from"),
            "score": round(score, 4),
            "f_antonym": f_anti,
            "f_category": round(f_cat, 4),
            "f_status": f_status,
            "lens": l,  # keep original for retention
        })
    return scored, drift_pair_count


def atomic_write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def append_archive(path: Path, entries):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a") as f:
        for e in entries:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")


def parse_args(argv):
    dry_run = False
    reg = REG_PATH
    arc = ARCHIVE_PATH
    thr = THRESHOLD
    out = EVIDENCE_PATH
    i = 1
    while i < len(argv):
        a = argv[i]
        if a == "--dry-run":
            dry_run = True
            i += 1
        elif a == "--registry":
            reg = Path(argv[i + 1]); i += 2
        elif a == "--archive":
            arc = Path(argv[i + 1]); i += 2
        elif a == "--threshold":
            thr = float(argv[i + 1]); i += 2
        elif a == "--out":
            out = Path(argv[i + 1]); i += 2
        else:
            i += 1
    return dry_run, reg, arc, thr, out


def main():
    dry_run, reg_path, arc_path, threshold, out_path = parse_args(sys.argv)
    print(f"[autoprune] registry={reg_path} threshold={threshold} dry_run={dry_run}")

    with open(reg_path) as f:
        reg = json.load(f)

    lenses = reg["lenses"]
    registry_size_before = len(lenses)
    print(f"[autoprune] loaded {registry_size_before} lenses")

    scored, drift_pair_count = compute_scores(lenses)
    print(f"[autoprune] drift antonym_pairs detected: {drift_pair_count}")

    archived = [s for s in scored if s["score"] < threshold]
    retained = [s for s in scored if s["score"] >= threshold]
    archived_count = len(archived)
    retained_count = len(retained)

    score_vals = [s["score"] for s in scored]
    min_score = round(min(score_vals), 4) if score_vals else 0.0
    max_score = round(max(score_vals), 4) if score_vals else 0.0
    mean_score = round(sum(score_vals) / len(score_vals), 4) if score_vals else 0.0

    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    decision_log = []
    archive_entries = []
    for s in archived:
        reason_parts = []
        if s["f_antonym"] < 1.0:
            reason_parts.append("antonym_drift")
        if s["f_category"] < 1.0:
            reason_parts.append(f"cat_conflict({s['f_category']:.2f})")
        if s["f_status"] < 0.85:
            reason_parts.append(f"weak_status({s['status']})")
        reason = "; ".join(reason_parts) or "composite_below_threshold"
        archive_entries.append({
            "id": s["name"],
            "name": s["name"],
            "score": s["score"],
            "reason": reason,
            "archived_at": now_iso,
            "category": s["category"],
            "status": s["status"],
            "derived_from": s["derived_from"],
        })
        decision_log.append({"name": s["name"], "score": s["score"], "action": "archive", "reason": reason})

    for s in retained[:5]:
        decision_log.append({"name": s["name"], "score": s["score"], "action": "retain"})

    print(f"[autoprune] archive: {archived_count}, retain: {retained_count}")
    print(f"[autoprune] score stats: min={min_score} max={max_score} mean={mean_score}")
    if archived_count:
        print("[autoprune] top archive candidates:")
        for s in sorted(archived, key=lambda x: x["score"])[:10]:
            print(f"    [{s['score']:.3f}] {s['name']} (status={s['status']} cat={s['category']})")

    registry_size_after = registry_size_before - archived_count

    if dry_run:
        print(f"[autoprune] DRY-RUN: would archive {archived_count}, registry {registry_size_before} → {registry_size_after}")
    else:
        if archive_entries:
            append_archive(arc_path, archive_entries)
            print(f"[autoprune] appended {len(archive_entries)} entries → {arc_path}")

        archived_names = {s["name"] for s in archived}
        new_lenses = [l for l in lenses if l["name"] not in archived_names]
        reg["lenses"] = new_lenses
        reg["total"] = len(new_lenses)
        prev_desc = reg.get("description", "")
        reg["description"] = (
            f"{prev_desc} | LENS-P3-1 autoprune: -{archived_count} (threshold<{threshold})"
            if "LENS-P3-1" not in prev_desc else prev_desc
        )
        cats = Counter(l.get("category") for l in new_lenses)
        reg["categories"] = dict(cats.most_common())
        atomic_write_json(reg_path, reg)
        print(f"[autoprune] registry rewritten: {registry_size_before} → {registry_size_after} (atomic)")

    evidence = {
        "task": "LENS-P3-1",
        "generated_at": now_iso,
        "scheme_name": SCHEME_NAME,
        "threshold": threshold,
        "total_scanned": registry_size_before,
        "archived_count": archived_count,
        "retained_count": retained_count,
        "min_score": min_score,
        "max_score": max_score,
        "mean_score": mean_score,
        "registry_size_before": registry_size_before,
        "registry_size_after": registry_size_after,
        "drift_pair_count": drift_pair_count,
        "dry_run": dry_run,
        "cycle_completed": True,
        "archive_path": str(arc_path),
        "registry_path": str(reg_path),
        "sample_decisions": decision_log[:30],
        "top_archived_sample": [
            {"name": s["name"], "score": s["score"], "category": s["category"], "status": s["status"]}
            for s in sorted(archived, key=lambda x: x["score"])[:15]
        ],
    }
    atomic_write_json(out_path, evidence)
    print(f"[autoprune] evidence written: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
