#!/usr/bin/env python3
"""TECS-L Paper & Dataset Publisher — Zenodo + OSF Preprints.

Setup:
    # Zenodo tokens
    echo "TOKEN" > .local/zenodo_sandbox_token   # https://sandbox.zenodo.org/account/settings/applications/tokens/new/
    echo "TOKEN" > .local/zenodo_token            # https://zenodo.org/account/settings/applications/tokens/new/

    # OSF tokens
    echo "TOKEN" > .local/osf_test_token          # https://test.osf.io/settings/tokens/  (scope: osf.full_write)
    echo "TOKEN" > .local/osf_token               # https://osf.io/settings/tokens/        (scope: osf.full_write)

Usage:
    # === Zenodo ===
    python3 publish.py zenodo --sandbox upload-paper --title "Title" --files paper.pdf
    python3 publish.py zenodo --sandbox upload-dataset --title "Title" --files data/
    python3 publish.py zenodo --sandbox list
    python3 publish.py zenodo --sandbox publish --id 123456
    python3 publish.py zenodo --sandbox delete --id 123456

    # === OSF Preprints ===
    python3 publish.py osf --test upload --title "Title" --abstract "..." --file paper.pdf --subject Mathematics
    python3 publish.py osf --test list
    python3 publish.py osf --test publish --id abcde
    python3 publish.py osf --test delete --id abcde

    # Production: remove --sandbox / --test flag
"""

import argparse
import os
import sys
from pathlib import Path

try:
    import requests
except ImportError:
    print("pip install requests")
    sys.exit(1)

BASE_DIR = Path(__file__).parent
LOCAL_DIR = BASE_DIR / ".local"

# ============================================================
# Token management
# ============================================================

TOKEN_PATHS = {
    "zenodo": LOCAL_DIR / "zenodo_token",
    "zenodo_sandbox": LOCAL_DIR / "zenodo_sandbox_token",
    "osf": LOCAL_DIR / "osf_token",
    "osf_test": LOCAL_DIR / "osf_test_token",
}

ENV_VARS = {
    "zenodo": "ZENODO_TOKEN",
    "zenodo_sandbox": "ZENODO_SANDBOX_TOKEN",
    "osf": "OSF_TOKEN",
    "osf_test": "OSF_TEST_TOKEN",
}

TOKEN_URLS = {
    "zenodo": "https://zenodo.org/account/settings/applications/tokens/new/",
    "zenodo_sandbox": "https://sandbox.zenodo.org/account/settings/applications/tokens/new/",
    "osf": "https://osf.io/settings/tokens/",
    "osf_test": "https://test.osf.io/settings/tokens/",
}


def get_token(service: str) -> str:
    token = os.environ.get(ENV_VARS[service])
    if token:
        return token.strip()
    path = TOKEN_PATHS[service]
    if path.exists():
        return path.read_text().strip()
    print(f"Token not found for {service}.")
    print(f"  export {ENV_VARS[service]}=your_token")
    print(f"  echo your_token > {path}")
    print(f"  Get token: {TOKEN_URLS[service]}")
    sys.exit(1)


# ============================================================
# Shared utilities
# ============================================================

def collect_files(paths: list[str]) -> list[Path]:
    files = []
    for p in paths:
        path = Path(p)
        if path.is_dir():
            files.extend(f for f in path.rglob("*") if f.is_file())
        elif path.is_file():
            files.append(path)
        else:
            print(f"  Warning: {p} not found, skipping")
    return files


# ============================================================
# Zenodo
# ============================================================

ZENODO_URLS = {
    True: "https://sandbox.zenodo.org/api",
    False: "https://zenodo.org/api",
}


