#!/usr/bin/env python3
"""Upload 8 draft papers to Zenodo (production), OSF, and generate arXiv packages."""

import json
import os
import shutil
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
PAPERS_ROOT = ROOT.parent / "papers"

ZENODO_API = "https://zenodo.org/api"
OSF_API = "https://api.osf.io/v2"

ZENODO_TOKEN = (ROOT / ".local" / "zenodo_token").read_text().strip()
OSF_TOKEN = (ROOT / ".local" / "osf_token").read_text().strip()

AUTHOR = "Park, Min Woo"
AFFILIATION = "Independent Researcher"

# The 8 draft papers
DRAFTS = [
    {
        "id": "P-NEW-1",
        "title": "The Unique Prime Pair: Why (p-1)(q-1)=2 Makes Six Universal",
        "md": "tecs-l/P-NEW-prime-pair-universality.md",
        "tex": "tecs-l/P-NEW-prime-pair-universality.tex",
        "keywords": ["prime-pair", "perfect-numbers", "universality", "number-theory"],
        "arxiv_cat": "math.NT",
        "abstract": "Why (p-1)(q-1)=2 makes six universal among perfect numbers. The unique prime pair (2,3) gives n=6 properties no other even perfect number can possess.",
    },
    {
        "id": "P-NEW-2",
        "title": "Sixty-Eight Ways to Be Six: Arithmetic Identities Uniquely Satisfied by the First Perfect Number",
        "md": "tecs-l/P-NEW-68-ways-to-be-six.md",
        "tex": "tecs-l/P-NEW-68-ways-to-be-six.tex",
        "keywords": ["perfect-numbers", "arithmetic-identities", "uniqueness", "n=6"],
        "arxiv_cat": "math.NT",
        "abstract": "68 arithmetic identities uniquely satisfied by n=6 among all positive integers. Each identity uses standard number-theoretic functions.",
    },
    {
        "id": "P-NEW-3",
        "title": "Consonance, Crystals, and Orbits: The phi(n) <= 2 Filter Across Domains",
        "md": "tecs-l/P-NEW-consonance-crystals-orbits.md",
        "tex": "tecs-l/P-NEW-consonance-crystals-orbits.tex",
        "keywords": ["consonance", "crystals", "orbits", "totient", "cross-domain"],
        "arxiv_cat": "math.NT",
        "abstract": "The Euler totient filter phi(n)<=2 selects exactly {1,2,3,4,6}, connecting musical consonance, crystallographic symmetry, and orbital mechanics.",
    },
    {
        "id": "P-NOBEL",
        "title": "The Arithmetic Necessity of the Standard Model: Particle Physics from the First Perfect Number",
        "md": "tecs-l/P-NOBEL-SM-PERFECTION.md",
        "tex": None,
        "keywords": ["Standard-Model", "perfect-numbers", "particle-physics", "unification"],
        "arxiv_cat": "hep-ph",
        "abstract": "The structure of the Standard Model -- its gauge groups, particle content, and mass hierarchies -- emerges from the arithmetic of the first perfect number n=6.",
    },
    {
        "id": "P-CERN",
        "title": "Experimental Proposal: Search for a Narrow Resonance at 37-38 GeV",
        "md": "tecs-l/CERN-PROPOSAL-37GeV.md",
        "tex": None,
        "keywords": ["CERN", "resonance", "37GeV", "prediction", "experimental-proposal"],
        "arxiv_cat": "hep-ph",
        "abstract": "Experimental proposal to search for a narrow resonance at 37-38 GeV in dilepton and diphoton final states at the LHC.",
    },
    {
        "id": "PS-21",
        "title": "Orbital Period Ratios in Multi-Planet Systems and the Arithmetic of the Perfect Number n=6",
        "md": "sedi/PS-21-exoplanet-n6-orbital-ratios.md",
        "tex": None,
        "keywords": ["exoplanets", "orbital-resonances", "period-ratios", "perfect-numbers"],
        "arxiv_cat": "astro-ph.EP",
        "abstract": "Orbital period ratios in multi-planet systems cluster near ratios derived from the divisor arithmetic of the perfect number n=6.",
    },
    {
        "id": "PS-22",
        "title": "Eight Mathematical Signatures of Consciousness: A Detection Framework",
        "md": "sedi/PS-22-consciousness-signal-detection.md",
        "tex": None,
        "keywords": ["consciousness-detection", "integrated-information", "signal-processing"],
        "arxiv_cat": "q-bio.NC",
        "abstract": "Eight mathematical signatures of consciousness derived from n=6 arithmetic, forming a detection framework for consciousness signals.",
    },
    {
        "id": "PS-23",
        "title": "SEDI: A Mathematical Signal Receiver Tuned to the Perfect Number n=6",
        "md": "sedi/PS-23-sedi-architecture.md",
        "tex": None,
        "keywords": ["signal-detection", "perfect-numbers", "SETI", "data-analysis"],
        "arxiv_cat": "astro-ph.IM",
        "abstract": "Architecture of SEDI (Search for Extra-Dimensional Intelligence), a mathematical signal receiver tuned to n=6 arithmetic frequencies.",
    },
]


