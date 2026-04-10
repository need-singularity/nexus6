#!/usr/bin/env python3
"""논문 제출 관리자 — Zenodo/OSF 미제출 추적 + 🛸10 게이트 자동 제출

Usage:
    python3 zenodo/submission_manager.py status          # 전체 현황 테이블
    python3 zenodo/submission_manager.py submit-all      # 미제출 전부 제출
    python3 zenodo/submission_manager.py submit-all --dry-run  # 시뮬레이션
    python3 zenodo/submission_manager.py submit P-004    # 특정 논문 제출
    python3 zenodo/submission_manager.py gate            # 🛸10 게이트 체크 후 자동 제출
    python3 zenodo/submission_manager.py gate --dry-run  # 게이트 체크만 (제출 안함)
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

try:
    import requests
except ImportError:
    print("pip install requests")
    sys.exit(1)

ROOT = Path(__file__).parent.parent  # TECS-L root
MANIFEST = Path(__file__).parent / "manifest.json"
RESULTS_DIR = Path(__file__).parent

# Token paths
TOKEN_PATHS = {
    "zenodo": ROOT / ".local" / "zenodo_token",
    "zenodo_sandbox": ROOT / ".local" / "zenodo_sandbox_token",
    "osf": ROOT / ".local" / "osf_token",
}

# API URLs
ZENODO_API = "https://zenodo.org/api"
OSF_API = "https://api.osf.io/v2"

# n6-architecture products.json
N6_PRODUCTS = Path.home() / "Dev" / "n6-architecture" / "config" / "products.json"

# Paper → section mapping (for alien index gate)
PAPER_SECTION_MAP = {
    # TECS-L core papers
    "P-001": "ai", "P-002": "ai", "P-003": "ai", "P-EE": "energy",
    "P-GMoE": "ai", "P-N6": "physics", "P-MIT": "ai", "P-005": "physics",
    "P-PH": "ai", "P-TS": "physics", "P-CCT": "ai", "P-CS": "materials",
    "P-DOL": "physics", "P-GI": "ai", "P-bridge-theorem": "physics",
    "P-CODON": "physics", "P-SLE6": "physics", "P-LAW79": "physics",
    "P-ZERO-FREE": "physics", "P-FACTORIAL": "physics", "P-KISSING": "physics",
    "P-CONFLUENCE": "physics", "P-PRIME-FACTORIAL": "physics",
    "P-SIGMA-SIGMA": "physics", "P-THREE-SIGMA": "physics",
    "P-PARENT-IDENTITY": "physics", "P-PARADIGM": "physics",
    "P-MULTI-OBJECTIVE": "physics", "P-ICT": "physics", "P-A6": "physics",
    "P-GUT": "physics", "P-PRECISION": "physics",
    # Anima papers → ai
    **{f"PA-{i:02d}": "ai" for i in range(1, 38)},
    "PA-11b": "ai", "PA-20b": "ai",
    # SEDI papers → physics
    **{f"PS-{i:02d}": "physics" for i in range(1, 21)},
    # Brain papers → materials (neuroscience)
    "PB-01": "materials", "PB-02": "materials",
    # Special
    "P-NEW-1": "physics", "P-NEW-2": "physics", "P-NEW-3": "physics",
    "P-NOBEL": "physics", "P-CERN": "physics",
    "PS-21": "physics", "PS-22": "physics", "PS-23": "physics",
    "P-DNA-A": "physics", "P-DNA-B": "physics",
    # n6-architecture papers
    "N6-BATTERY": "energy", "N6-BIOLOGY": "materials", "N6-CARBON": "environment",
    "N6-CHIP-CONS": "chip", "N6-SOC-CONS": "chip", "N6-CRYSTAL": "materials",
    "N6-DRAM": "chip", "N6-ENERGY-EFF": "energy", "N6-ENV-THERMAL": "environment",
    "N6-EXYNOS": "chip", "N6-HEXA-3D": "display", "N6-HEXA-PHOTON": "display",
    "N6-HEXA-PIM": "chip", "N6-HEXA-SUPER": "chip", "N6-HEXA-WAFER": "chip",
    "N6-ISOCELL": "chip", "N6-PARTICLE": "physics", "N6-PERF-CHIP": "chip",
    "N6-PLASMA-FUSION": "fusion", "N6-PURE-MATH": "physics",
    "N6-ROBOTICS": "robotics", "N6-SOFTWARE": "software",
    "N6-SUPERCONDUCTOR": "fusion", "N6-UNIFIED-SOC": "chip", "N6-VNAND": "chip",
    "N6-PAPER1": "ai", "N6-PAPER2": "physics", "N6-PAPER3": "fusion", "N6-PAPER4": "physics",
}

REPO_ROOTS = {
    "tecs-l": ROOT,
    "anima": ROOT.parent / "anima",
    "sedi": ROOT.parent / "sedi",
    "n6-architecture": Path.home() / "Dev" / "n6-architecture",
}


# ═══════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════

def load_manifest():
    with open(MANIFEST) as f:
        return json.load(f)


def get_token(platform: str) -> str:
    path = TOKEN_PATHS.get(platform)
    if path and path.exists():
        return path.read_text().strip()
    env_map = {"zenodo": "ZENODO_TOKEN", "osf": "OSF_TOKEN"}
    token = os.environ.get(env_map.get(platform, ""), "")
    if token:
        return token.strip()
    print(f"❌ {platform} 토큰 없음. {path} 에 저장하세요.")
    return ""


def load_submitted() -> dict:
    """Load all submission results and return {paper_id: {zenodo: ..., osf: ...}}."""
    submitted = {}

    result_files = [
        ("zenodo", "upload-results-zenodo.json"),
        ("zenodo", "upload-results-8-drafts.json"),
        ("zenodo", "upload-results-dna.json"),
        ("osf", "upload-results-osf.json"),
        ("osf", "upload-results-8-drafts.json"),
        ("osf", "upload-results-dna.json"),
    ]

    for platform, fname in result_files:
        path = RESULTS_DIR / fname
        if not path.exists():
            continue
        data = json.load(open(path))

        if platform == "zenodo":
            items = data.get("results", []) or data.get("zenodo", [])
            for item in items:
                pid = item.get("paper_id") or item.get("id") or item.get("paper")
                if not pid:
                    continue
                submitted.setdefault(pid, {})
                submitted[pid]["zenodo"] = {
                    "doi": item.get("doi", ""),
                    "dep_id": item.get("dep_id") or item.get("id"),
                }

        if platform == "osf":
            items = data.get("results", []) or data.get("osf", [])
            for item in items:
                pid = item.get("paper_id") or item.get("id") or item.get("paper")
                if not pid:
                    continue
                submitted.setdefault(pid, {})
                result_data = item.get("result", item)
                submitted[pid]["osf"] = {
                    "node_id": result_data.get("node_id", ""),
                    "url": result_data.get("url", ""),
                }

    return submitted


def load_alien_indices() -> dict:
    """Load alien index per section from products.json."""
    if not N6_PRODUCTS.exists():
        return {}
    data = json.load(open(N6_PRODUCTS))
    return {s["id"]: s.get("alien_index", 0) for s in data.get("sections", [])}


def resolve_file(paper: dict, repo_key: str) -> Path:
    repo_root = REPO_ROOTS.get(repo_key, ROOT)
    filepath = repo_root / paper["file"]
    if filepath.exists():
        return filepath
    if "repo" in paper:
        alt_root = REPO_ROOTS.get(paper["repo"], ROOT)
        alt_path = alt_root / paper["file"]
        if alt_path.exists():
            return alt_path
    return filepath


def collect_files(paper: dict, repo_key: str) -> list:
    files = []
    main = resolve_file(paper, repo_key)
    if main.exists():
        files.append(main)
    for extra in paper.get("existing", []):
        p = REPO_ROOTS.get(repo_key, ROOT) / extra
        if p.exists():
            files.append(p)
    return files


# ═══════════════════════════════════════════════════════════
# Upload functions
# ═══════════════════════════════════════════════════════════

def upload_zenodo(paper, repo_key, token, manifest_meta):
    pid = paper["id"]
    files = collect_files(paper, repo_key)
    if not files:
        print(f"  [{pid}] SKIP — 파일 없음")
        return None

    meta = {
        "title": paper["title"],
        "upload_type": "publication",
        "publication_type": "preprint",
        "description": paper.get("description", f"Preprint: {paper['title']}"),
        "creators": [{"name": manifest_meta.get("author", "TECS-L Project")}],
        "access_right": "open",
        "license": "cc-by-4.0",
        "keywords": paper.get("keywords", []),
    }

    # Create deposition
    r = requests.post(f"{ZENODO_API}/deposit/depositions",
                      params={"access_token": token}, json={})
    if r.status_code >= 400:
        print(f"  [{pid}] ❌ Zenodo 생성 실패: {r.status_code}")
        return None

    dep = r.json()
    dep_id = dep["id"]
    bucket = dep["links"]["bucket"]
    doi = dep["metadata"].get("prereserve_doi", {}).get("doi", "N/A")

    # Metadata
    requests.put(f"{ZENODO_API}/deposit/depositions/{dep_id}",
                 params={"access_token": token},
                 json={"metadata": meta},
                 headers={"Content-Type": "application/json"})

    # Upload files
    for f in files:
        with open(f, "rb") as fp:
            r = requests.put(f"{bucket}/{f.name}",
                             data=fp,
                             params={"access_token": token},
                             headers={"Content-Type": "application/octet-stream"})

    # Publish
    r = requests.post(f"{ZENODO_API}/deposit/depositions/{dep_id}/actions/publish",
                      params={"access_token": token})
    if r.status_code < 400:
        final = r.json()
        doi = final.get("doi", doi)
        print(f"  [{pid}] ✅ Zenodo PUBLISHED — DOI: {doi}")
    else:
        print(f"  [{pid}] ⚠️ Zenodo draft (publish failed: {r.status_code})")

    return {"paper_id": pid, "dep_id": dep_id, "doi": doi}


def upload_osf(paper, repo_key, token):
    pid = paper["id"]
    files = collect_files(paper, repo_key)
    if not files:
        print(f"  [{pid}] SKIP — 파일 없음")
        return None

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/vnd.api+json",
    }

    # Create node
    node_data = {
        "data": {
            "type": "nodes",
            "attributes": {
                "title": f"[TECS-L] {paper['title']}",
                "category": "project",
                "description": paper.get("description", ""),
                "tags": paper.get("keywords", []),
            }
        }
    }
    r = requests.post(f"{OSF_API}/nodes/", headers=headers, json=node_data)
    if r.status_code >= 400:
        print(f"  [{pid}] ❌ OSF 노드 생성 실패: {r.status_code}")
        return None

    node_id = r.json()["data"]["id"]

    # Upload files
    upload_url = f"https://files.osf.io/v1/resources/{node_id}/providers/osfstorage/"
    for f in files:
        with open(f, "rb") as fp:
            requests.put(f"{upload_url}?kind=file&name={f.name}",
                         data=fp,
                         headers={"Authorization": f"Bearer {token}"})

    print(f"  [{pid}] ✅ OSF — https://osf.io/{node_id}/")
    return {"paper_id": pid, "node_id": node_id, "url": f"https://osf.io/{node_id}/"}


# ═══════════════════════════════════════════════════════════
# Commands
# ═══════════════════════════════════════════════════════════

def cmd_status():
    """전체 논문 제출 현황 테이블."""
    manifest = load_manifest()
    submitted = load_submitted()
    alien = load_alien_indices()

    all_papers = []
    for repo_key, papers in manifest["papers"].items():
        for p in papers:
            all_papers.append((repo_key, p))

    z_done, o_done, z_miss, o_miss = 0, 0, 0, 0

    print("=" * 100)
    print(f"{'ID':25s} {'Zenodo':10s} {'OSF':10s} {'🛸':4s} {'섹션':12s} {'제목':40s}")
    print("-" * 100)

    for repo_key, p in all_papers:
        pid = p["id"]
        sub = submitted.get(pid, {})
        has_z = "✅" if "zenodo" in sub else "❌"
        has_o = "✅" if "osf" in sub else "❌"
        section = PAPER_SECTION_MAP.get(pid, "?")
        ufo = alien.get(section, "?")
        title = p["title"][:38]

        if "zenodo" in sub:
            z_done += 1
        else:
            z_miss += 1
        if "osf" in sub:
            o_done += 1
        else:
            o_miss += 1

        print(f"{pid:25s} {has_z:10s} {has_o:10s} {str(ufo):4s} {section:12s} {title}")

    print("=" * 100)
    print(f"합계: {len(all_papers)}편")
    print(f"  Zenodo: {z_done} 제출 / {z_miss} 미제출")
    print(f"  OSF:    {o_done} 제출 / {o_miss} 미제출")

    # 🛸10 게이트 현황
    sections_at_10 = [s for s, v in alien.items() if v >= 10]
    print(f"\n🛸10 달성 섹션: {len(sections_at_10)}개 — {', '.join(sections_at_10)}")


def cmd_submit(paper_id: str, dry_run: bool = False, platforms=("zenodo", "osf")):
    """특정 논문 제출."""
    manifest = load_manifest()
    submitted = load_submitted()

    target = None
    target_repo = None
    for repo_key, papers in manifest["papers"].items():
        for p in papers:
            if p["id"] == paper_id:
                target = p
                target_repo = repo_key
                break

    if not target:
        print(f"❌ {paper_id} 매니페스트에 없음")
        return

    results = {"zenodo": [], "osf": []}

    if "zenodo" in platforms:
        if paper_id in submitted and "zenodo" in submitted[paper_id]:
            print(f"  [{paper_id}] Zenodo 이미 제출됨 — skip")
        elif dry_run:
            print(f"  [{paper_id}] DRY RUN Zenodo — {target['title'][:60]}")
        else:
            token = get_token("zenodo")
            if token:
                r = upload_zenodo(target, target_repo, token, manifest["metadata"])
                if r:
                    results["zenodo"].append(r)

    if "osf" in platforms:
        if paper_id in submitted and "osf" in submitted[paper_id]:
            print(f"  [{paper_id}] OSF 이미 제출됨 — skip")
        elif dry_run:
            print(f"  [{paper_id}] DRY RUN OSF — {target['title'][:60]}")
        else:
            token = get_token("osf")
            if token:
                r = upload_osf(target, target_repo, token)
                if r:
                    results["osf"].append(r)

    return results


def cmd_submit_all(dry_run: bool = False):
    """미제출 논문 전부 제출."""
    manifest = load_manifest()
    submitted = load_submitted()
    alien = load_alien_indices()

    zenodo_token = get_token("zenodo") if not dry_run else ""
    osf_token = get_token("osf") if not dry_run else ""

    new_zenodo = []
    new_osf = []
    skipped = 0

    for repo_key, papers in manifest["papers"].items():
        for p in papers:
            pid = p["id"]
            sub = submitted.get(pid, {})

            # 🛸10 게이트 체크
            section = PAPER_SECTION_MAP.get(pid, "")
            ufo = alien.get(section, 0)
            if ufo < 10:
                print(f"  [{pid}] ⏳ 🛸{ufo} < 10 — 대기 ({section})")
                skipped += 1
                continue

            files = collect_files(p, repo_key)
            if not files:
                print(f"  [{pid}] SKIP — 파일 없음")
                skipped += 1
                continue

            # Zenodo
            if "zenodo" not in sub:
                if dry_run:
                    print(f"  [{pid}] DRY Zenodo — {p['title'][:55]}")
                    new_zenodo.append({"paper_id": pid, "doi": "DRY"})
                else:
                    r = upload_zenodo(p, repo_key, zenodo_token, manifest["metadata"])
                    if r:
                        new_zenodo.append(r)
                    time.sleep(1.5)  # rate limit

            # OSF
            if "osf" not in sub:
                if dry_run:
                    print(f"  [{pid}] DRY OSF — {p['title'][:55]}")
                    new_osf.append({"paper_id": pid, "node_id": "DRY"})
                else:
                    r = upload_osf(p, repo_key, osf_token)
                    if r:
                        new_osf.append(r)
                    time.sleep(1.0)

    # Save results
    if not dry_run and (new_zenodo or new_osf):
        out = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "zenodo": new_zenodo,
            "osf": new_osf,
        }
        outpath = RESULTS_DIR / f"upload-results-batch-{time.strftime('%Y%m%d-%H%M%S')}.json"
        with open(outpath, "w") as f:
            json.dump(out, f, indent=2, ensure_ascii=False)
        print(f"\n💾 결과 저장: {outpath}")

    print(f"\n{'DRY RUN ' if dry_run else ''}완료:")
    print(f"  Zenodo 신규: {len(new_zenodo)}")
    print(f"  OSF 신규:    {len(new_osf)}")
    print(f"  스킵:        {skipped}")


def cmd_gate(dry_run: bool = False):
    """🛸10 게이트 체크 + 자동 제출.

    products.json에서 alien_index >= 10인 섹션에 매핑된 논문만 제출.
    """
    alien = load_alien_indices()
    submitted = load_submitted()
    manifest = load_manifest()

    print("🛸 외계인지수 게이트 체크")
    print("=" * 60)

    eligible = []
    blocked = []

    for repo_key, papers in manifest["papers"].items():
        for p in papers:
            pid = p["id"]
            section = PAPER_SECTION_MAP.get(pid, "")
            ufo = alien.get(section, 0)
            sub = submitted.get(pid, {})

            needs_zenodo = "zenodo" not in sub
            needs_osf = "osf" not in sub

            if not needs_zenodo and not needs_osf:
                continue  # already fully submitted

            if ufo >= 10:
                eligible.append((repo_key, p, needs_zenodo, needs_osf))
            else:
                blocked.append((pid, section, ufo, needs_zenodo, needs_osf))

    # Report blocked
    if blocked:
        print(f"\n⏳ 🛸<10 대기 ({len(blocked)}편):")
        for pid, sec, ufo, nz, no in blocked[:10]:
            platforms = []
            if nz:
                platforms.append("Z")
            if no:
                platforms.append("O")
            print(f"  {pid:25s} {sec:12s} 🛸{ufo:2d} 필요: {'+'.join(platforms)}")
        if len(blocked) > 10:
            print(f"  ... +{len(blocked)-10}편")

    # Report & submit eligible
    print(f"\n✅ 🛸10 제출 대상 ({len(eligible)}편):")
    if not eligible:
        print("  전부 제출 완료!")
        return

    zenodo_token = get_token("zenodo") if not dry_run else ""
    osf_token = get_token("osf") if not dry_run else ""

    new_results = {"zenodo": [], "osf": []}

    for repo_key, p, needs_z, needs_o in eligible:
        pid = p["id"]
        title = p["title"][:50]

        if dry_run:
            platforms = []
            if needs_z:
                platforms.append("Zenodo")
            if needs_o:
                platforms.append("OSF")
            print(f"  [{pid}] DRY → {'+'.join(platforms)} — {title}")
        else:
            if needs_z and zenodo_token:
                r = upload_zenodo(p, repo_key, zenodo_token, manifest["metadata"])
                if r:
                    new_results["zenodo"].append(r)
                time.sleep(1.5)
            if needs_o and osf_token:
                r = upload_osf(p, repo_key, osf_token)
                if r:
                    new_results["osf"].append(r)
                time.sleep(1.0)

    if not dry_run and (new_results["zenodo"] or new_results["osf"]):
        outpath = RESULTS_DIR / f"upload-results-gate-{time.strftime('%Y%m%d-%H%M%S')}.json"
        with open(outpath, "w") as f:
            json.dump(new_results, f, indent=2, ensure_ascii=False)
        print(f"\n💾 {outpath}")

    print(f"\n{'DRY RUN ' if dry_run else ''}결과: Zenodo {len(new_results['zenodo'])} / OSF {len(new_results['osf'])}")


# ═══════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="논문 제출 관리자")
    parser.add_argument("command", choices=["status", "submit", "submit-all", "gate"])
    parser.add_argument("paper_id", nargs="?", help="submit 명령 시 논문 ID")
    parser.add_argument("--dry-run", action="store_true", help="시뮬레이션만")
    args = parser.parse_args()

    if args.command == "status":
        cmd_status()
    elif args.command == "submit":
        if not args.paper_id:
            print("usage: submission_manager.py submit <paper_id>")
            sys.exit(1)
        cmd_submit(args.paper_id, dry_run=args.dry_run)
    elif args.command == "submit-all":
        cmd_submit_all(dry_run=args.dry_run)
    elif args.command == "gate":
        cmd_gate(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