def zenodo_upload(args):
    sandbox = getattr(args, "sandbox", False)
    base = ZENODO_URLS[sandbox]
    token = get_token("zenodo_sandbox" if sandbox else "zenodo")
    host = "sandbox.zenodo.org" if sandbox else "zenodo.org"
    upload_type = "publication" if "paper" in args.zenodo_cmd else "dataset"

    metadata = {
        "title": args.title,
        "upload_type": upload_type,
        "description": args.description or f"TECS-L {upload_type}: {args.title}",
        "creators": [{"name": args.author or "TECS-L Project"}],
        "access_right": "open",
        "license": "cc-by-4.0",
    }
    if upload_type == "publication":
        metadata["publication_type"] = "preprint"
    if args.keywords:
        metadata["keywords"] = args.keywords.split(",")

    print(f"Creating {upload_type} on Zenodo {'(sandbox)' if sandbox else ''}...")
    r = requests.post(f"{base}/deposit/depositions",
                      params={"access_token": token}, json={})
    r.raise_for_status()
    dep = r.json()
    dep_id = dep["id"]
    bucket_url = dep["links"]["bucket"]
    doi = dep["metadata"].get("prereserve_doi", {}).get("doi", "N/A")

    requests.put(f"{base}/deposit/depositions/{dep_id}",
                 params={"access_token": token},
                 json={"metadata": metadata},
                 headers={"Content-Type": "application/json"})

    files = collect_files(args.files)
    if not files:
        print("No files found!")
        return
    print(f"Uploading {len(files)} file(s)...")
    for f in files:
        print(f"  {f.name} ({f.stat().st_size:,} B)...", end=" ", flush=True)
        with open(f, "rb") as fp:
            r = requests.put(f"{bucket_url}/{f.name}", data=fp,
                             params={"access_token": token},
                             headers={"Content-Type": "application/octet-stream"})
        print("ok" if r.status_code < 400 else f"FAILED ({r.status_code})")

    print(f"\n{'='*50}")
    print(f"ID:      {dep_id}")
    print(f"DOI:     {doi}")
    print(f"Edit:    https://{host}/deposit/{dep_id}")
    print(f"Status:  DRAFT")
    print(f"Publish: python3 publish.py zenodo {'--sandbox ' if sandbox else ''}publish --id {dep_id}")


def zenodo_list(args):
    sandbox = getattr(args, "sandbox", False)
    base = ZENODO_URLS[sandbox]
    token = get_token("zenodo_sandbox" if sandbox else "zenodo")
    r = requests.get(f"{base}/deposit/depositions", params={"access_token": token})
    r.raise_for_status()
    deps = r.json()
    if not deps:
        print("No Zenodo depositions.")
        return
    print(f"{'ID':<10} {'Status':<10} {'Title':<50} {'DOI'}")
    print("-" * 85)
    for d in deps:
        s = "published" if d.get("submitted") else "draft"
        t = (d.get("title") or "(none)")[:48]
        doi = d["metadata"].get("doi") or d["metadata"].get("prereserve_doi", {}).get("doi", "")
        print(f"{d['id']:<10} {s:<10} {t:<50} {doi}")


def zenodo_publish(args):
    sandbox = getattr(args, "sandbox", False)
    base = ZENODO_URLS[sandbox]
    token = get_token("zenodo_sandbox" if sandbox else "zenodo")
    if not sandbox:
        print("*** WARNING: Permanent DOI on production Zenodo! ***")
    confirm = input("Type 'yes' to publish: ")
    if confirm.lower() != "yes":
        print("Cancelled.")
        return
    r = requests.post(f"{base}/deposit/depositions/{args.id}/actions/publish",
                      params={"access_token": token})
    if r.status_code < 400:
        doi = r.json().get("doi", "N/A")
        print(f"Published! DOI: {doi}\nURL: https://doi.org/{doi}")
    else:
        print(f"Failed: {r.status_code} {r.text[:200]}")


def zenodo_delete(args):
    sandbox = getattr(args, "sandbox", False)
    base = ZENODO_URLS[sandbox]
    token = get_token("zenodo_sandbox" if sandbox else "zenodo")
    r = requests.delete(f"{base}/deposit/depositions/{args.id}",
                        params={"access_token": token})
    print("Deleted." if r.status_code == 204 else f"Failed: {r.status_code} {r.text[:200]}")


# ============================================================
# OSF Preprints
# ============================================================

OSF_URLS = {
    True: {"api": "https://api.test.osf.io/v2", "files": "https://files.test.osf.io/v1", "web": "https://test.osf.io"},
    False: {"api": "https://api.osf.io/v2", "files": "https://files.osf.io/v1", "web": "https://osf.io"},
}

SUBJECT_ALIASES = {
    "math": "Mathematics", "mathematics": "Mathematics",
    "cs": "Computer Science", "computer science": "Computer Science",
    "physics": "Physical Sciences and Mathematics",
    "ai": "Artificial Intelligence and Robotics",
    "ml": "Artificial Intelligence and Robotics",
    "neuroscience": "Neuroscience and Neurobiology",
}


def osf_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/vnd.api+json"}