def zenodo_upload_all():
    """Upload all 8 drafts to Zenodo production and PUBLISH them."""
    print("\n" + "=" * 60)
    print("ZENODO PRODUCTION UPLOAD")
    print("=" * 60)

    results = []
    for paper in DRAFTS:
        pid = paper["id"]
        title = paper["title"]
        md_path = PAPERS_ROOT / paper["md"]

        if not md_path.exists():
            print(f"  [{pid}] SKIP -- file not found: {md_path}")
            continue

        files_to_upload = [md_path]
        if paper.get("tex"):
            tex_path = PAPERS_ROOT / paper["tex"]
            if tex_path.exists():
                files_to_upload.append(tex_path)

        print(f"\n  [{pid}] {title}")
        print(f"         Files: {[f.name for f in files_to_upload]}")

        # 1. Create deposition
        r = requests.post(
            f"{ZENODO_API}/deposit/depositions",
            params={"access_token": ZENODO_TOKEN},
            json={},
        )
        if r.status_code >= 400:
            print(f"  [{pid}] FAILED create: {r.status_code} {r.text[:200]}")
            results.append({"id": pid, "zenodo": "FAILED", "error": r.text[:200]})
            continue

        dep = r.json()
        dep_id = dep["id"]
        bucket = dep["links"]["bucket"]
        doi = dep["metadata"].get("prereserve_doi", {}).get("doi", "N/A")
        print(f"         Deposit: {dep_id}, DOI: {doi}")

        # 2. Set metadata
        meta = {
            "title": title,
            "upload_type": "publication",
            "publication_type": "preprint",
            "description": paper["abstract"],
            "creators": [{"name": AUTHOR, "affiliation": AFFILIATION}],
            "access_right": "open",
            "license": "cc-by-4.0",
            "keywords": paper["keywords"],
        }
        r = requests.put(
            f"{ZENODO_API}/deposit/depositions/{dep_id}",
            params={"access_token": ZENODO_TOKEN},
            json={"metadata": meta},
            headers={"Content-Type": "application/json"},
        )
        if r.status_code >= 400:
            print(f"         WARN metadata: {r.status_code} {r.text[:100]}")

        # 3. Upload files
        for f in files_to_upload:
            with open(f, "rb") as fp:
                r = requests.put(
                    f"{bucket}/{f.name}",
                    data=fp,
                    params={"access_token": ZENODO_TOKEN},
                    headers={"Content-Type": "application/octet-stream"},
                )
            status = "ok" if r.status_code < 400 else f"FAIL({r.status_code})"
            print(f"         {f.name} ({f.stat().st_size:,}B) -- {status}")

        # 4. Publish
        r = requests.post(
            f"{ZENODO_API}/deposit/depositions/{dep_id}/actions/publish",
            params={"access_token": ZENODO_TOKEN},
        )
        if r.status_code < 400:
            final_doi = r.json().get("doi", doi)
            print(f"         PUBLISHED -- DOI: {final_doi}")
            print(f"         URL: https://zenodo.org/records/{dep_id}")
            results.append({"id": pid, "zenodo": "PUBLISHED", "doi": final_doi, "dep_id": dep_id})
        else:
            print(f"         PUBLISH FAILED: {r.status_code} {r.text[:200]}")
            print(f"         Draft URL: https://zenodo.org/deposit/{dep_id}")
            results.append({"id": pid, "zenodo": "DRAFT", "doi": doi, "dep_id": dep_id, "error": r.text[:200]})

        time.sleep(1.5)  # Rate limiting

    return results


def osf_upload_all():
    """Upload all 8 drafts to OSF as project files."""
    print("\n" + "=" * 60)
    print("OSF UPLOAD")
    print("=" * 60)

    headers = {
        "Authorization": f"Bearer {OSF_TOKEN}",
        "Content-Type": "application/vnd.api+json",
    }

    results = []
    for paper in DRAFTS:
        pid = paper["id"]
        title = paper["title"]
        md_path = PAPERS_ROOT / paper["md"]

        if not md_path.exists():
            print(f"  [{pid}] SKIP -- file not found")
            continue

        files_to_upload = [md_path]
        if paper.get("tex"):
            tex_path = PAPERS_ROOT / paper["tex"]
            if tex_path.exists():
                files_to_upload.append(tex_path)

        print(f"\n  [{pid}] {title}")

        # 1. Create OSF node (project)
        node_data = {
            "data": {
                "type": "nodes",
                "attributes": {
                    "title": f"[TECS-L] {title}",
                    "category": "project",
                    "description": paper["abstract"],
                    "tags": paper["keywords"],
                }
            }
        }
        r = requests.post(f"{OSF_API}/nodes/", headers=headers, json=node_data)
        if r.status_code >= 400:
            print(f"  [{pid}] FAILED node create: {r.status_code} {r.text[:300]}")
            results.append({"id": pid, "osf": "FAILED", "error": r.text[:300]})
            time.sleep(1)
            continue

        node = r.json()
        node_id = node["data"]["id"]
        osf_url = f"https://osf.io/{node_id}/"
        print(f"         Node: {node_id} -- {osf_url}")

        # 2. Upload files
        upload_url = f"https://files.osf.io/v1/resources/{node_id}/providers/osfstorage/"
        for f in files_to_upload:
            print(f"         Uploading {f.name}...", end=" ", flush=True)
            with open(f, "rb") as fp:
                r = requests.put(
                    f"{upload_url}?kind=file&name={f.name}",
                    data=fp,
                    headers={"Authorization": f"Bearer {OSF_TOKEN}"},
                )
            print("ok" if r.status_code < 400 else f"FAIL({r.status_code}: {r.text[:100]})")

        results.append({"id": pid, "osf": "UPLOADED", "node_id": node_id, "url": osf_url})
        time.sleep(1)

    return results


