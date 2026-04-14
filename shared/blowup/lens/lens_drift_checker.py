#!/usr/bin/env python3
# @hexa-first-exempt — hexa stage1 runtime bug 우회 (T23~T29 복구 후 포팅)
"""
lens_drift_checker.py — LENS-P2-4

렌즈 간 모순(drift) 자동 감지기.

shared/config/lens_registry.json 의 1434 렌즈에서 "signals 가 상반되는 쌍" 탐지:
  (1) antonym_pair     — 이름에 상반 의미 키워드 쌍 포함 (e.g. "entropy" vs "entropy_reverse")
  (2) category_conflict — 동일 derived_from 인데 category 다름 (같은 출처가 두 도메인 주장)
  (3) cross_domain_self — "X_as_Y" 렌즈인데 X/Y 가 상호 배타적 카테고리 (e.g. thermodynamics_as_cognition)
  (4) status_conflict  — 동일 name 근본이 implemented vs forged/synthesized (상충 상태)
  (5) feature_opposition — features 리스트가 반대 키워드 포함 (e.g. path_search vs random_walk)

각 카테고리별 drift pair 목록 + 총 count + severity 등급 출력.
evidence: shared/discovery/lens_p2_4_drift_checker_2026-04-14.json

Usage:
  python3 lens_drift_checker.py
  python3 lens_drift_checker.py --registry /path/to/lens_registry.json --out /path/evidence.json
"""

import json
import sys
from pathlib import Path
from collections import defaultdict


# ─── 상반 키워드 쌍 (렌즈 이름/특징에서 탐지할 antonym) ───
ANTONYM_PAIRS = [
    ("entropy", "neg_entropy"),
    ("entropy", "negentropy"),
    ("entropy", "order"),
    ("linear", "nonlinear"),
    ("linear", "non_linear"),
    ("local", "global"),
    ("discrete", "continuous"),
    ("stable", "unstable"),
    ("stable", "chaotic"),
    ("deterministic", "stochastic"),
    ("deterministic", "random"),
    ("symmetric", "asymmetric"),
    ("classical", "quantum"),
    ("static", "dynamic"),
    ("reversible", "irreversible"),
    ("growth", "decay"),
    ("convergent", "divergent"),
    ("bounded", "unbounded"),
    ("finite", "infinite"),
    ("integer", "continuous"),
    ("coherent", "decoherent"),
    ("pure", "mixed"),
    ("forward", "reverse"),
    ("attractor", "repeller"),
    ("positive", "negative"),
    ("increase", "decrease"),
    ("minimal", "maximal"),
    ("compression", "expansion"),
    ("coupled", "decoupled"),
    ("ordered", "disordered"),
]

# ─── 상호 배타 도메인 쌍 (cross_domain A_as_B 에서 drift 후보) ───
# A_as_B: A 도메인 관점에서 B를 설명. 두 도메인이 근본적으로 이질적이면 drift 위험.
# lens_registry 에서 derived_from 에 실제 사용되는 도메인 토큰 기준.
EXCLUSIVE_DOMAIN_PAIRS = [
    # 지식계층: 형식과학(math) ↔ 인문예술
    ("math", "art"),
    ("math", "philosophy"),
    # 물리계 ↔ 사회문화
    ("physics", "culture"),
    ("physics", "philosophy"),
    # 자동화/기계 ↔ 생체/감정
    ("ai", "emotion"),
    ("robotics", "emotion"),
    ("robotics", "biology"),
    # 거시 ↔ 미시 (이례적 결합)
    ("cosmology", "chip"),
    ("cosmology", "battery"),
    # 이산/디지털 ↔ 유기/연속
    ("quantum", "economy"),
    ("chip", "biology"),
    ("chip", "cosmology"),
    # 에너지 생성 ↔ 인지
    ("fusion", "cognition"),
    ("solar", "cognition"),
    ("battery", "philosophy"),
]


def tokenize_name(name):
    """Split lens name into tokens: 'a_as_b' -> ['a', 'b']; 'entropy_reverse' -> ['entropy', 'reverse']."""
    return [t for t in name.lower().replace("-", "_").split("_") if t]


def _has_token(tokens, kw):
    """True if kw exactly matches any token (not substring — avoid 'linear' in 'nonlinear')."""
    return kw in tokens