def osf_find_subject(api_url: str, headers: dict, query: str) -> list:
    normalized = SUBJECT_ALIASES.get(query.lower(), query)
    r = requests.get(f"{api_url}/providers/preprints/osf/taxonomies/",
                     params={"filter[text]": normalized, "page[size]": 5},
                     headers=headers)
    return r.json().get("data", []) if r.status_code < 400 else []


def osf_upload(args):
    test = getattr(args, "test", False)
    urls = OSF_URLS[test]
    token = get_token("osf_test" if test else "osf")
    headers = osf_headers(token)

    file_path = Path(args.file)
    if not file_path.is_file():
        print(f"File not found: {args.file}")
        sys.exit(1)
    if file_path.suffix.lower() != ".pdf":
        print(f"  Note: OSF prefers PDF. Got {file_path.suffix}. Consider converting.")

    # Step 1: Create node
    print(f"Creating OSF node {'(test)' if test else ''}...")
    node_data = {"data": {"type": "nodes", "attributes": {
        "title": args.title, "category": "project",
        "description": args.abstract or f"TECS-L preprint: {args.title}",
        "public": True,
    }}}
    r = requests.post(f"{urls['api']}/nodes/", json=node_data, headers=headers)
    if r.status_code >= 400:
        print(f"Failed: {r.status_code} {r.text[:300]}")
        sys.exit(1)
    node_id = r.json()["data"]["id"]
    print(f"  Node: {node_id}")

    # Step 2: Upload file via WaterButler
    print(f"  Uploading {file_path.name} ({file_path.stat().st_size:,} B)...", end=" ", flush=True)
    with open(file_path, "rb") as f:
        r = requests.put(f"{urls['files']}/resources/{node_id}/providers/osfstorage/",
                         params={"kind": "file", "name": file_path.name},
                         headers={"Authorization": f"Bearer {token}"},
                         data=f)
    if r.status_code >= 400:
        print(f"FAILED ({r.status_code}: {r.text[:200]})")
        sys.exit(1)
    print("ok")

    # Get file ID from node files
    r = requests.get(f"{urls['api']}/nodes/{node_id}/files/osfstorage/", headers=headers)
    files_list = r.json().get("data", []) if r.status_code < 400 else []
    file_id = files_list[0]["id"] if files_list else None
    if not file_id:
        print("  Could not get file ID. Create preprint manually.")
        print(f"  Node: {urls['web']}/{node_id}/")
        return
    print(f"  File ID: {file_id}")

    # Step 3: Find subject
    subject_data = []
    if args.subject:
        subjects = osf_find_subject(urls["api"], headers, args.subject)
        if subjects:
            subject_data = [[{"id": subjects[0]["id"], "type": "taxonomies"}]]
            print(f"  Subject: {subjects[0]['attributes']['text']}")
        else:
            print(f"  Subject '{args.subject}' not found. Set manually on web.")

    # Step 4: Create preprint (draft)
    print("Creating preprint...")
    pp_data = {"data": {
        "type": "preprints",
        "attributes": {
            "title": args.title,
            "description": args.abstract or f"TECS-L preprint: {args.title}",
            "is_published": False,
        },
        "relationships": {
            "node": {"data": {"type": "nodes", "id": node_id}},
            "provider": {"data": {"type": "providers", "id": "osf"}},
            "primary_file": {"data": {"type": "files", "id": file_id}},
        }
    }}
    if args.keywords:
        pp_data["data"]["attributes"]["tags"] = args.keywords.split(",")

    r = requests.post(f"{urls['api']}/preprints/", json=pp_data, headers=headers)
    if r.status_code >= 400:
        print(f"Failed: {r.status_code} {r.text[:400]}")
        print(f"  Node exists: {urls['web']}/{node_id}/ — create preprint via web UI.")
        return

    preprint_id = r.json()["data"]["id"]

    # Set subjects
    if subject_data:
        requests.patch(f"{urls['api']}/preprints/{preprint_id}/",
                       json={"data": {"type": "preprints", "id": preprint_id,
                                      "relationships": {"subjects": {"data": subject_data}}}},
                       headers=headers)

    print(f"\n{'='*50}")
    print(f"Preprint: {preprint_id}")
    print(f"Node:     {node_id}")
    print(f"Edit:     {urls['web']}/preprints/osf/{preprint_id}")
    print(f"Status:   DRAFT")
    print(f"Publish:  python3 publish.py osf {'--test ' if test else ''}publish --id {preprint_id}")


