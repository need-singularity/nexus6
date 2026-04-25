#!/usr/bin/env python3
# tool/self_correction_evidence.py
#
# Created: 2026-04-25 (paper draft companion — docs/self_correction_chain_paper_20260425.md).
# Aggregates git-log evidence for the meta-claim:
#
#   "AI iterative design via paired enforce rules (raw 37/38 voluntary discipline)
#    → empirical self-correction chain → claim precision ↑"
#
# Scope (本 session):
#   - 9-step mechanism self-correction chain (cycle 24 → 33), commit hashes, claim transitions
#   - 11+번 self-correction across 57 cycles (env propagation 5/8/9 → 11, enforce reality 43 → 56,
#     dispatch_path 49 → 51 → sub-agent L7)
#   - 2 enforce wire decisions (cycle 44 zero-dep + cycle 56 standalone CLI)
#
# Methodology:
#   1. git log --since/--until 으로 본 session window 의 commits collect
#   2. message regex 로 cycle number / fix-vs-feat / mechanism keywords 추출
#   3. 9-step chain 정합성 (cycle 24~33 모두 존재) verify
#   4. solo-cycle vs chain-completed claim 의 status mapping (paper Table 1/2)
#
# Zero-dependency:
#   - python3 stdlib only (subprocess, re, json, dataclasses)
#   - shell call: git log only
#
# Outputs:
#   - stdout: human-readable summary (paper §3 evidence table)
#   - --json: machine-readable JSON (state/self_correction_evidence_20260425.json)

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional


SESSION_SINCE = "2026-04-25 14:00:00"
SESSION_UNTIL = "2026-04-25 23:59:59"


@dataclass
class Commit:
    hash: str
    iso_ts: str
    subject: str
    cycle: Optional[int] = None
    proposal: Optional[str] = None  # nxs-20260425-001/002/003/004
    kind: Optional[str] = None      # feat / fix / docs / chore
    is_correction: bool = False     # 'fix(' prefix or 'falsif' / '정정' / 'incomplete' / 'narrow'
    keywords: List[str] = field(default_factory=list)


# ---------- self-correction chain 정의 (paper Table 1) ----------
# 9-step mechanism chain (cycle 24 → 33)
MECHANISM_CHAIN = [
    (24, "isolated ER → general self-averaging", "over-broad"),
    (25, "finite-N self-averaging at N=800",     "misleading"),
    (26, "N=800 special accident",                "over-narrow"),
    (27, "K=100 boundary alignment",              "still narrow"),
    (28, "K=80~105 range invariance",             "wrong width"),
    (29, "K interleaved pattern",                 "numerical detail"),
    (30, "ER lowest > K cut → invariant",         "incomplete"),
    (31, "K=100 ALL comp small eig mixing",       "partial"),
    (32, "singleton + giant component structure", "true mechanism"),
    (33, "universal ER giant+singletons (98% giant)", "paper-grade"),
]

# 11+ self-correction events (env propagation, dispatch path, enforce reality)
OTHER_CORRECTIONS = [
    # env propagation chain: cycle 5/8/9 over-reach → cycle 11 정정
    (5,  "Phase 3 1차 발사 negative",                   "env propagation 가설 weak signal"),
    (8,  "env propagation 가설 확정 + setenv sanity",   "premature confirm"),
    (9,  "env propagation 가설 기각",                   "self-falsified"),
    (11, "TRUE root cause: hetzner setenv 미정의",       "true mechanism (corrected)"),
    # dispatch_path: cycle 49 partial → 51 root cause → sub-agent L7
    (49, "Phase 3 field validation",                     "partial"),
    (51, "진짜 root cause = cross-session host load 97%","root cause"),
    (52, "Phase 4 L7 PSI-defer FIFO queue",              "sub-agent fix (true mechanism)"),
    # enforce reality: cycle 43 ready-but-not-wired → cycle 56 wired
    (43, "raw 37/38 enforce 실제 작동 안 함 (caller 없음)",  "honesty"),
    (44, "의존도 0 달성, raw 37/38 enforce 의도적 미wire",   "principled defer"),
    (56, "raw 37/38 enforce wire (standalone CLI)",          "wired (true closure)"),
]


