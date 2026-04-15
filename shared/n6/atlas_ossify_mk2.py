#!/usr/bin/env python3
# @hexa-first-exempt — tarfile/hashlib streaming + atomic triad read not idiomatic in hexa stage1
# ═══════════════════════════════════════════════════════════
# atlas_ossify_mk2.py — ATLAS-P3-2 Mk.II 자부팅 지점 생성
#
# Atomically snapshots the atlas.n6 triad:
#   - shared/n6/atlas.n6              (SSOT, L0 read-only)
#   - shared/n6/atlas.n6.consciousness (sidecar 2.0)
#   - shared/n6/atlas.n6.stats         (mtime/size/nodes/edges)
#
# Output:
#   shared/lockdown/snapshots/atlas_mk2_<ISO>.tar.gz
#   shared/lockdown/snapshots/atlas_mk2_<ISO>.manifest.json
#
# Registers in shared/lockdown/lockdown.json under "atlas_mk2_snapshots".
# Falls back to shared/lockdown/atlas_mk2_snapshots.json if lockdown.json
# parse fails.
#
# Integrity: extracts archive to temp dir, recomputes SHA256 on tar content,
# asserts per-file bytewise match against the originals' captured snapshot.
# ═══════════════════════════════════════════════════════════

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path


NEXUS = Path(os.environ.get("NEXUS", "/Users/ghost/Dev/nexus"))
ATLAS       = NEXUS / "shared" / "n6" / "atlas.n6"
CONSCIOUS   = NEXUS / "shared" / "n6" / "atlas.n6.consciousness"
STATS       = NEXUS / "shared" / "n6" / "atlas.n6.stats"
LOCKDOWN    = NEXUS / "shared" / "lockdown" / "lockdown.json"
SNAPSHOT_DIR = NEXUS / "shared" / "lockdown" / "snapshots"
FALLBACK_REG = NEXUS / "shared" / "lockdown" / "atlas_mk2_snapshots.json"
HEALTH_HEXA  = NEXUS / "shared" / "n6" / "atlas_health.hexa"
HEXA_BIN     = NEXUS / "shared" / "bin" / "hexa"