def osf_list(args):
    test = getattr(args, "test", False)
    urls = OSF_URLS[test]
    token = get_token("osf_test" if test else "osf")
    headers = osf_headers(token)
    r = requests.get(f"{urls['api']}/users/me/preprints/", headers=headers)
    if r.status_code >= 400:
        print(f"Failed: {r.status_code} {r.text[:200]}")
        return
    data = r.json().get("data", [])
    if not data:
        print("No OSF preprints.")
        return
    print(f"{'ID':<12} {'Status':<10} {'Title'}")
    print("-" * 70)
    for pp in data:
        a = pp["attributes"]
        s = "published" if a.get("is_published") else "draft"
        print(f"{pp['id']:<12} {s:<10} {(a.get('title') or '(none)')[:50]}")


def osf_publish(args):
    test = getattr(args, "test", False)
    urls = OSF_URLS[test]
    token = get_token("osf_test" if test else "osf")
    headers = osf_headers(token)
    if not test:
        print("*** WARNING: Published preprints get a DOI and cannot be fully deleted! ***")
    confirm = input("Type 'yes' to publish: ")
    if confirm.lower() != "yes":
        print("Cancelled.")
        return
    r = requests.patch(f"{urls['api']}/preprints/{args.id}/",
                       json={"data": {"type": "preprints", "id": args.id,
                                      "attributes": {"is_published": True}}},
                       headers=headers)
    if r.status_code < 400:
        doi = r.json()["data"]["attributes"].get("doi", "pending")
        print(f"Published! DOI: {doi}\nURL: {urls['web']}/preprints/osf/{args.id}")
    else:
        print(f"Failed: {r.status_code} {r.text[:300]}")
        print("Check: subject set? abstract present? file is PDF?")


def osf_delete(args):
    test = getattr(args, "test", False)
    urls = OSF_URLS[test]
    token = get_token("osf_test" if test else "osf")
    headers = osf_headers(token)
    r = requests.delete(f"{urls['api']}/preprints/{args.id}/", headers=headers)
    if r.status_code == 204:
        print(f"Deleted {args.id}.")
    elif r.status_code == 409:
        print("Cannot delete published preprint. Can only withdraw.")
    else:
        print(f"Failed: {r.status_code} {r.text[:200]}")


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="TECS-L Publisher: Zenodo + OSF Preprints",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="platform")

    # --- Zenodo ---
    zen = sub.add_parser("zenodo", help="Zenodo (DOI + archive)")
    zen.add_argument("--sandbox", action="store_true")
    zs = zen.add_subparsers(dest="zenodo_cmd")
    for name in ("upload-paper", "upload-dataset"):
        p = zs.add_parser(name)
        p.add_argument("--title", required=True)
        p.add_argument("--files", nargs="+", required=True)
        p.add_argument("--author")
        p.add_argument("--description")
        p.add_argument("--keywords", help="Comma-separated")
    zs.add_parser("list")
    zs.add_parser("publish").add_argument("--id", required=True, type=int)
    zs.add_parser("delete").add_argument("--id", required=True, type=int)

    # --- OSF ---
    osf_p = sub.add_parser("osf", help="OSF Preprints (Google Scholar indexed)")
    osf_p.add_argument("--test", action="store_true")
    os_ = osf_p.add_subparsers(dest="osf_cmd")
    ou = os_.add_parser("upload")
    ou.add_argument("--title", required=True)
    ou.add_argument("--file", required=True, help="Primary file (PDF preferred)")
    ou.add_argument("--abstract")
    ou.add_argument("--subject", help="e.g. Mathematics, CS, AI, Physics")
    ou.add_argument("--keywords", help="Comma-separated")
    ou.add_argument("--author")
    os_.add_parser("list")
    os_.add_parser("publish").add_argument("--id", required=True)
    os_.add_parser("delete").add_argument("--id", required=True)

    args = parser.parse_args()
    if not args.platform:
        parser.print_help()
        return

    dispatch = {
        "zenodo": {"upload-paper": zenodo_upload, "upload-dataset": zenodo_upload,
                    "list": zenodo_list, "publish": zenodo_publish, "delete": zenodo_delete},
        "osf": {"upload": osf_upload, "list": osf_list,
                "publish": osf_publish, "delete": osf_delete},
    }

    cmd = getattr(args, "zenodo_cmd", None) or getattr(args, "osf_cmd", None)
    if not cmd:
        parser.print_help()
        return
    dispatch[args.platform][cmd](args)


if __name__ == "__main__":
    main()
