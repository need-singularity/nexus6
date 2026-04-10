#!/usr/bin/env python3
"""Batch upload all TECS-L papers to Zenodo, OSF, and prepare arXiv packages.

Supports 3 platforms:
  1. Zenodo   — Direct API upload (sandbox or production)
  2. OSF      — Preprints API upload (Google Scholar indexed, no review)
  3. arXiv    — Generate submission packages (manual upload, needs endorsement)

Usage:
    # Upload ALL papers to Zenodo sandbox
    python3 zenodo/batch_upload.py --platform zenodo --sandbox --all

    # Upload specific paper
    python3 zenodo/batch_upload.py --platform zenodo --sandbox --paper P-004

    # Upload to OSF Preprints
    python3 zenodo/batch_upload.py --platform osf --all

    # Generate arXiv packages (tar.gz per paper)
    python3 zenodo/batch_upload.py --platform arxiv --all

    # Dry run (show what would be uploaded)
    python3 zenodo/batch_upload.py --platform zenodo --sandbox --all --dry-run

    # List all papers in manifest
    python3 zenodo/batch_upload.py --list
"""

import argparse
import json
import os
import sys
import tarfile
import time
from pathlib import Path

try:
    import requests
except ImportError:
    print("pip install requests")
    sys.exit(1)

ROOT = Path(__file__).parent.parent  # TECS-L root
MANIFEST = Path(__file__).parent / "manifest.json"

# Token paths
ZENODO_TOKEN_PATH = ROOT / ".local" / "zenodo_token"
ZENODO_SANDBOX_TOKEN_PATH = ROOT / ".local" / "zenodo_sandbox_token"
OSF_TOKEN_PATH = ROOT / ".local" / "osf_token"

# API URLs
ZENODO_API = "https://zenodo.org/api"
ZENODO_SANDBOX_API = "https://sandbox.zenodo.org/api"
OSF_API = "https://api.osf.io/v2"

REPO_ROOTS = {
    "tecs-l": ROOT,
    "anima": ROOT.parent / "anima",
    "sedi": ROOT.parent / "sedi",
    "papers": Path.home() / "Dev" / "papers",
}


def load_manifest():
    with open(MANIFEST) as f:
        return json.load(f)


def get_token(platform: str, sandbox: bool = False) -> str:
    if platform == "zenodo":
        env_var = "ZENODO_SANDBOX_TOKEN" if sandbox else "ZENODO_TOKEN"
        path = ZENODO_SANDBOX_TOKEN_PATH if sandbox else ZENODO_TOKEN_PATH
    elif platform == "osf":
        env_var = "OSF_TOKEN"
        path = OSF_TOKEN_PATH
    else:
        return ""

    token = os.environ.get(env_var)
    if token:
        return token.strip()
    if path.exists():
        return path.read_text().strip()

    host = {
        "zenodo": "sandbox.zenodo.org" if sandbox else "zenodo.org",
        "osf": "osf.io",
    }.get(platform, "")
    print(f"Token not found. Get one at: https://{host}/settings/tokens")
    print(f"  Save to: {path}")
    print(f"  Or: export {env_var}=your_token")
    sys.exit(1)


def resolve_file(paper: dict, repo_key: str) -> Path:
    """Resolve the paper file path."""
    repo_root = REPO_ROOTS.get(repo_key, ROOT)
    filepath = repo_root / paper["file"]
    if filepath.exists():
        return filepath
    # Try from paper's repo field
    if "repo" in paper:
        alt_root = REPO_ROOTS.get(paper["repo"], ROOT)
        alt_path = alt_root / paper["file"]
        if alt_path.exists():
            return alt_path
    return filepath


def collect_paper_files(paper: dict, repo_key: str) -> list[Path]:
    """Collect main file + any existing supplementary files."""
    files = []
    main = resolve_file(paper, repo_key)
    if main.exists():
        files.append(main)
    for extra in paper.get("existing", []):
        p = REPO_ROOTS.get(repo_key, ROOT) / extra
        if p.exists():
            files.append(p)
    return files