def detect_antonym_pairs(lenses):
    """Find pairs of lenses whose token sets are 'near-duplicates' except for an antonym swap.
    Robust matching:
      (a) two lenses share ≥1 overlapping token (any root, not just first), AND
      (b) one lens has token X while the other has token Y where (X,Y) in ANTONYM_PAIRS, AND
      (c) neither lens contains both antonym tokens (to avoid cases where a single lens
          describes the antonymy intentionally, e.g. 'linear_vs_nonlinear')."""
    pairs = []
    lens_tokens = [(l, set(tokenize_name(l["name"]))) for l in lenses]
    seen = set()
    for i in range(len(lens_tokens)):
        a_lens, a_tok = lens_tokens[i]
        for a_kw, b_kw in ANTONYM_PAIRS:
            if not (_has_token(a_tok, a_kw) and not _has_token(a_tok, b_kw)):
                continue
            # look for partner with b_kw token and overlapping non-antonym token
            for j in range(len(lens_tokens)):
                if j == i:
                    continue
                b_lens, b_tok = lens_tokens[j]
                if not (_has_token(b_tok, b_kw) and not _has_token(b_tok, a_kw)):
                    continue
                overlap = (a_tok & b_tok) - {a_kw, b_kw}
                if not overlap:
                    continue
                key = tuple(sorted([a_lens["name"], b_lens["name"]]))
                if key in seen:
                    continue
                seen.add(key)
                pairs.append({
                    "type": "antonym_pair",
                    "lens_a": a_lens["name"],
                    "lens_b": b_lens["name"],
                    "overlap_tokens": sorted(overlap),
                    "antonym": [a_kw, b_kw],
                    "severity": "high",
                })
    return pairs


def detect_category_conflicts(lenses):
    """Same derived_from but different category → taxonomic drift."""
    by_source = defaultdict(list)
    for l in lenses:
        src = l.get("derived_from")
        if not src:
            continue
        by_source[src].append(l)

    pairs = []
    for src, group in by_source.items():
        cats = {l.get("category") for l in group}
        if len(cats) > 1:
            # emit pairwise for each distinct category pair
            grouped_by_cat = defaultdict(list)
            for l in group:
                grouped_by_cat[l.get("category")].append(l["name"])
            cat_list = sorted(grouped_by_cat.keys(), key=lambda c: (c is None, c))
            for ai in range(len(cat_list)):
                for bi in range(ai + 1, len(cat_list)):
                    ca, cb = cat_list[ai], cat_list[bi]
                    pairs.append({
                        "type": "category_conflict",
                        "derived_from": src,
                        "category_a": ca,
                        "category_b": cb,
                        "names_a_sample": grouped_by_cat[ca][:3],
                        "names_b_sample": grouped_by_cat[cb][:3],
                        "count_a": len(grouped_by_cat[ca]),
                        "count_b": len(grouped_by_cat[cb]),
                        "severity": "medium",
                    })
    return pairs


def detect_cross_domain_exclusive(lenses):
    """A_as_B cross_domain lenses where A and B are in exclusive-pair list."""
    pairs = []
    for l in lenses:
        if l.get("category") != "cross_domain":
            continue
        # expect derived_from = "a,b" and name = "a_as_b"
        df = l.get("derived_from", "")
        if "," not in df:
            continue
        a, b = [s.strip() for s in df.split(",", 1)]
        for pa, pb in EXCLUSIVE_DOMAIN_PAIRS:
            if (a == pa and b == pb) or (a == pb and b == pa):
                pairs.append({
                    "type": "cross_domain_exclusive",
                    "lens": l["name"],
                    "domains": [a, b],
                    "exclusive_pair": [pa, pb],
                    "severity": "medium",
                })
                break
    return pairs


def detect_status_conflicts(lenses):
    """Lenses whose name-token sets substantially overlap but statuses conflict
    (implemented vs forged/synthesized).  Requires ≥2 shared non-trivial tokens to
    avoid coincidental first-token matches (e.g. 'battery' vs 'bt_battery_array')."""
    implemented = [l for l in lenses if l.get("status") == "implemented"]
    weaker = [l for l in lenses if l.get("status") in ("forged", "synthesized")]

    # Precompute token sets, strip very common/short tokens to reduce noise
    COMMON = {"lens", "blowup", "bt", "hexa", "impl", "as"}
    def sig(l):
        return {t for t in tokenize_name(l["name"]) if t not in COMMON and len(t) >= 3}

    pairs = []
    seen = set()
    for imp in implemented:
        imp_sig = sig(imp)
        if len(imp_sig) < 2:
            continue
        for w in weaker:
            w_sig = sig(w)
            overlap = imp_sig & w_sig
            if len(overlap) >= 2:
                key = tuple(sorted([imp["name"], w["name"]]))
                if key in seen:
                    continue
                seen.add(key)
                pairs.append({
                    "type": "status_conflict",
                    "lens_implemented": imp["name"],
                    "lens_weaker": w["name"],
                    "weaker_status": w.get("status"),
                    "shared_tokens": sorted(overlap),
                    "severity": "low",
                })
    return pairs


