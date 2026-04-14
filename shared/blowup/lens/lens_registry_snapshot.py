#!/usr/bin/env python3
# @hexa-first-exempt — hexa stage1 runtime bug 우회 (LENS-P2 precedent)
"""
lens_registry_snapshot.py — LENS-P3-2

lens_registry.json 스냅샷 + rollback 골화.

Subcommands:
  snapshot [--out DIR]                    tar+gz lens_registry.json, sha256 기록
  list [--dir DIR]                        스냅샷 나열 (date/sha/size)
  rollback <snapshot_path> [--dry-run]    sha 검증 → 추출 → 원자적 교체

Ossify: shared/lockdown/lockdown.json 의 "lens_snapshots" 키에 append.
        lockdown 파싱 실패 시 shared/lockdown/lens_snapshots.json 로 fallback.

CLI:
  python3 lens_registry_snapshot.py snapshot
  python3 lens_registry_snapshot.py list
  python3 lens_registry_snapshot.py rollback /path/to/snap.tar.gz --dry-run
"""

import hashlib
import io
import json
import os
import sys
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path("/Users/ghost/Dev/nexus")
REG_PATH = ROOT / "shared/config/lens_registry.json"
SNAP_DIR = ROOT / "shared/lockdown/snapshots"
LOCKDOWN_PATH = ROOT / "shared/lockdown/lockdown.json"
FALLBACK_OSSIFY = ROOT / "shared/lockdown/lens_snapshots.json"
EVIDENCE_PATH = ROOT / "shared/discovery/lens_p3_2_snapshot_2026-04-14.json"


def sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def atomic_write_bytes(path: Path, data: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def atomic_write_text(path: Path, text: str):
    atomic_write_bytes(path, text.encode("utf-8"))


def atomic_write_json(path: Path, data):
    atomic_write_text(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def count_lenses(reg_path: Path) -> int:
    try:
        with open(reg_path) as f:
            return len(json.load(f).get("lenses", []))
    except Exception:
        return -1


# ─── snapshot ───

def do_snapshot(out_dir: Path = SNAP_DIR):
    out_dir.mkdir(parents=True, exist_ok=True)
    if not REG_PATH.exists():
        raise FileNotFoundError(f"registry not found: {REG_PATH}")

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    snap_name = f"lens_registry_{now}.tar.gz"
    snap_path = out_dir / snap_name
    sha_path = out_dir / (snap_name + ".sha256")

    # Build tar.gz in-memory so we can write atomically
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        tar.add(str(REG_PATH), arcname="lens_registry.json")
    data = buf.getvalue()
    atomic_write_bytes(snap_path, data)

    sha = sha256_of_file(snap_path)
    atomic_write_text(sha_path, sha + "  " + snap_name + "\n")
    size = snap_path.stat().st_size
    lens_count = count_lenses(REG_PATH)

    created_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entry = {
        "path": str(snap_path),
        "sha256": sha,
        "created_at": created_at,
        "lens_count": lens_count,
        "size_bytes": size,
    }

    ossify_target, ossified = ossify_entry(entry)
    return {
        "snapshot_path": str(snap_path),
        "sha256_path": str(sha_path),
        "sha256": sha,
        "size_bytes": size,
        "lens_count": lens_count,
        "created_at": created_at,
        "ossify_target": ossify_target,
        "ossify_entry": entry,
        "ossified": ossified,
    }


def ossify_entry(entry: dict):
    """Append entry to lockdown.json lens_snapshots; fallback to dedicated file on failure.

    Returns (target_label, ok_bool). target_label is "lockdown.json" or "lens_snapshots.json".
    """
    try:
        with open(LOCKDOWN_PATH) as f:
            lock = json.load(f)
        if not isinstance(lock, dict):
            raise ValueError("lockdown.json root is not an object")
        snaps = lock.get("lens_snapshots")
        if snaps is None:
            lock["lens_snapshots"] = [entry]
        elif isinstance(snaps, list):
            snaps.append(entry)
        else:
            raise ValueError(f"lens_snapshots has unexpected type {type(snaps).__name__}")
        atomic_write_json(LOCKDOWN_PATH, lock)
        return ("lockdown.json", True)
    except Exception as e:
        print(f"[snapshot] WARN: lockdown.json ossify failed ({e}); falling back")
        # Fallback: write/append to dedicated file
        try:
            if FALLBACK_OSSIFY.exists():
                with open(FALLBACK_OSSIFY) as f:
                    data = json.load(f)
                if not isinstance(data, dict):
                    data = {"lens_snapshots": []}
            else:
                data = {"lens_snapshots": []}
            data.setdefault("lens_snapshots", []).append(entry)
            atomic_write_json(FALLBACK_OSSIFY, data)
            return ("lens_snapshots.json", True)
        except Exception as e2:
            print(f"[snapshot] ERR: fallback ossify also failed: {e2}")
            return ("lens_snapshots.json", False)


# ─── list ───

def do_list(dir_path: Path = SNAP_DIR):
    if not dir_path.exists():
        print(f"[list] no snapshot dir: {dir_path}")
        return []
    entries = []
    for p in sorted(dir_path.glob("lens_registry_*.tar.gz")):
        sha_p = p.with_name(p.name + ".sha256")
        sha_val = None
        if sha_p.exists():
            with open(sha_p) as f:
                first = f.read().strip().split()
                if first:
                    sha_val = first[0]
        entries.append({
            "path": str(p),
            "name": p.name,
            "size_bytes": p.stat().st_size,
            "mtime_iso": datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "sha256": sha_val,
        })
    for e in entries:
        sha = e["sha256"] or "(missing)"
        print(f"  {e['name']}  size={e['size_bytes']}B  sha={sha[:16]}…  mtime={e['mtime_iso']}")
    if not entries:
        print(f"[list] empty: {dir_path}")
    return entries


# ─── rollback ───

def verify_and_extract(snap_path: Path):
    """Verify sha, extract tar.gz → return (extracted_bytes, extracted_lens_count, sha_matches_bool)."""
    sha_file = snap_path.with_name(snap_path.name + ".sha256")
    if not sha_file.exists():
        raise FileNotFoundError(f"sha sidecar missing: {sha_file}")
    with open(sha_file) as f:
        expected_sha = f.read().strip().split()[0]

    actual_sha = sha256_of_file(snap_path)
    matches = (actual_sha == expected_sha)
    if not matches:
        raise ValueError(f"sha mismatch: expected {expected_sha}, got {actual_sha}")

    with tarfile.open(snap_path, mode="r:gz") as tar:
        members = tar.getmembers()
        target = None
        for m in members:
            if m.name.endswith("lens_registry.json"):
                target = m
                break
        if target is None:
            raise ValueError("snapshot does not contain lens_registry.json")
        f = tar.extractfile(target)
        if f is None:
            raise ValueError("could not extract lens_registry.json")
        data = f.read()

    try:
        parsed = json.loads(data)
        lens_count = len(parsed.get("lenses", []))
    except Exception:
        lens_count = -1
    return data, lens_count, matches, expected_sha


def do_rollback(snap_path: Path, dry_run: bool = False):
    data, lens_count, matches, expected_sha = verify_and_extract(snap_path)
    if not matches:
        raise ValueError("sha verification failed — aborting rollback")
    if dry_run:
        print(f"[rollback] DRY-RUN OK: sha={expected_sha[:16]}… lens_count={lens_count} (would replace {REG_PATH})")
        return {"ok": True, "dry_run": True, "lens_count": lens_count, "sha256": expected_sha}

    atomic_write_bytes(REG_PATH, data)
    print(f"[rollback] replaced {REG_PATH} (lens_count={lens_count})")
    return {"ok": True, "dry_run": False, "lens_count": lens_count, "sha256": expected_sha}


# ─── CLI ───

def main():
    argv = sys.argv[1:]
    if not argv:
        print(__doc__)
        return 2

    cmd = argv[0]
    if cmd == "snapshot":
        out_dir = SNAP_DIR
        i = 1
        while i < len(argv):
            if argv[i] == "--out":
                out_dir = Path(argv[i + 1]); i += 2
            else:
                i += 1
        result = do_snapshot(out_dir)
        print(f"[snapshot] wrote {result['snapshot_path']}")
        print(f"[snapshot] sha256 = {result['sha256']}")
        print(f"[snapshot] size  = {result['size_bytes']} B")
        print(f"[snapshot] lens  = {result['lens_count']}")
        print(f"[snapshot] ossified to: {result['ossify_target']} (ok={result['ossified']})")

        # Rollback dry-run end-to-end test
        rb = do_rollback(Path(result["snapshot_path"]), dry_run=True)
        print(f"[snapshot] rollback_dry_run: ok={rb['ok']} lens_count={rb['lens_count']}")

        evidence = {
            "task": "LENS-P3-2",
            "generated_at": result["created_at"],
            "snapshot_path": result["snapshot_path"],
            "sha256_path": result["sha256_path"],
            "sha256": result["sha256"],
            "size_bytes": result["size_bytes"],
            "lens_count": result["lens_count"],
            "rollback_dry_run_passed": bool(rb["ok"]),
            "ossify_target": result["ossify_target"],
            "ossify_entry": result["ossify_entry"],
            "ossified": result["ossified"],
        }
        atomic_write_json(EVIDENCE_PATH, evidence)
        print(f"[snapshot] evidence: {EVIDENCE_PATH}")
        return 0

    if cmd == "list":
        d = SNAP_DIR
        i = 1
        while i < len(argv):
            if argv[i] == "--dir":
                d = Path(argv[i + 1]); i += 2
            else:
                i += 1
        do_list(d)
        return 0

    if cmd == "rollback":
        if len(argv) < 2:
            print("usage: rollback <snapshot_path> [--dry-run]")
            return 2
        snap = Path(argv[1])
        dry = "--dry-run" in argv[2:]
        rb = do_rollback(snap, dry_run=dry)
        print(f"[rollback] {rb}")
        return 0 if rb.get("ok") else 1

    print(f"unknown cmd: {cmd}")
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