def all_papers(manifest: dict) -> list[tuple[str, dict]]:
    """Yield (repo_key, paper) for all papers."""
    result = []
    for repo_key, papers in manifest["papers"].items():
        for paper in papers:
            result.append((repo_key, paper))
    return result


# ─── Zenodo ───

def zenodo_upload(paper: dict, repo_key: str, token: str, base_url: str, dry_run: bool):
    pid = paper["id"]
    title = paper["title"]
    files = collect_paper_files(paper, repo_key)

    if not files:
        print(f"  [{pid}] SKIP — no files found: {paper['file']}")
        return None

    meta = {
        "title": title,
        "upload_type": "publication",
        "publication_type": "preprint",
        "description": paper.get("description", f"TECS-L preprint: {title}"),
        "creators": [{"name": manifest_data["metadata"]["author"]}],
        "access_right": "open",
        "license": "cc-by-4.0",
        "keywords": paper.get("keywords", []),
    }

    if dry_run:
        print(f"  [{pid}] DRY RUN — {title}")
        print(f"         Files: {[f.name for f in files]}")
        print(f"         Keywords: {meta['keywords']}")
        return None

    print(f"  [{pid}] Creating deposition...")
    r = requests.post(f"{base_url}/deposit/depositions",
                      params={"access_token": token}, json={})
    if r.status_code >= 400:
        print(f"  [{pid}] FAILED create: {r.status_code} {r.text[:100]}")
        return None

    dep = r.json()
    dep_id = dep["id"]
    bucket = dep["links"]["bucket"]
    doi = dep["metadata"].get("prereserve_doi", {}).get("doi", "N/A")

    # Set metadata
    r = requests.put(f"{base_url}/deposit/depositions/{dep_id}",
                     params={"access_token": token},
                     json={"metadata": meta},
                     headers={"Content-Type": "application/json"})
    if r.status_code >= 400:
        print(f"  [{pid}] WARN metadata: {r.status_code}")

    # Upload files
    for f in files:
        with open(f, "rb") as fp:
            r = requests.put(f"{bucket}/{f.name}",
                             data=fp,
                             params={"access_token": token},
                             headers={"Content-Type": "application/octet-stream"})
        status = "ok" if r.status_code < 400 else f"FAIL({r.status_code})"
        print(f"         {f.name} ({f.stat().st_size:,}B) — {status}")

    env = "sandbox.zenodo.org" if "sandbox" in base_url else "zenodo.org"
    print(f"  [{pid}] Done — DOI: {doi} — https://{env}/deposit/{dep_id}")
    return {"id": dep_id, "doi": doi, "paper_id": pid}


# ─── OSF Preprints ───

def osf_upload(paper: dict, repo_key: str, token: str, dry_run: bool):
    pid = paper["id"]
    title = paper["title"]
    files = collect_paper_files(paper, repo_key)

    if not files:
        print(f"  [{pid}] SKIP — no files found")
        return None

    if dry_run:
        print(f"  [{pid}] DRY RUN (OSF) — {title}")
        print(f"         Files: {[f.name for f in files]}")
        return None

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/vnd.api+json",
    }

    # Step 1: Create OSF project (node)
    print(f"  [{pid}] Creating OSF node...")
    node_data = {
        "data": {
            "type": "nodes",
            "attributes": {
                "title": f"[TECS-L] {title}",
                "category": "project",
                "description": paper.get("description", ""),
                "tags": paper.get("keywords", []),
            }
        }
    }
    r = requests.post(f"{OSF_API}/nodes/", headers=headers, json=node_data)
    if r.status_code >= 400:
        print(f"  [{pid}] FAILED node create: {r.status_code} {r.text[:200]}")
        return None

    node = r.json()
    node_id = node["data"]["id"]
    print(f"         Node: {node_id} — https://osf.io/{node_id}/")

    # Step 2: Upload files to OSF Storage
    upload_url = f"https://files.osf.io/v1/resources/{node_id}/providers/osfstorage/"
    for f in files:
        print(f"         Uploading {f.name}...", end=" ", flush=True)
        with open(f, "rb") as fp:
            r = requests.put(
                f"{upload_url}?kind=file&name={f.name}",
                data=fp,
                headers={"Authorization": f"Bearer {token}"},
            )
        print("ok" if r.status_code < 400 else f"FAIL({r.status_code})")

    # Step 3: Create preprint
    print(f"  [{pid}] Creating preprint...")
    preprint_data = {
        "data": {
            "type": "preprints",
            "attributes": {
                "title": title,
                "description": paper.get("description", ""),
                "tags": paper.get("keywords", []),
                "is_published": False,  # Draft first
            },
            "relationships": {
                "node": {"data": {"type": "nodes", "id": node_id}},
                "provider": {"data": {"type": "providers", "id": "osf"}},
            }
        }
    }
    r = requests.post(f"{OSF_API}/preprints/", headers=headers, json=preprint_data)
    if r.status_code < 400:
        pp = r.json()
        pp_id = pp["data"]["id"]
        print(f"  [{pid}] Preprint draft: https://osf.io/preprints/osf/{pp_id}")
        return {"node_id": node_id, "preprint_id": pp_id, "paper_id": pid}
    else:
        print(f"  [{pid}] Preprint create failed: {r.status_code}")
        print(f"         Node still available: https://osf.io/{node_id}/")
        return {"node_id": node_id, "paper_id": pid}


