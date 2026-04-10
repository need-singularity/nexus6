#!/usr/bin/env python3
"""
Upload P-DNA-A and P-DNA-B to Zenodo (production) and OSF.
"""

import requests
import json
import os
import sys

ZENODO_TOKEN = open(os.path.expanduser("~/.local/zenodo_token")).read().strip() if os.path.exists(os.path.expanduser("~/.local/zenodo_token")) else open(os.path.expanduser("~/Dev/TECS-L/.local/zenodo_token")).read().strip()
OSF_TOKEN = open(os.path.expanduser("~/Dev/TECS-L/.local/osf_token")).read().strip()

ZENODO_URL = "https://zenodo.org/api"
OSF_URL = "https://api.osf.io/v2"

PAPERS = [
    {
        "id": "P-DNA-A",
        "title": "One Hundred Unique Identities of the First Perfect Number: Arithmetic, Crystallographic, and Compositional Characterizations of n=6",
        "file": os.path.expanduser("~/Dev/papers/tecs-l/P-DNA-A-unique-identities-six.md"),
        "description": "A systematic computational search finds over 100 equations involving standard arithmetic functions that are satisfied uniquely by n=6. Three headline results with complete proofs: (1) sigma(n) = tau(n)(tau(n)-1) holds only for n=6; (2) the divisor set d(n) union {tau(n)} equals the crystallographic restriction set {1,2,3,4,6} only for n=6; (3) all identities derive from 8 independent number-theoretic constraints forming a closed composition web. Infinite parameterized families are proven to exist.",
        "keywords": ["perfect numbers", "arithmetic functions", "number theory", "sigma function", "crystallographic restriction", "divisor function", "unique identities"],
        "subjects": "Number Theory",
    },
    {
        "id": "P-DNA-B",
        "title": "The Ubiquity of Six: A 500-Hypothesis Survey of the Perfect Number Across All Sciences",
        "file": os.path.expanduser("~/Dev/papers/tecs-l/P-DNA-B-ubiquity-of-six.md"),
        "description": "We tested 500 hypotheses across 18 scientific domains asking whether the number 6 and sigma(6)=12 appear as structural constants beyond chance. 66 findings confirmed at GREEN level. Statistical significance: p < 10^-25. Three mathematical root theorems (2D kissing number, honeycomb theorem, sigma=tau(tau-1)) explain >60% of findings. A biology-to-mathematics mapping achieves 100% explanation rate. Anti-evidence (7-fold systems) maps to divisors of the second perfect number 28.",
        "keywords": ["perfect numbers", "hexagonal symmetry", "kissing number", "crystallography", "molecular biology", "interdisciplinary", "number six", "statistical survey"],
        "subjects": "Mathematical Physics",
    },
]

AUTHOR = {
    "name": "Park, Min Woo",
    "affiliation": "Independent Researcher",
    "orcid": None,
}

# ═══════════════════════════════════════════
# ZENODO UPLOAD
# ═══════════════════════════════════════════

def zenodo_upload(paper, sandbox=False):
    base = "https://sandbox.zenodo.org/api" if sandbox else ZENODO_URL
    token = ZENODO_TOKEN
    headers = {"Content-Type": "application/json"}
    params = {"access_token": token}

    print(f"\n{'='*60}")
    print(f"ZENODO {'SANDBOX' if sandbox else 'PRODUCTION'}: {paper['id']}")
    print(f"{'='*60}")

    # 1. Create empty deposit
    print("  Creating deposit...")
    r = requests.post(f"{base}/deposit/depositions", params=params, json={}, headers=headers)
    if r.status_code != 201:
        print(f"  ERROR creating deposit: {r.status_code} {r.text[:200]}")
        return None
    dep = r.json()
    dep_id = dep["id"]
    bucket_url = dep["links"]["bucket"]
    print(f"  Deposit ID: {dep_id}")

    # 2. Upload file
    print(f"  Uploading {os.path.basename(paper['file'])}...")
    filename = os.path.basename(paper["file"])
    with open(paper["file"], "rb") as f:
        r = requests.put(f"{bucket_url}/{filename}", params=params, data=f)
    if r.status_code not in (200, 201):
        print(f"  ERROR uploading: {r.status_code} {r.text[:200]}")
        return dep_id
    print(f"  Uploaded: {r.json().get('size', '?')} bytes")

    # 3. Set metadata
    print("  Setting metadata...")
    metadata = {
        "metadata": {
            "title": paper["title"],
            "upload_type": "publication",
            "publication_type": "preprint",
            "description": paper["description"],
            "creators": [{"name": AUTHOR["name"], "affiliation": AUTHOR["affiliation"]}],
            "keywords": paper["keywords"],
            "access_right": "open",
            "license": "cc-by-4.0",
            "notes": "Part of the TECS-L Consciousness Continuity Engine project. GitHub: https://github.com/need-singularity/TECS-L",
        }
    }
    r = requests.put(f"{base}/deposit/depositions/{dep_id}", params=params, json=metadata, headers=headers)
    if r.status_code != 200:
        print(f"  ERROR setting metadata: {r.status_code} {r.text[:200]}")
        return dep_id
    print("  Metadata set.")

    # 4. Publish
    print("  Publishing...")
    r = requests.post(f"{base}/deposit/depositions/{dep_id}/actions/publish", params=params)
    if r.status_code != 202:
        print(f"  ERROR publishing: {r.status_code} {r.text[:200]}")
        print(f"  Deposit saved as DRAFT: {dep_id}")
        return dep_id
    pub = r.json()
    doi = pub.get("doi", "N/A")
    url = pub.get("links", {}).get("html", "N/A")
    print(f"  ✓ PUBLISHED!")
    print(f"  DOI: {doi}")
    print(f"  URL: {url}")
    return {"dep_id": dep_id, "doi": doi, "url": url}