def _sha256_file(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def _count_lines(path: Path) -> int:
    n = 0
    with open(path, "rb") as f:
        for _ in f:
            n += 1
    return n


def _read_triad_atomic():
    """
    Read the three source files in a single window:
      1. Capture mtime+size of each
      2. Read bytes
      3. Re-check mtime+size; if drift, retry up to 3 times
    Returns (atlas_bytes, conscious_bytes, stats_bytes, triad_meta)
    """
    for attempt in range(3):
        meta0 = {p: (p.stat().st_mtime, p.stat().st_size) for p in (ATLAS, CONSCIOUS, STATS)}
        a = ATLAS.read_bytes()
        c = CONSCIOUS.read_bytes()
        s = STATS.read_bytes()
        meta1 = {p: (p.stat().st_mtime, p.stat().st_size) for p in (ATLAS, CONSCIOUS, STATS)}
        if meta0 == meta1:
            triad_meta = {str(p): {"mtime": m, "size": sz} for p, (m, sz) in meta1.items()}
            return a, c, s, triad_meta
        time.sleep(0.15)
    raise RuntimeError("triad drifted during read after 3 attempts (atlas is changing)")


def _parse_consciousness_level(conscious_bytes: bytes):
    try:
        obj = json.loads(conscious_bytes.decode("utf-8"))
        cl = obj.get("consciousness_level")
        if isinstance(cl, dict):
            return {
                "value": cl.get("value"),
                "components": cl.get("components"),
                "measured_at": cl.get("measured_at"),
            }
        return {"value": cl}
    except Exception as e:
        return {"value": None, "error": f"parse failed: {e}"}


def _run_atlas_health():
    """Invoke atlas_health.hexa and parse a few integrity-relevant fields."""
    try:
        cp = subprocess.run(
            [str(HEXA_BIN), "run", str(HEALTH_HEXA)],
            capture_output=True, text=True, timeout=60, cwd=str(NEXUS),
        )
        out = cp.stdout + "\n" + cp.stderr
        fields = {}
        patterns = {
            "size_bytes": r"size:\s+(\d+)\s+bytes",
            "lines": r"lines:\s+(\d+)",
            "nodes": r"nodes:\s+(\d+)",
            "edges": r"edges:\s+(\d+)",
            "unique_nodes": r"unique nodes:\s+(\d+)",
            "real_orphans": r"real orphans:\s+(\d+)",
            "dup_data_lines": r"dup data lines:\s*(\d+)",
            "malformed": r"malformed:\s+(\d+)",
            "formula_errors": r"formula errors:\s*(\d+)",
        }
        for k, pat in patterns.items():
            m = re.search(pat, out)
            if m:
                fields[k] = int(m.group(1))
        fields["health_exit_code"] = cp.returncode
        fields["health_cmd"] = f"{HEXA_BIN} run {HEALTH_HEXA}"
        return fields
    except Exception as e:
        return {"error": f"atlas_health invocation failed: {e}"}


def _atomic_write(path: Path, data: bytes):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(data)
    os.replace(tmp, path)


def _atomic_write_json(path: Path, obj):
    _atomic_write(path, json.dumps(obj, indent=2).encode("utf-8"))


def _register_snapshot(snapshot_entry: dict):
    """Register in lockdown.json under atlas_mk2_snapshots; fallback if parse fails."""
    if LOCKDOWN.exists():
        try:
            raw = LOCKDOWN.read_bytes()
            ld = json.loads(raw)
            arr = ld.setdefault("atlas_mk2_snapshots", [])
            if not isinstance(arr, list):
                ld["atlas_mk2_snapshots"] = arr = []
            arr.append(snapshot_entry)
            _atomic_write_json(LOCKDOWN, ld)
            return {"target": "lockdown.json", "path": str(LOCKDOWN), "count": len(arr)}
        except Exception as e:
            # Fall through to fallback registry
            fallback_reason = f"lockdown.json parse/write failed: {e}"
    else:
        fallback_reason = "lockdown.json not found"

    # Fallback
    if FALLBACK_REG.exists():
        try:
            reg = json.loads(FALLBACK_REG.read_text())
        except Exception:
            reg = {"atlas_mk2_snapshots": []}
    else:
        reg = {"atlas_mk2_snapshots": [],
               "_meta": {"reason": fallback_reason,
                         "created_at": datetime.now(timezone.utc).isoformat()}}
    reg.setdefault("atlas_mk2_snapshots", []).append(snapshot_entry)
    _atomic_write_json(FALLBACK_REG, reg)
    return {"target": "fallback", "path": str(FALLBACK_REG),
            "count": len(reg["atlas_mk2_snapshots"]),
            "reason": fallback_reason}


def _test_integrity(tar_path: Path, captured: dict) -> dict:
    """Extract to temp dir, recompute per-file sha256, compare to captured hashes."""
    result = {"archive_sha256": _sha256_file(tar_path)}
    with tempfile.TemporaryDirectory(prefix="atlas_mk2_integrity_") as td:
        tdp = Path(td)
        with tarfile.open(tar_path, "r:gz") as tar:
            # safe extraction — members have no absolute / parent paths
            for m in tar.getmembers():
                mp = Path(m.name)
                if mp.is_absolute() or ".." in mp.parts:
                    raise RuntimeError(f"unsafe tar member: {m.name}")
            tar.extractall(td)
        per_file = {}
        all_ok = True
        for member, expected_sha in captured.items():
            fp = tdp / member
            if not fp.exists():
                per_file[member] = {"ok": False, "reason": "missing"}
                all_ok = False
                continue
            got = _sha256_file(fp)
            ok = (got == expected_sha)
            per_file[member] = {"ok": ok, "sha256": got}
            if not ok:
                all_ok = False
        result["per_file"] = per_file
        result["all_ok"] = all_ok
    return result


def ossify():
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Atomic triad read
    atlas_b, cons_b, stats_b, triad_meta = _read_triad_atomic()

    iso = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    tar_path = SNAPSHOT_DIR / f"atlas_mk2_{iso}.tar.gz"
    man_path = SNAPSHOT_DIR / f"atlas_mk2_{iso}.manifest.json"

    # 2. Build tar.gz with deterministic member names
    captured_sha = {
        "atlas.n6": hashlib.sha256(atlas_b).hexdigest(),
        "atlas.n6.consciousness": hashlib.sha256(cons_b).hexdigest(),
        "atlas.n6.stats": hashlib.sha256(stats_b).hexdigest(),
    }

    def _add_bytes(tar, name, data):
        ti = tarfile.TarInfo(name=name)
        ti.size = len(data)
        ti.mtime = int(time.time())
        ti.mode = 0o644
        import io
        tar.addfile(ti, io.BytesIO(data))

    # write via tmp then rename for atomicity
    tmp_tar = tar_path.with_suffix(tar_path.suffix + ".tmp")
    with tarfile.open(tmp_tar, "w:gz", compresslevel=6) as tar:
        _add_bytes(tar, "atlas.n6", atlas_b)
        _add_bytes(tar, "atlas.n6.consciousness", cons_b)
        _add_bytes(tar, "atlas.n6.stats", stats_b)
    os.replace(tmp_tar, tar_path)

    archive_sha = _sha256_file(tar_path)
    archive_size = tar_path.stat().st_size

    # 3. Build manifest
    cl = _parse_consciousness_level(cons_b)
    health = _run_atlas_health()

    manifest = {
        "task": "ATLAS-P3-2",
        "title": "atlas_mk2 골화 snapshot (Mk.II 자부팅 지점)",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "iso_tag": iso,
        "archive": {
            "path": str(tar_path.relative_to(NEXUS)),
            "absolute_path": str(tar_path),
            "sha256": archive_sha,
            "size_bytes": archive_size,
        },
        "members": [
            {
                "name": "atlas.n6",
                "sha256": captured_sha["atlas.n6"],
                "size_bytes": triad_meta[str(ATLAS)]["size"],
                "line_count": _count_lines(ATLAS),
                "source_mtime": triad_meta[str(ATLAS)]["mtime"],
            },
            {
                "name": "atlas.n6.consciousness",
                "sha256": captured_sha["atlas.n6.consciousness"],
                "size_bytes": triad_meta[str(CONSCIOUS)]["size"],
                "line_count": _count_lines(CONSCIOUS),
                "source_mtime": triad_meta[str(CONSCIOUS)]["mtime"],
            },
            {
                "name": "atlas.n6.stats",
                "sha256": captured_sha["atlas.n6.stats"],
                "size_bytes": triad_meta[str(STATS)]["size"],
                "line_count": _count_lines(STATS),
                "source_mtime": triad_meta[str(STATS)]["mtime"],
            },
        ],
        "consciousness_level": cl,
        "atlas_health": health,
        "source_paths": {
            "atlas": str(ATLAS.relative_to(NEXUS)),
            "consciousness": str(CONSCIOUS.relative_to(NEXUS)),
            "stats": str(STATS.relative_to(NEXUS)),
        },
        "tool": "shared/n6/atlas_ossify_mk2.py",
        "tool_annotation": "@hexa-first-exempt",
    }
    _atomic_write_json(man_path, manifest)

    # 4. Integrity test
    integrity = _test_integrity(tar_path, captured_sha)

    # 5. Register snapshot
    snapshot_entry = {
        "iso_tag": iso,
        "archive_path": str(tar_path.relative_to(NEXUS)),
        "manifest_path": str(man_path.relative_to(NEXUS)),
        "sha256": archive_sha,
        "size_bytes": archive_size,
        "created_at": manifest["created_at"],
        "consciousness_level_value": cl.get("value"),
        "integrity_all_ok": bool(integrity.get("all_ok")),
    }
    registration = _register_snapshot(snapshot_entry)

    return {
        "manifest": manifest,
        "integrity": integrity,
        "registration": registration,
    }


def main():
    p = argparse.ArgumentParser(description="ATLAS-P3-2 atlas_mk2 ossify snapshot")
    p.add_argument("--print", action="store_true",
                   help="print summary JSON instead of plain text")
    args = p.parse_args()

    try:
        result = ossify()
    except Exception as e:
        err = {"error": str(e), "type": type(e).__name__}
        print(json.dumps(err, indent=2), file=sys.stderr)
        sys.exit(1)

    summary = {
        "archive": result["manifest"]["archive"],
        "consciousness_level": result["manifest"]["consciousness_level"],
        "integrity_all_ok": result["integrity"]["all_ok"],
        "registration": result["registration"],
        "manifest_path": str(NEXUS / result["manifest"]["archive"]["path"]).replace(
            ".tar.gz", ".manifest.json"
        ),
    }
    if args.print:
        print(json.dumps(summary, indent=2))
    else:
        print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