# ─── arXiv Package ───

def arxiv_package(paper: dict, repo_key: str, output_dir: Path, dry_run: bool):
    pid = paper["id"]
    title = paper["title"]
    files = collect_paper_files(paper, repo_key)

    if not files:
        print(f"  [{pid}] SKIP — no files found")
        return None

    pkg_name = f"{pid.lower().replace(' ', '-')}"
    pkg_dir = output_dir / pkg_name

    if dry_run:
        print(f"  [{pid}] DRY RUN (arXiv) — {pkg_dir}")
        return None

    pkg_dir.mkdir(parents=True, exist_ok=True)

    # Copy files
    for f in files:
        import shutil
        dest = pkg_dir / f.name
        shutil.copy2(f, dest)

    # Create metadata file
    meta_content = f"""% arXiv submission metadata
% Title: {title}
% Authors: {manifest_data['metadata']['author']}
% Category: {arxiv_category(paper)}
% Keywords: {', '.join(paper.get('keywords', []))}
% Abstract: {paper.get('description', '')}
%
% NOTE: arXiv requires endorsement for first-time submitters.
% Get endorsement: https://arxiv.org/help/endorsement
% Manual upload: https://arxiv.org/submit
%
% This package contains the preprint files ready for submission.
% For LaTeX submissions, convert .md to .tex first:
%   pandoc {files[0].name} -o main.tex
"""
    (pkg_dir / "00-arxiv-metadata.txt").write_text(meta_content)

    # Create tar.gz
    tar_path = output_dir / f"{pkg_name}.tar.gz"
    with tarfile.open(tar_path, "w:gz") as tar:
        for f in pkg_dir.iterdir():
            tar.add(f, arcname=f"{pkg_name}/{f.name}")

    size = tar_path.stat().st_size
    print(f"  [{pid}] Package: {tar_path.name} ({size:,}B, {len(files)} files)")
    return {"package": str(tar_path), "paper_id": pid}


def arxiv_category(paper: dict) -> str:
    """Guess arXiv category from keywords."""
    kw = " ".join(paper.get("keywords", []) + [paper.get("target_venue", "")]).lower()
    if any(w in kw for w in ["number-theory", "perfect-number", "arithmetic", "divisor", "egyptian"]):
        return "math.NT"
    if any(w in kw for w in ["algebra", "galois", "group"]):
        return "math.GR"
    if any(w in kw for w in ["particle", "qcd", "higgs", "fermion", "baryon", "quark", "cern"]):
        return "hep-ph"
    if any(w in kw for w in ["string-theory", "lie-algebra", "E8", "anomaly"]):
        return "hep-th"
    if any(w in kw for w in ["cosmolog", "hubble", "cmb", "dark-matter"]):
        return "astro-ph.CO"
    if any(w in kw for w in ["quantum", "tsirelson", "bell"]):
        return "quant-ph"
    if any(w in kw for w in ["consciousness", "IIT", "phi", "neuroscience"]):
        return "q-bio.NC"
    if any(w in kw for w in ["neural", "mixture", "language-model", "training", "efficient"]):
        return "cs.LG"
    if any(w in kw for w in ["persistent-homology", "topolog"]):
        return "cs.LG"
    return "cs.AI"