def arxiv_package_all():
    """Generate arXiv submission packages for all 8 drafts."""
    print("\n" + "=" * 60)
    print("arXiv PACKAGE GENERATION")
    print("=" * 60)

    output_dir = ROOT / "zenodo" / "arxiv-packages"
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for paper in DRAFTS:
        pid = paper["id"]
        title = paper["title"]
        md_path = PAPERS_ROOT / paper["md"]

        if not md_path.exists():
            print(f"  [{pid}] SKIP -- file not found")
            continue

        pkg_name = pid.lower().replace(" ", "-")
        pkg_dir = output_dir / pkg_name

        # Clean and create
        if pkg_dir.exists():
            shutil.rmtree(pkg_dir)
        pkg_dir.mkdir(parents=True)

        # Copy .md
        shutil.copy2(md_path, pkg_dir / md_path.name)

        # Copy .tex if exists
        has_tex = False
        if paper.get("tex"):
            tex_path = PAPERS_ROOT / paper["tex"]
            if tex_path.exists():
                shutil.copy2(tex_path, pkg_dir / "main.tex")
                has_tex = True

        # Create metadata
        meta_content = f"""% arXiv submission metadata
% Title: {title}
% Authors: {AUTHOR} ({AFFILIATION})
% Category: {paper['arxiv_cat']}
% Keywords: {', '.join(paper['keywords'])}
%
% Abstract: {paper['abstract']}
%
% NOTE: arXiv requires endorsement for first-time submitters.
% Get endorsement: https://arxiv.org/help/endorsement
% Manual upload: https://arxiv.org/submit
%
% {'LaTeX source included (main.tex)' if has_tex else 'No LaTeX source -- convert .md to .tex with: pandoc ' + md_path.name + ' -o main.tex'}
"""
        (pkg_dir / "00-arxiv-metadata.txt").write_text(meta_content)

        # Create tar.gz
        tar_path = output_dir / f"{pkg_name}.tar.gz"
        with tarfile.open(tar_path, "w:gz") as tar:
            for f in sorted(pkg_dir.iterdir()):
                tar.add(f, arcname=f"{pkg_name}/{f.name}")

        size = tar_path.stat().st_size
        n_files = len(list(pkg_dir.iterdir()))
        tex_note = " (has .tex)" if has_tex else " (md only, needs pandoc)"
        print(f"  [{pid}] {tar_path.name} ({size:,}B, {n_files} files){tex_note}")
        results.append({
            "id": pid,
            "arxiv": "PACKAGED",
            "package": str(tar_path),
            "has_tex": has_tex,
            "category": paper["arxiv_cat"],
        })

    return results


def main():
    all_results = {}

    # Platform 1: Zenodo
    zenodo_results = zenodo_upload_all()
    all_results["zenodo"] = zenodo_results

    # Platform 2: OSF
    osf_results = osf_upload_all()
    all_results["osf"] = osf_results

    # Platform 3: arXiv packages
    arxiv_results = arxiv_package_all()
    all_results["arxiv"] = arxiv_results

    # Final summary
    print("\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)
    print(f"\n{'Paper':<10} {'Zenodo':<35} {'OSF':<30} {'arXiv'}")
    print("-" * 110)
    for paper in DRAFTS:
        pid = paper["id"]
        z = next((r for r in zenodo_results if r["id"] == pid), {})
        o = next((r for r in osf_results if r["id"] == pid), {})
        a = next((r for r in arxiv_results if r["id"] == pid), {})

        z_str = f"{z.get('zenodo', 'N/A')} {z.get('doi', '')}"
        o_str = f"{o.get('osf', 'N/A')} {o.get('url', '')}"
        a_str = f"{a.get('arxiv', 'N/A')} {a.get('category', '')}"
        print(f"{pid:<10} {z_str:<35} {o_str:<30} {a_str}")

    # Save combined results
    results_file = ROOT / "zenodo" / "upload-results-8-drafts.json"
    with open(results_file, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nResults saved: {results_file}")


if __name__ == "__main__":
    main()