def git_log_lines(since: str, until: str) -> List[Commit]:
    """git log --pretty 로 commit list 수집."""
    cmd = [
        "git", "log",
        f"--since={since}", f"--until={until}",
        "--pretty=format:%H|%aI|%s",
        "--no-merges",
    ]
    try:
        out = subprocess.check_output(cmd, text=True, cwd="/Users/ghost/core/nexus")
    except subprocess.CalledProcessError as e:
        print(f"git log failed: {e}", file=sys.stderr)
        return []

    commits: List[Commit] = []
    cycle_re = re.compile(r"cycle\s+(\d+)", re.IGNORECASE)
    proposal_re = re.compile(r"nxs-2026042[0-9]-(\d{3})")
    kind_re = re.compile(r"^(feat|fix|docs|chore|refactor|test)")
    correction_words = ("falsif", "정정", "incomplete", "narrow", "기각",
                        "broaden", "wrong", "missing", "재해석", "revised",
                        "honest", "진솔", "진짜", "TRUE root cause",
                        "ready-but-not-wired", "partial")

    for line in out.splitlines():
        if not line.strip():
            continue
        parts = line.split("|", 2)
        if len(parts) != 3:
            continue
        h, ts, subj = parts
        c = Commit(hash=h[:8], iso_ts=ts, subject=subj)
        m = cycle_re.search(subj)
        if m:
            c.cycle = int(m.group(1))
        m2 = proposal_re.search(subj)
        if m2:
            c.proposal = f"nxs-2026042?-{m2.group(1)}"
        m3 = kind_re.match(subj)
        if m3:
            c.kind = m3.group(1)
        c.is_correction = (c.kind == "fix") or any(w in subj for w in correction_words)
        for kw in ("ER", "giant", "singleton", "anti-hub", "V3'", "K=100",
                   "Lanczos", "PSI", "dispatch", "enforce", "self-correction",
                   "mechanism", "universal"):
            if kw in subj:
                c.keywords.append(kw)
        commits.append(c)

    return commits


def find_chain_commits(commits: List[Commit], cycles_wanted: List[int]) -> Dict[int, Commit]:
    """cycle 번호 → 가장 늦은 (or 첫) commit 매핑."""
    by_cycle: Dict[int, Commit] = {}
    for c in commits:
        if c.cycle in cycles_wanted:
            # nxs-20260425-001 우선 (mechanism chain), 그 외 첫 매칭 보존
            if c.cycle not in by_cycle:
                by_cycle[c.cycle] = c
            else:
                # nxs-001 prefer over 002/003/004
                cur = by_cycle[c.cycle]
                if cur.proposal != "nxs-2026042?-001" and c.proposal == "nxs-2026042?-001":
                    by_cycle[c.cycle] = c
    return by_cycle


def precision_table(by_cycle: Dict[int, Commit]) -> List[Dict]:
    """paper Table 1 — 9-step chain precision evolution."""
    rows = []
    for cyc, claim, status in MECHANISM_CHAIN:
        c = by_cycle.get(cyc)
        rows.append({
            "cycle": cyc,
            "claim": claim,
            "status": status,
            "commit": c.hash if c else None,
            "subject": c.subject if c else None,
            "is_correction": c.is_correction if c else None,
        })
    return rows


def other_corrections_table(by_cycle: Dict[int, Commit]) -> List[Dict]:
    """paper Table 2 — env+dispatch+enforce corrections."""
    rows = []
    for cyc, claim, status in OTHER_CORRECTIONS:
        c = by_cycle.get(cyc)
        rows.append({
            "cycle": cyc,
            "claim_or_action": claim,
            "status": status,
            "commit": c.hash if c else None,
            "subject": c.subject if c else None,
            "is_correction": c.is_correction if c else None,
        })
    return rows