# ─── Main ───

manifest_data = None


def main():
    global manifest_data

    parser = argparse.ArgumentParser(description="Batch upload TECS-L papers")
    parser.add_argument("--platform", choices=["zenodo", "osf", "arxiv"], default="zenodo")
    parser.add_argument("--sandbox", action="store_true", help="Use Zenodo sandbox")
    parser.add_argument("--all", action="store_true", help="Upload all papers")
    parser.add_argument("--paper", help="Upload specific paper by ID (e.g., P-004, PA-01)")
    parser.add_argument("--repo", choices=["tecs-l", "anima", "sedi"], help="Filter by repo")
    parser.add_argument("--tier", type=int, help="Filter by tier (1, 2, 3)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be uploaded")
    parser.add_argument("--list", action="store_true", help="List all papers")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between uploads (sec)")

    args = parser.parse_args()
    manifest_data = load_manifest()

    papers = all_papers(manifest_data)

    # Filters
    if args.paper:
        papers = [(r, p) for r, p in papers if p["id"] == args.paper]
    if args.repo:
        papers = [(r, p) for r, p in papers if r == args.repo]
    if args.tier:
        papers = [(r, p) for r, p in papers if p.get("tier") == args.tier]

    if args.list:
        print(f"\n{'ID':<8} {'Tier':<5} {'Repo':<8} {'Title':<65} {'Venue'}")
        print("=" * 120)
        for repo_key, paper in papers:
            repo = paper.get("repo", repo_key)
            print(f"{paper['id']:<8} T{paper.get('tier', '?'):<4} {repo:<8} {paper['title'][:63]:<65} {paper.get('target_venue', '')}")
        print(f"\nTotal: {len(papers)} papers")
        return

    if not args.all and not args.paper:
        parser.print_help()
        print("\nUse --all or --paper ID")
        return

    print(f"\n{'='*60}")
    print(f"Platform: {args.platform.upper()}" + (" (SANDBOX)" if args.sandbox else ""))
    print(f"Papers:   {len(papers)}")
    print(f"Dry run:  {args.dry_run}")
    print(f"{'='*60}\n")

    results = []

    if args.platform == "zenodo":
        token = get_token("zenodo", args.sandbox)
        base_url = ZENODO_SANDBOX_API if args.sandbox else ZENODO_API
        for i, (repo_key, paper) in enumerate(papers):
            result = zenodo_upload(paper, repo_key, token, base_url, args.dry_run)
            if result:
                results.append(result)
            if i < len(papers) - 1 and not args.dry_run:
                time.sleep(args.delay)

    elif args.platform == "osf":
        token = get_token("osf")
        for i, (repo_key, paper) in enumerate(papers):
            result = osf_upload(paper, repo_key, token, args.dry_run)
            if result:
                results.append(result)
            if i < len(papers) - 1 and not args.dry_run:
                time.sleep(args.delay)

    elif args.platform == "arxiv":
        output_dir = ROOT / "zenodo" / "arxiv-packages"
        output_dir.mkdir(parents=True, exist_ok=True)
        for repo_key, paper in papers:
            result = arxiv_package(paper, repo_key, output_dir, args.dry_run)
            if result:
                results.append(result)

    # Summary
    print(f"\n{'='*60}")
    print(f"Completed: {len(results)}/{len(papers)}")
    if results and not args.dry_run:
        print("\nResults:")
        for r in results:
            print(f"  {r.get('paper_id', '?')}: {r.get('doi') or r.get('preprint_id') or r.get('package', 'done')}")

    # Save results
    if results and not args.dry_run:
        results_file = ROOT / "zenodo" / f"upload-results-{args.platform}.json"
        with open(results_file, "w") as f:
            json.dump({"platform": args.platform, "sandbox": args.sandbox, "results": results}, f, indent=2)
        print(f"\nResults saved: {results_file}")


if __name__ == "__main__":
    main()