def detect_feature_opposition(lenses):
    """Lenses sharing root but whose features contain antonym keyword pairs."""
    pairs = []
    feat_lenses = [l for l in lenses if isinstance(l.get("features"), list)]
    for i in range(len(feat_lenses)):
        a = feat_lenses[i]
        a_feat = {f.lower() for f in a["features"]}
        a_tokens = set(tokenize_name(a["name"]))
        for j in range(i + 1, len(feat_lenses)):
            b = feat_lenses[j]
            b_feat = {f.lower() for f in b["features"]}
            b_tokens = set(tokenize_name(b["name"]))
            # need some shared context (overlapping token) to count as drift
            if not (a_tokens & b_tokens):
                continue
            for k1, k2 in ANTONYM_PAIRS:
                if (any(k1 in f for f in a_feat) and any(k2 in f for f in b_feat)) or \
                   (any(k2 in f for f in a_feat) and any(k1 in f for f in b_feat)):
                    pairs.append({
                        "type": "feature_opposition",
                        "lens_a": a["name"],
                        "lens_b": b["name"],
                        "features_a": sorted(a_feat),
                        "features_b": sorted(b_feat),
                        "antonym": [k1, k2],
                        "severity": "low",
                    })
                    break
    return pairs


def run_drift_check(lenses):
    antonyms = detect_antonym_pairs(lenses)
    cat_conf = detect_category_conflicts(lenses)
    xdom     = detect_cross_domain_exclusive(lenses)
    status   = detect_status_conflicts(lenses)
    feat_opp = detect_feature_opposition(lenses)

    all_pairs = antonyms + cat_conf + xdom + status + feat_opp
    severity_count = {"high": 0, "medium": 0, "low": 0}
    for p in all_pairs:
        severity_count[p["severity"]] = severity_count.get(p["severity"], 0) + 1

    return {
        "total_pairs": len(all_pairs),
        "by_type": {
            "antonym_pair":            len(antonyms),
            "category_conflict":       len(cat_conf),
            "cross_domain_exclusive":  len(xdom),
            "status_conflict":         len(status),
            "feature_opposition":      len(feat_opp),
        },
        "by_severity": severity_count,
        "pairs": all_pairs,
    }


# ─── CLI ───

def parse_args(argv):
    registry = "/Users/ghost/Dev/nexus/shared/config/lens_registry.json"
    out = "/Users/ghost/Dev/nexus/shared/discovery/lens_p2_4_drift_checker_2026-04-14.json"
    i = 1
    while i < len(argv):
        if argv[i] == "--registry":
            registry = argv[i + 1]
            i += 2
        elif argv[i] == "--out":
            out = argv[i + 1]
            i += 2
        else:
            i += 1
    return registry, out


def main():
    registry, out = parse_args(sys.argv)
    print(f"[lens_drift] registry={registry}")

    with open(registry) as f:
        data = json.load(f)
    lenses = data["lenses"]
    print(f"[lens_drift] loaded {len(lenses)} lenses")

    report = run_drift_check(lenses)
    report["registry_version"]   = data.get("version")
    report["registry_total"]     = data.get("total")
    report["registry_generated"] = data.get("generated")
    report["generated_at"]       = "2026-04-14"
    report["drift_rate"]         = round(report["total_pairs"] / max(len(lenses), 1), 4)

    print("")
    print("=== Lens Drift Report ===")
    print(f"total drift pairs: {report['total_pairs']}")
    print(f"drift rate: {report['drift_rate']} (pairs / lens)")
    print(f"by type:     {report['by_type']}")
    print(f"by severity: {report['by_severity']}")
    print("")
    print("Top 10 pairs (by severity):")
    sev_rank = {"high": 0, "medium": 1, "low": 2}
    sorted_pairs = sorted(report["pairs"], key=lambda p: sev_rank.get(p["severity"], 9))
    for p in sorted_pairs[:10]:
        if p["type"] == "antonym_pair":
            print(f"  [{p['severity']}] {p['type']}: {p['lens_a']} ⟷ {p['lens_b']} (overlap={p['overlap_tokens']}, antonym={p['antonym']})")
        elif p["type"] == "category_conflict":
            print(f"  [{p['severity']}] {p['type']}: src={p['derived_from']} cats={p['category_a']}/{p['category_b']}")
        elif p["type"] == "cross_domain_exclusive":
            print(f"  [{p['severity']}] {p['type']}: {p['lens']} [{p['domains']}]")
        elif p["type"] == "status_conflict":
            print(f"  [{p['severity']}] {p['type']}: {p['lens_implemented']} (implemented) ⟷ {p['lens_weaker']} ({p['weaker_status']}) — shared {p['shared_tokens']}")
        elif p["type"] == "feature_opposition":
            print(f"  [{p['severity']}] {p['type']}: {p['lens_a']} ⟷ {p['lens_b']} antonym={p['antonym']}")

    Path(out).parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\n→ evidence written: {out}")


if __name__ == "__main__":
    main()