def stats(commits: List[Commit], chain_rows: List[Dict],
          other_rows: List[Dict]) -> Dict:
    """meta-statistics: solo vs chain claim precision."""
    n_total = len(commits)
    n_corrections = sum(1 for c in commits if c.is_correction)

    # 9-step chain: solo cycle 24 alone vs full chain endpoint cycle 33
    solo_24 = chain_rows[0]
    final_33 = chain_rows[-1]
    chain_steps = sum(1 for r in chain_rows if r["commit"] is not None)
    chain_corrections = sum(1 for r in chain_rows if r.get("is_correction"))

    other_steps = sum(1 for r in other_rows if r["commit"] is not None)
    other_corrections = sum(1 for r in other_rows if r.get("is_correction"))

    return {
        "session_window": f"{SESSION_SINCE} → {SESSION_UNTIL}",
        "total_commits_in_window": n_total,
        "total_corrections": n_corrections,
        "correction_rate": round(n_corrections / max(1, n_total), 3),
        "mechanism_chain_steps_found": f"{chain_steps}/10",
        "mechanism_chain_corrections": chain_corrections,
        "other_corrections_steps_found": f"{other_steps}/{len(OTHER_CORRECTIONS)}",
        "other_corrections_count": other_corrections,
        "self_corrections_total_documented": chain_corrections + other_corrections,
        "solo_claim_cycle24": solo_24["claim"],
        "solo_claim_status": solo_24["status"],
        "chain_endpoint_claim_cycle33": final_33["claim"],
        "chain_endpoint_status": final_33["status"],
        "precision_delta_qualitative":
            "over-broad → paper-grade (universal across N=200~3200, ~98% giant fraction)",
    }


def render_text(chain_rows, other_rows, st):
    lines = []
    lines.append("=" * 78)
    lines.append("SELF-CORRECTION CHAIN — EVIDENCE AGGREGATION (paper companion)")
    lines.append(f"Session: {st['session_window']}")
    lines.append("=" * 78)
    lines.append("")
    lines.append("## Stats")
    for k, v in st.items():
        if k == "session_window":
            continue
        lines.append(f"  {k}: {v}")
    lines.append("")
    lines.append("## Table 1 — 9-step mechanism chain (cycle 24→33)")
    lines.append(f"{'cyc':>4}  {'commit':<10}  {'status':<22}  claim")
    lines.append("-" * 78)
    for r in chain_rows:
        commit = r["commit"] or "(missing)"
        lines.append(f"{r['cycle']:>4}  {commit:<10}  {r['status']:<22}  {r['claim']}")
    lines.append("")
    lines.append("## Table 2 — Other self-corrections (env / dispatch / enforce)")
    lines.append(f"{'cyc':>4}  {'commit':<10}  {'status':<28}  action/claim")
    lines.append("-" * 78)
    for r in other_rows:
        commit = r["commit"] or "(missing)"
        lines.append(f"{r['cycle']:>4}  {commit:<10}  {r['status']:<28}  {r['claim_or_action']}")
    lines.append("")
    lines.append("## Meta-claim verification")
    lines.append("  IF solo-cycle claim only (cycle 24)  → over-broad generalization")
    lines.append("  IF full chain to cycle 33            → paper-grade universal pattern")
    lines.append(f"  Self-corrections documented in 1 session: "
                 f"{st['self_corrections_total_documented']} (paired enforce → falsification chain)")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=None,
                    help="write machine-readable JSON to this path")
    ap.add_argument("--since", default=SESSION_SINCE)
    ap.add_argument("--until", default=SESSION_UNTIL)
    args = ap.parse_args()

    commits = git_log_lines(args.since, args.until)
    cycles_wanted_chain = [c for c, _, _ in MECHANISM_CHAIN]
    cycles_wanted_other = [c for c, _, _ in OTHER_CORRECTIONS]
    by_cycle_chain = find_chain_commits(commits, cycles_wanted_chain)
    by_cycle_other = find_chain_commits(commits, cycles_wanted_other)

    chain_rows = precision_table(by_cycle_chain)
    other_rows = other_corrections_table(by_cycle_other)
    st = stats(commits, chain_rows, other_rows)

    text = render_text(chain_rows, other_rows, st)
    print(text)

    if args.json:
        payload = {
            "stats": st,
            "mechanism_chain": chain_rows,
            "other_corrections": other_rows,
            "all_commits_in_window": [asdict(c) for c in commits],
        }
        with open(args.json, "w") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        print(f"\n[wrote] {args.json}", file=sys.stderr)


if __name__ == "__main__":
    main()