# ═══════════════════════════════════════════
# OSF UPLOAD (Preprints)
# ═══════════════════════════════════════════

def osf_upload(paper):
    """Upload to OSF as a preprint (if API access works)."""
    headers = {
        "Authorization": f"Bearer {OSF_TOKEN}",
        "Content-Type": "application/json",
    }

    print(f"\n{'='*60}")
    print(f"OSF: {paper['id']}")
    print(f"{'='*60}")

    # Test token
    print("  Testing OSF token...")
    r = requests.get(f"{OSF_URL}/users/me/", headers=headers)
    if r.status_code != 200:
        print(f"  ERROR: OSF token invalid or account not approved ({r.status_code})")
        print(f"  Response: {r.text[:200]}")
        return None
    user = r.json()["data"]["attributes"]
    print(f"  Logged in as: {user.get('full_name', 'unknown')}")

    # Create a new OSF project (not preprint — preprints need provider approval)
    print("  Creating OSF project...")
    project_data = {
        "data": {
            "type": "nodes",
            "attributes": {
                "title": paper["title"],
                "category": "project",
                "description": paper["description"],
                "public": True,
                "tags": paper["keywords"],
            }
        }
    }
    r = requests.post(f"{OSF_URL}/nodes/", headers=headers, json=project_data)
    if r.status_code not in (200, 201):
        print(f"  ERROR creating project: {r.status_code} {r.text[:300]}")
        return None

    node = r.json()["data"]
    node_id = node["id"]
    print(f"  Project created: {node_id}")
    print(f"  URL: https://osf.io/{node_id}/")

    # Upload file to project
    print(f"  Uploading file...")
    upload_url = f"https://files.osf.io/v1/resources/{node_id}/providers/osfstorage/"
    filename = os.path.basename(paper["file"])
    with open(paper["file"], "rb") as f:
        r = requests.put(
            f"{upload_url}?kind=file&name={filename}",
            headers={"Authorization": f"Bearer {OSF_TOKEN}"},
            data=f,
        )
    if r.status_code in (200, 201):
        print(f"  ✓ File uploaded!")
    else:
        print(f"  ERROR uploading file: {r.status_code} {r.text[:200]}")

    return {"node_id": node_id, "url": f"https://osf.io/{node_id}/"}


# ═══════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════

if __name__ == "__main__":
    results = {"zenodo": [], "osf": []}

    for paper in PAPERS:
        if not os.path.exists(paper["file"]):
            print(f"  ERROR: {paper['file']} not found!")
            continue

        # Zenodo production
        z = zenodo_upload(paper, sandbox=False)
        results["zenodo"].append({"paper": paper["id"], "result": z})

        # OSF
        o = osf_upload(paper)
        results["osf"].append({"paper": paper["id"], "result": o})

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for platform in ["zenodo", "osf"]:
        print(f"\n  {platform.upper()}:")
        for r in results[platform]:
            res = r["result"]
            if isinstance(res, dict):
                doi = res.get("doi", "N/A")
                url = res.get("url", "N/A")
                print(f"    {r['paper']}: DOI={doi}  URL={url}")
            else:
                print(f"    {r['paper']}: {res}")

    # Save results
    out_path = os.path.expanduser("~/Dev/TECS-L/zenodo/upload-results-dna.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n  Results saved to {out_path}")
