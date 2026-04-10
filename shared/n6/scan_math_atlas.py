#!/usr/bin/env python3
"""Math Atlas — Hypothesis Markdown Parser.

Parses hypothesis markdown files from TECS-L, anima, SEDI repos
and extracts structured metadata (id, title, grade, refs, etc.).
"""

import re
import ast
import json
import sys
import sqlite3
import argparse
from pathlib import Path
from datetime import datetime

# ── Grade emojis (detection order matters) ──────────────────────────
GRADE_EMOJIS = ["\u2b50", "\U0001f7e9", "\U0001f7e7", "\U0001f7e6", "\U0001f7e8", "\U0001f7e5", "\U0001f7ea", "\u26aa", "\u2b1b", "\u2605", "\u26a1", "\u2705"]


def _parse_yaml_frontmatter(text):
    """Extract YAML frontmatter as a dict (simple key: value parsing)."""
    m = re.match(r'^---\n(.*?)\n---', text, re.DOTALL)
    if not m:
        return {}
    result = {}
    for line in m.group(1).splitlines():
        km = re.match(r'^(\w[\w-]*):\s*"?([^"]*)"?\s*$', line.strip())
        if km:
            result[km.group(1)] = km.group(2).strip()
    return result


def _extract_grade(text, yaml, title_line):
    """Extract grade with priority: YAML > ## Grade > **Grade:**/**Status:** > title emoji > title checkmark."""
    # Priority 1: YAML frontmatter
    if yaml.get("grade"):
        return yaml["grade"]

    # Priority 2: ## Grade: line
    m = re.search(r'^##\s*Grade:\s*(.+)', text, re.MULTILINE)
    if m:
        grade_text = m.group(1).strip()
        emojis = _extract_emoji_run(grade_text)
        if emojis:
            return emojis
        return grade_text

    # Priority 3: **Grade:** or **Status:** line
    m = re.search(r'\*\*(?:Grade|Status):\s*(.+?)(?:\*\*|$)', text, re.MULTILINE)
    if m:
        grade_text = m.group(1).strip()
        emojis = _extract_emoji_run(grade_text)
        if emojis:
            return emojis
        return grade_text

    # Priority 4: Emoji in title
    if title_line:
        emojis = _extract_emoji_run(title_line)
        if emojis:
            return emojis

    # Priority 5: Checkmark in title
    if title_line and "\u2705" in title_line:
        return "\u2705"

    return None


def _extract_emoji_run(text):
    """Extract a contiguous run of grade emojis from text."""
    result = []
    i = 0
    started = False
    while i < len(text):
        matched = False
        for emoji in GRADE_EMOJIS:
            if text[i:].startswith(emoji):
                result.append(emoji)
                i += len(emoji)
                matched = True
                started = True
                break
        if not matched:
            if started:
                break
            i += 1
    return "".join(result) if result else None


def _extract_refs(text):
    """Extract cross-references: related hypothesis numbers and H-XX-NNN patterns."""
    refs = []

    # Pattern: "Related hypotheses: 041(Name), 055(Name)"
    m = re.search(r'[Rr]elated\s+hypothes[ei]s?:\s*(.+)', text)
    if m:
        for num_match in re.finditer(r'(\d{2,4})\s*\(', m.group(1)):
            refs.append(num_match.group(1))

    # Pattern: inline "(H-XX-NNN)" references
    for m in re.finditer(r'\(H-([A-Z]+)-(\d+)\)', text):
        refs.append(f"H-{m.group(1)}-{m.group(2)}")

    return refs


def _extract_gz_dependency(text):
    """Extract Golden Zone dependency flag."""
    m = re.search(r'\*\*Golden Zone dependency:\*\*\s*(.+)', text)
    if not m:
        return None
    value = m.group(1).strip().upper()
    if value.startswith("NONE") or value.startswith("NO"):
        return False
    if value.startswith("YES"):
        return True
    return None


def _extract_domain(hid):
    """Extract domain from H-XX-NNN style ID."""
    m = re.match(r'H-([A-Z]+)-', hid)
    if m:
        return m.group(1)
    return None


def parse_hypothesis_md(text, repo, filepath):
    """Parse a hypothesis markdown file and return structured metadata.

    Args:
        text: Full markdown text content.
        repo: Repository name (TECS-L, anima, SEDI).
        filepath: Relative file path within repo.

    Returns:
        dict with keys: id, title, repo, domain, grade, refs, gz_dependent, filepath
    """
    yaml = _parse_yaml_frontmatter(text)
    stem = Path(filepath).stem  # filename without extension

    # Try to find the first H1 heading
    title_match = re.search(r'^#\s+(.+)', text, re.MULTILINE)
    title_line = title_match.group(1).strip() if title_match else ""

    hid = None
    title = None
    domain = None

    # Pattern A: "Hypothesis Review NNN: Title"
    m = re.match(r'Hypothesis\s+Review\s+(\d+):\s*(.+)', title_line)
    if m:
        hid = m.group(1)
        title = m.group(2).strip()

    # Pattern B: "Hypothesis NNN: Title"
    if not hid:
        m = re.match(r'Hypothesis\s+(\d+):\s*(.+)', title_line)
        if m:
            hid = m.group(1)
            title = m.group(2).strip()

    # Pattern C: "H-XX-NNN: Title"
    if not hid:
        m = re.match(r'(H-[A-Z]+-\d+):\s*(.+)', title_line)
        if m:
            hid = m.group(1)
            title = m.group(2).strip()
            domain = _extract_domain(hid)

    # Pattern E: "Frontier NNN: Title"
    if not hid:
        m = re.match(r'Frontier\s+(\d+):\s*(.+)', title_line)
        if m:
            hid = f"F-{m.group(1)}"
            title = m.group(2).strip()

    # Pattern D: YAML frontmatter id field (highest priority — overrides heading)
    if yaml.get("id"):
        hid = yaml["id"]
        domain = _extract_domain(hid)
        if yaml.get("title"):
            title = yaml["title"]

    # Fallback: no pattern matched
    if not hid:
        hid = stem
        title = title_line if title_line else stem

    if not title:
        title = title_line

    # Build full qualified ID
    full_id = f"{repo}:{hid}"

    grade = _extract_grade(text, yaml, title_line)
    refs = _extract_refs(text)
    gz_dependent = _extract_gz_dependency(text)

    return {
        "id": full_id,
        "title": title,
        "repo": repo,
        "domain": domain,
        "grade": grade,
        "refs": refs,
        "gz_dependent": gz_dependent,
        "file": filepath,
    }


def parse_anima_recommender(source):
    """Parse anima's HYPOTHESIS_DB Python source and extract hypothesis entries.

    Args:
        source: Python source code containing HYPOTHESIS_DB list.

    Returns:
        list of dicts with keys: id, title, code, category, description, grade
    """
    results = []
    for m in re.finditer(r'Hypothesis\(\s*(.*?)\s*\)', source, re.DOTALL):
        block = m.group(1)
        entry = {}

        for field in ("code", "name", "category", "description"):
            fm = re.search(rf'{field}\s*=\s*"([^"]*)"', block)
            if fm:
                entry[field] = fm.group(1)

        fm = re.search(r'expected_phi\s*=\s*([\d.]+)', block)
        if fm:
            entry["expected_phi"] = float(fm.group(1))

        code = entry.get("code", "???")
        results.append({
            "id": f"anima:{code}",
            "title": entry.get("name", ""),
            "code": code,
            "category": entry.get("category"),
            "description": entry.get("description"),
            "grade": None,
        })

    return results


# ── Repo scan configuration ──────────────────────────────────────

BASE = Path(__file__).resolve().parent.parent  # TECS-L root
DEV = BASE.parent  # ~/Dev

REPO_SCANS = [
    {
        "name": "TECS-L",
        "root": BASE,
        "hypothesis_dirs": ["docs/hypotheses", "math/docs/hypotheses"],
        "constant_dirs": [".", "calc", "math"],
    },
    {
        "name": "SEDI",
        "root": DEV / "SEDI",
        "hypothesis_dirs": ["docs/hypotheses"],
        "constant_dirs": ["sedi", "sedi/sources"],
    },
    {
        "name": "anima",
        "root": DEV / "anima",
        "hypothesis_dirs": [
            "docs/hypotheses",
            "docs/hypotheses/cx",
            "docs/hypotheses/ce",
            "docs/hypotheses/dd",
            "docs/hypotheses/dasein",
            "docs/hypotheses/evo",
            "docs/hypotheses/genesis",
            "docs/hypotheses/hw",
            "docs/hypotheses/inf",
            "docs/hypotheses/omega",
            "docs/hypotheses/onto",
            "docs/hypotheses/phil",
            "docs/hypotheses/phys",
            "docs/hypotheses/se",
            "docs/hypotheses/sing",
            "docs/hypotheses/sl",
            "docs/hypotheses/three",
            "docs/hypotheses/topo",
            "docs/hypotheses/tp",
        ],
        "python_sources": ["hypothesis_recommender.py"],
        "constant_dirs": ["."],
    },
    {
        "name": "golden-moe",
        "root": DEV / "golden-moe",
        "hypothesis_dirs": [],
        "constant_dirs": ["."],
    },
    {
        "name": "conscious-lm",
        "root": DEV / "conscious-lm",
        "hypothesis_dirs": [],
        "constant_dirs": ["."],
    },
    {
        "name": "energy-efficiency",
        "root": DEV / "energy-efficiency",
        "hypothesis_dirs": [],
        "constant_dirs": [".", "techniques", "experiments"],
    },
]


def _scan_md_dir(repo_name, repo_root, rel_dir):
    """Scan a directory for *.md files and parse each as a hypothesis.

    Args:
        repo_name: Repository name (TECS-L, SEDI, anima).
        repo_root: Path to the repository root.
        rel_dir: Relative directory path within the repo.

    Returns:
        list of parsed hypothesis dicts.
    """
    results = []
    dirpath = repo_root / rel_dir
    if not dirpath.is_dir():
        return results
    for mdfile in sorted(dirpath.glob("*.md")):
        if mdfile.name.startswith('.') or mdfile.name == 'README.md':
            continue
        try:
            text = mdfile.read_text(encoding="utf-8", errors="replace")
        except (OSError, IOError):
            continue
        filepath = str(mdfile.relative_to(repo_root))
        h = parse_hypothesis_md(text, repo_name, filepath)
        results.append(h)
    return results


def _scan_anima_python(repo_root, source_file):
    """Read and parse an anima Python source file.

    Args:
        repo_root: Path to the anima repository root.
        source_file: Relative path to the Python source.

    Returns:
        list of parsed hypothesis dicts (anima format).
    """
    fpath = repo_root / source_file
    if not fpath.is_file():
        return []
    try:
        text = fpath.read_text(encoding="utf-8", errors="replace")
    except (OSError, IOError):
        return []
    entries = parse_anima_recommender(text)
    # Normalize anima entries to match MD hypothesis shape
    results = []
    for e in entries:
        results.append({
            "id": e["id"],
            "title": e["title"],
            "repo": "anima",
            "domain": e.get("category"),
            "grade": e.get("grade"),
            "refs": [],
            "gz_dependent": None,
            "file": source_file,
        })
    return results


def _make_json_safe(obj):
    """Recursively convert non-JSON-serializable types (sets, tuples) to lists."""
    if isinstance(obj, set):
        return sorted(list(obj), key=str)
    if isinstance(obj, tuple):
        return [_make_json_safe(v) for v in obj]
    if isinstance(obj, dict):
        return {str(k): _make_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_make_json_safe(v) for v in obj]
    if isinstance(obj, (int, float, str, bool, type(None))):
        return obj
    # Fallback: stringify
    return str(obj)


def _categorize_constant(name, file_path=""):
    """Auto-categorize a constant map by its name and file path."""
    upper = name.upper()
    fpath = file_path.lower()

    # ── Consciousness / Axioms (anima Ψ-constants, laws) ──
    if any(k in upper for k in ("PSI", "CONSCIOUSNESS", "PHI_", "MIND", "WILL")):
        return "consciousness"
    if any(k in fpath for k in ("consciousness", "anima_alive", "conscious")):
        return "consciousness"

    # ── Architecture / Engines ──
    if any(k in upper for k in ("ENGINE", "ARCH", "DECODER", "MODEL", "TOPOLOG")):
        return "architecture"
    if any(k in fpath for k in ("engine", "architect", "decoder", "bench")):
        return "architecture"

    # ── Targets ──
    if "TARGET" in upper:
        return "targets"

    # ── Physics ──
    if any(k in upper for k in ("PHYSICS", "PARTICLE", "MASS", "ZETA", "GAUGE",
                                 "STRING", "QUANTUM", "LADDER", "RESONAN")):
        return "physics"

    # ── Constants / Math pools ──
    if any(k in upper for k in ("CONSTANT", "POOL", "PERFECT_NUMBER", "KNOWN_PERFECT",
                                 "FIBONACCI", "KISSING", "PLATONIC")):
        return "constants"

    # ── Domains ──
    if "DOMAIN" in upper or "CATEGOR" in upper:
        return "domains"

    # ── Nuclear ──
    if "MAGIC" in upper or "NUCLEAR" in upper:
        return "nuclear"

    # ── Expressions / Formulas ──
    if "EXPRESSION" in upper or "FORMULA" in upper or "IDENTITY" in upper:
        return "expressions"

    # ── Observed / Empirical data ──
    if "OBSERVED" in upper or "EMPIRICAL" in upper or "BENCHMARK" in upper:
        return "observed"

    # ── Neuroscience ──
    if any(k in upper for k in ("PROFILE", "BRAIN", "EEG", "EMOTION", "GROWTH",
                                 "STAGE", "DRUG", "PHARMACOL")):
        return "neuroscience"

    # ── Verification / Testing ──
    if any(k in upper for k in ("CLAIM", "VERIFY", "TEST", "SCAN", "GRADE", "VALID")):
        return "verification"

    # ── Data / Configuration ──
    if any(k in upper for k in ("PRESET", "CONFIG", "PARAM", "SWEEP", "STRATEG")):
        return "config"

    return "other"


def _is_uppercase_name(name):
    """Check if a name is an UPPERCASE constant (all caps with underscores)."""
    return bool(re.match(r'^[A-Z][A-Z0-9_]*$', name))


def _try_extract_ordered_dict(node):
    """Try to extract keys/values from OrderedDict([(...), ...]) calls."""
    if not isinstance(node, ast.Call):
        return None
    # Check for OrderedDict(...)
    func = node.func
    func_name = None
    if isinstance(func, ast.Name):
        func_name = func.id
    elif isinstance(func, ast.Attribute):
        func_name = func.attr
    if func_name != "OrderedDict":
        return None
    if not node.args:
        return None
    arg = node.args[0]
    if not isinstance(arg, (ast.List, ast.Tuple)):
        return None
    keys = []
    values = {}
    evaluable = True
    for elt in arg.elts:
        if not isinstance(elt, (ast.Tuple, ast.List)) or len(elt.elts) != 2:
            continue
        try:
            key = ast.literal_eval(elt.elts[0])
            keys.append(key)
        except (ValueError, TypeError):
            keys.append("?")
            evaluable = False
            continue
        try:
            val = ast.literal_eval(elt.elts[1])
            values[key] = val
        except (ValueError, TypeError):
            evaluable = False
    return {"keys": keys, "values": values if evaluable else None, "evaluable": evaluable}


def extract_constants_from_py(filepath, repo_name):
    """Extract UPPERCASE constant maps (dicts, lists, OrderedDicts) from a Python file.

    Uses the ast module to parse the file and find top-level assignments
    to UPPERCASE names that are dicts, lists, or OrderedDict calls.

    Args:
        filepath: Absolute path to the Python file.
        repo_name: Repository name (TECS-L, SEDI, anima).

    Returns:
        list of constant map entry dicts.
    """
    filepath = Path(filepath)
    try:
        source = filepath.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source)
    except (OSError, SyntaxError):
        return []

    # Find repo root for relative path
    repo_roots = {
        "TECS-L": BASE,
        "SEDI": DEV / "SEDI",
        "anima": DEV / "anima",
    }
    repo_root = repo_roots.get(repo_name, BASE)
    try:
        rel_path = str(filepath.relative_to(repo_root))
    except ValueError:
        rel_path = filepath.name

    results = []
    for node in ast.iter_child_nodes(tree):
        if not isinstance(node, ast.Assign):
            continue
        if len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name):
            continue
        name = target.id
        if not _is_uppercase_name(name):
            continue
        if name.startswith("_"):
            continue

        value_node = node.value
        entry = {
            "name": name,
            "repo": repo_name,
            "file": rel_path,
            "line": node.lineno,
            "type": None,
            "size": 0,
            "keys": None,
            "evaluable": False,
            "values": None,
            "category": _categorize_constant(name, rel_path),
        }

        # Dict literal
        if isinstance(value_node, ast.Dict):
            entry["type"] = "dict"
            # Try to extract keys
            keys = []
            for k in value_node.keys:
                if k is None:
                    keys.append("**")
                    continue
                try:
                    keys.append(ast.literal_eval(k))
                except (ValueError, TypeError):
                    keys.append("?")
            entry["keys"] = keys
            entry["size"] = len(value_node.keys)

            # Try full literal_eval
            try:
                val = ast.literal_eval(value_node)
                entry["evaluable"] = True
                entry["values"] = val
            except (ValueError, TypeError):
                entry["evaluable"] = False

        # List/Tuple literal
        elif isinstance(value_node, (ast.List, ast.Tuple)):
            entry["type"] = "list"
            entry["size"] = len(value_node.elts)
            try:
                val = ast.literal_eval(value_node)
                entry["evaluable"] = True
                entry["values"] = val
            except (ValueError, TypeError):
                entry["evaluable"] = False

        # Dict comprehension
        elif isinstance(value_node, ast.DictComp):
            entry["type"] = "dict"
            entry["size"] = 0  # unknown
            entry["evaluable"] = False

        # OrderedDict(...) call
        elif isinstance(value_node, ast.Call):
            od = _try_extract_ordered_dict(value_node)
            if od is not None:
                entry["type"] = "OrderedDict"
                entry["keys"] = od["keys"]
                entry["size"] = len(od["keys"])
                entry["evaluable"] = od["evaluable"]
                entry["values"] = od["values"]
            else:
                continue  # Not a recognized constant pattern

        # {**A, **B} style merge (still a Dict node, handled above)
        else:
            continue  # Skip non-collection assignments

        # Filtering: skip empty and very large
        if entry["size"] == 0 and entry["type"] != "dict":
            continue
        if entry["size"] > 500:
            continue

        # Make values JSON-safe (convert sets, tuples, etc.)
        if entry["values"] is not None:
            entry["values"] = _make_json_safe(entry["values"])
        if entry["keys"] is not None:
            entry["keys"] = [_make_json_safe(k) for k in entry["keys"]]

        results.append(entry)

    return results


def _scan_py_constants(repo_name, repo_root, scan_dirs):
    """Scan Python files in given directories for constant maps.

    Args:
        repo_name: Repository name.
        repo_root: Path to the repository root.
        scan_dirs: List of relative directory paths to scan.

    Returns:
        list of constant map entry dicts.
    """
    results = []
    for rel_dir in scan_dirs:
        dirpath = repo_root / rel_dir
        if not dirpath.is_dir():
            continue
        for pyfile in sorted(dirpath.glob("*.py")):
            if pyfile.name.startswith('.'):
                continue
            entries = extract_constants_from_py(pyfile, repo_name)
            results.extend(entries)
    return results


def build_atlas():
    """Scan all repos and build a unified atlas of hypotheses.

    Returns:
        dict with keys: version, generated, stats, total, hypotheses
    """
    all_hypotheses = []
    stats = {}

    for repo_cfg in REPO_SCANS:
        name = repo_cfg["name"]
        root = repo_cfg["root"]
        repo_count = 0

        # Scan markdown hypothesis directories
        for rel_dir in repo_cfg.get("hypothesis_dirs", []):
            entries = _scan_md_dir(name, root, rel_dir)
            all_hypotheses.extend(entries)
            repo_count += len(entries)

        # Scan Python sources (anima)
        for src in repo_cfg.get("python_sources", []):
            entries = _scan_anima_python(root, src)
            all_hypotheses.extend(entries)
            repo_count += len(entries)

        stats[name] = repo_count

    # Deduplicate by ID (keep first occurrence)
    seen = set()
    unique = []
    for h in all_hypotheses:
        if h["id"] not in seen:
            seen.add(h["id"])
            unique.append(h)

    # Scan constant maps from Python files
    all_constants = []
    constant_stats = {}
    for repo_cfg in REPO_SCANS:
        name = repo_cfg["name"]
        root = repo_cfg["root"]
        cdirs = repo_cfg.get("constant_dirs", [])
        if cdirs:
            entries = _scan_py_constants(name, root, cdirs)
            all_constants.extend(entries)
            constant_stats[name] = len(entries)

    return {
        "version": "1.1",
        "generated": datetime.now().isoformat(timespec="seconds"),
        "stats": stats,
        "total": len(unique),
        "hypotheses": unique,
        "constant_maps": all_constants,
        "constant_stats": constant_stats,
    }


# ── SQLite output ────────────────────────────────────────────────

def write_sqlite(atlas, dbpath):
    """Write atlas data to a SQLite database.

    Creates tables:
        hypotheses: id (PK), repo, file, title, grade, domain, gz_dependent, refs (JSON)
        edges: source_id, target_id, relation

    Args:
        atlas: dict returned by build_atlas().
        dbpath: Path to the SQLite database file.
    """
    conn = sqlite3.connect(dbpath)
    cur = conn.cursor()

    cur.execute("DROP TABLE IF EXISTS hypotheses")
    cur.execute("DROP TABLE IF EXISTS edges")

    cur.execute("""
        CREATE TABLE hypotheses (
            id TEXT PRIMARY KEY,
            repo TEXT,
            file TEXT,
            title TEXT,
            grade TEXT,
            domain TEXT,
            gz_dependent INTEGER,
            refs TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE edges (
            source_id TEXT,
            target_id TEXT,
            relation TEXT
        )
    """)

    cur.execute("CREATE INDEX idx_repo ON hypotheses(repo)")
    cur.execute("CREATE INDEX idx_grade ON hypotheses(grade)")
    cur.execute("CREATE INDEX idx_domain ON hypotheses(domain)")

    # Insert hypotheses
    for h in atlas["hypotheses"]:
        gz = None
        if h["gz_dependent"] is True:
            gz = 1
        elif h["gz_dependent"] is False:
            gz = 0
        cur.execute(
            "INSERT INTO hypotheses VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (h["id"], h["repo"], h["file"], h["title"],
             h["grade"], h["domain"], gz, json.dumps(h["refs"])),
        )

    # Build ID lookup: short_id -> full_id (for resolving refs)
    id_lookup = {}
    for h in atlas["hypotheses"]:
        full_id = h["id"]
        # e.g. "TECS-L:056" -> short "056", "TECS-L:H-CX-215" -> short "H-CX-215"
        short = full_id.split(":", 1)[1] if ":" in full_id else full_id
        # Map short -> full (first wins for collisions)
        if short not in id_lookup:
            id_lookup[short] = full_id

    # Build edges from refs
    for h in atlas["hypotheses"]:
        source = h["id"]
        for ref in h.get("refs", []):
            target = id_lookup.get(ref)
            if target and target != source:
                cur.execute(
                    "INSERT INTO edges VALUES (?, ?, ?)",
                    (source, target, "ref"),
                )

    # ── constant_maps table ──
    cur.execute("DROP TABLE IF EXISTS constant_maps")
    cur.execute("""
        CREATE TABLE constant_maps (
            name TEXT,
            repo TEXT,
            file TEXT,
            line INTEGER,
            type TEXT,
            size INTEGER,
            keys TEXT,
            evaluable INTEGER,
            val_json TEXT,
            category TEXT
        )
    """)
    cur.execute("CREATE INDEX idx_cm_repo ON constant_maps(repo)")
    cur.execute("CREATE INDEX idx_cm_category ON constant_maps(category)")

    for cm in atlas.get("constant_maps", []):
        cur.execute(
            "INSERT INTO constant_maps VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                cm["name"], cm["repo"], cm["file"], cm["line"],
                cm["type"], cm["size"],
                json.dumps(cm["keys"]) if cm["keys"] is not None else None,
                1 if cm["evaluable"] else 0,
                json.dumps(cm["values"]) if cm["values"] is not None else None,
                cm["category"],
            ),
        )

    conn.commit()
    conn.close()


# ── Graphviz DOT output ──────────────────────────────────────────

REPO_COLORS = {
    "TECS-L": "#4A90D9",
    "SEDI": "#E67E22",
    "anima": "#2ECC71",
    "golden-moe": "#F1C40F",
    "conscious-lm": "#9B59B6",
    "energy-efficiency": "#1ABC9C",
}

GRADE_SHAPES = {
    "\u2b50": "doubleoctagon",   # star
    "\u2605": "doubleoctagon",   # filled star
    "\U0001f7e9": "box",         # green square
    "\U0001f7e7": "diamond",     # orange square
    "\u26aa": "ellipse",         # white circle
    "\u2b1b": "point",           # black square
}


def _sanitize_dot_id(hid):
    """Sanitize a hypothesis ID for use as a DOT node ID."""
    return re.sub(r'[:\-]', '_', hid)


def _grade_to_shape(grade):
    """Map a grade string to a DOT shape."""
    if not grade:
        return "ellipse"
    for emoji, shape in GRADE_SHAPES.items():
        if emoji in grade:
            return shape
    return "ellipse"


def write_dot(atlas, dotpath):
    """Write atlas graph to a Graphviz DOT file.

    Only includes nodes that have at least one edge (ref connection).

    Args:
        atlas: dict returned by build_atlas().
        dotpath: Path to the output .dot file.
    """
    # Build ID lookup for resolving refs
    id_lookup = {}
    hyp_by_id = {}
    for h in atlas["hypotheses"]:
        full_id = h["id"]
        short = full_id.split(":", 1)[1] if ":" in full_id else full_id
        if short not in id_lookup:
            id_lookup[short] = full_id
        hyp_by_id[full_id] = h

    # Collect edges
    edges = []
    connected = set()
    for h in atlas["hypotheses"]:
        source = h["id"]
        for ref in h.get("refs", []):
            target = id_lookup.get(ref)
            if target and target != source:
                edges.append((source, target))
                connected.add(source)
                connected.add(target)

    lines = ['digraph math_atlas {', '  rankdir=LR;', '  node [style=filled];', '']

    # Emit connected nodes
    for nid in sorted(connected):
        h = hyp_by_id.get(nid)
        if not h:
            continue
        safe = _sanitize_dot_id(nid)
        color = REPO_COLORS.get(h["repo"], "#999999")
        shape = _grade_to_shape(h.get("grade"))
        label = h["title"][:40].replace('"', '\\"') if h.get("title") else nid
        lines.append(f'  {safe} [label="{label}" fillcolor="{color}" shape={shape}];')

    lines.append('')

    # Emit edges
    for src, tgt in edges:
        lines.append(f'  {_sanitize_dot_id(src)} -> {_sanitize_dot_id(tgt)};')

    lines.append('}')

    with open(dotpath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')


# ── Markdown output ──────────────────────────────────────────────

def write_markdown(atlas, mdpath):
    """Write complete atlas as a readable markdown document."""
    lines = []

    # Header
    total = atlas["total"]
    cm_count = len(atlas.get("constant_maps", []))
    lines.append("# Math Atlas")
    lines.append("")
    lines.append(f"> Auto-generated: {atlas['generated']} | {total} hypotheses | {cm_count} constant maps")
    lines.append("")

    # Summary table
    lines.append("## Summary")
    lines.append("")
    lines.append("| Repo | Hypotheses | Constant Maps |")
    lines.append("|------|-----------|--------------|")
    total_h = 0
    total_c = 0
    for repo in ["TECS-L", "SEDI", "anima"]:
        h_count = atlas["stats"].get(repo, 0)
        c_count = atlas.get("constant_stats", {}).get(repo, 0)
        total_h += h_count
        total_c += c_count
        lines.append(f"| {repo} | {h_count:,} | {c_count} |")
    lines.append(f"| **Total** | **{total_h:,}** | **{total_c}** |")
    lines.append("")

    # Grade distribution
    grade_dist = {}
    for h in atlas["hypotheses"]:
        g = h.get("grade") or "(none)"
        grade_dist[g] = grade_dist.get(g, 0) + 1
    lines.append("### Grade Distribution")
    lines.append("")
    lines.append("| Grade | Count |")
    lines.append("|-------|-------|")
    for g, c in sorted(grade_dist.items(), key=lambda x: -x[1])[:15]:
        lines.append(f"| {g} | {c} |")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Hypotheses by repo
    lines.append("## Hypotheses")
    lines.append("")
    for repo in ["TECS-L", "SEDI", "anima"]:
        hyps = [h for h in atlas["hypotheses"] if h["repo"] == repo]
        lines.append(f"### {repo} ({len(hyps)})")
        lines.append("")
        lines.append("| # | ID | Title | Grade | Domain |")
        lines.append("|---|-----|-------|-------|--------|")
        for i, h in enumerate(hyps, 1):
            hid = h["id"].split(":", 1)[1] if ":" in h["id"] else h["id"]
            title = (h.get("title") or "")[:60]
            grade = h.get("grade") or "-"
            domain = h.get("domain") or "-"
            lines.append(f"| {i} | {hid} | {title} | {grade} | {domain} |")
        lines.append("")

    lines.append("---")
    lines.append("")

    # Constant maps by repo
    lines.append("## Constant Maps")
    lines.append("")
    cmaps = atlas.get("constant_maps", [])
    for repo in ["TECS-L", "SEDI", "anima"]:
        repo_cms = [cm for cm in cmaps if cm["repo"] == repo]
        if not repo_cms:
            continue
        lines.append(f"### {repo} ({len(repo_cms)})")
        lines.append("")
        lines.append("| # | Name | File | Type | Size | Category | Eval |")
        lines.append("|---|------|------|------|------|----------|------|")
        for i, cm in enumerate(repo_cms, 1):
            ev = "Y" if cm.get("evaluable") else "-"
            lines.append(f"| {i} | {cm['name']} | {cm['file']}:{cm['line']} | {cm['type']} | {cm['size']} | {cm['category']} | {ev} |")
        lines.append("")

    lines.append("---")
    lines.append("")

    # Edges (build from hypotheses refs using id_lookup)
    id_lookup = {}
    for h in atlas["hypotheses"]:
        full_id = h["id"]
        short = full_id.split(":", 1)[1] if ":" in full_id else full_id
        if short not in id_lookup:
            id_lookup[short] = full_id

    edge_list = []
    for h in atlas["hypotheses"]:
        for ref in h.get("refs", []):
            target = id_lookup.get(ref)
            if target and target != h["id"]:
                edge_list.append((h["id"], target))

    lines.append(f"## Cross-Reference Edges ({len(edge_list)})")
    lines.append("")
    lines.append("| Source | Target |")
    lines.append("|--------|--------|")
    for src, tgt in edge_list:
        lines.append(f"| {src} | {tgt} |")
    lines.append("")

    with open(mdpath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')


# ── HTML output ──────────────────────────────────────────────────

HTML_TEMPLATE = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Math Atlas</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace; background: #1a1a2e; color: #e0e0e0; padding: 20px; }
.header { text-align: center; margin-bottom: 20px; }
.header h1 { font-size: 1.5em; color: #fff; }
.stats { color: #888; font-size: 0.85em; margin-top: 5px; }
.controls { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 15px; align-items: center; }
.search { flex: 1; min-width: 200px; padding: 8px 12px; background: #16213e; border: 1px solid #333; color: #fff; font-family: inherit; font-size: 0.9em; border-radius: 4px; outline: none; }
.search:focus { border-color: #4A90D9; }
.filters { display: flex; gap: 15px; flex-wrap: wrap; }
.filter-group { display: flex; gap: 5px; align-items: center; flex-wrap: wrap; }
.filter-group label { font-size: 0.8em; cursor: pointer; padding: 3px 8px; border-radius: 3px; border: 1px solid #333; transition: all 0.15s; }
.filter-group label:hover { border-color: #666; }
.filter-group label.active { border-color: #4A90D9; background: #16213e; }
.filter-group input[type="checkbox"] { display: none; }
.repo-tecs-l { color: #4A90D9; }
.repo-sedi { color: #E67E22; }
.repo-anima { color: #2ECC71; }
.tabs { display: flex; gap: 5px; margin-bottom: 10px; }
.tab { padding: 6px 16px; background: #16213e; border: 1px solid #333; color: #888; cursor: pointer; border-radius: 4px 4px 0 0; font-family: inherit; font-size: 0.85em; transition: all 0.15s; }
.tab.active { background: #1a1a2e; color: #fff; border-bottom-color: #1a1a2e; }
.tab:hover { color: #ccc; }
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: 0.8em; }
th { background: #16213e; padding: 6px 8px; text-align: left; cursor: pointer; user-select: none; position: sticky; top: 0; white-space: nowrap; }
th:hover { background: #1f305e; }
th .sort-arrow { margin-left: 4px; color: #555; }
th .sort-arrow.asc::after { content: ' \25B2'; }
th .sort-arrow.desc::after { content: ' \25BC'; }
td { padding: 4px 8px; border-bottom: 1px solid #222; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 400px; }
td.title-col { white-space: normal; max-width: 500px; }
tr:hover { background: #16213e; }
.count { background: #16213e; padding: 5px 10px; border-radius: 4px; font-size: 0.8em; color: #888; white-space: nowrap; }
.no-results { text-align: center; padding: 40px; color: #555; }
#graph-container { display: none; position: relative; width: 100%; min-height: 900px; }
#graph-canvas { background: #0f0f23; border-radius: 4px; cursor: grab; width: 100%; height: 900px; display: block; }
#graph-canvas:active { cursor: grabbing; }
#graph-tooltip { position: absolute; display: none; padding: 6px 10px; background: rgba(22,33,62,0.95); border: 1px solid #444; border-radius: 4px; font-size: 0.8em; pointer-events: none; max-width: 300px; white-space: nowrap; color: #e0e0e0; z-index: 10; }
#graph-stats { position: absolute; top: 10px; right: 10px; font-size: 0.75em; color: #666; }
#graph-legend { position: absolute; bottom: 10px; left: 10px; font-size: 0.7em; color: #888; background: rgba(15,15,35,0.85); padding: 8px 12px; border-radius: 4px; border: 1px solid #333; line-height: 1.6; }
#graph-legend b { color: #ccc; }
.legend-line { display: flex; align-items: center; gap: 6px; }
.legend-swatch { display: inline-block; width: 20px; height: 3px; border-radius: 1px; }
.legend-hub { display: inline-block; width: 12px; height: 12px; border-radius: 50%; border: 2px solid #FFD700; }
@media (max-width: 768px) {
  body { padding: 10px; }
  .controls { flex-direction: column; }
  td { font-size: 0.75em; padding: 3px 5px; }
  td.title-col { max-width: 200px; }
}
</style>
</head>
<body>

<div class="header">
  <h1>Math Atlas</h1>
  <div class="stats" id="stats"></div>
</div>

<div class="controls">
  <input type="text" class="search" id="search" placeholder="Search ID, title, domain, grade...">
  <div class="filters">
    <div class="filter-group" id="repo-filters"></div>
    <div class="filter-group" id="grade-filters"></div>
  </div>
  <div class="count" id="count"></div>
</div>

<div class="tabs">
  <div class="tab active" id="tab-hypotheses" onclick="switchTab('hypotheses')">Hypotheses</div>
  <div class="tab" id="tab-constants" onclick="switchTab('constants')">Constant Maps</div>
  <div class="tab" id="tab-graph" onclick="switchTab('graph')">Graph</div>
  <div class="tab" id="tab-tree" onclick="switchTab('tree')">Tree</div>
</div>

<div class="table-wrap" id="hypotheses-table"></div>
<div class="table-wrap" id="constants-table" style="display:none"></div>
<div id="tree-container" style="display:none; overflow:auto; background:#0f0f23; border-radius:4px; padding:20px; font-size:0.7em; line-height:1.3;">
<pre id="tree-content" style="color:#e0e0e0;">__TREE_ASCII__</pre>
</div>
<div id="graph-container" style="display:none">
  <canvas id="graph-canvas" height="900"></canvas>
  <div id="graph-tooltip"></div>
  <div id="graph-stats"></div>
  <div id="graph-legend">
    <b>Legend</b><br>
    <div class="legend-line"><span class="legend-swatch" style="background:rgba(255,200,50,0.7);height:4px"></span> Strong (w>=5)</div>
    <div class="legend-line"><span class="legend-swatch" style="background:rgba(180,180,255,0.5);height:3px"></span> Medium (w>=3)</div>
    <div class="legend-line"><span class="legend-swatch" style="background:rgba(100,100,100,0.3);height:2px"></span> Weak (w=1)</div>
    <div class="legend-line"><span class="legend-hub"></span> Hub node (high degree)</div>
    <div class="legend-line" style="color:#666">Cluster = colored background</div>
  </div>
</div>

<script>
const ATLAS = __ATLAS_JSON__;
const GRAPH = __GRAPH_JSON__;

let currentTab = 'hypotheses';
let sortCol = null;
let sortAsc = true;
let searchText = '';
let activeRepos = new Set(__REPO_LIST__);
let activeGrades = null;

const REPO_COLORS = {'TECS-L': '#4A90D9', 'SEDI': '#E67E22', 'anima': '#2ECC71'};
const ALL_REPOS = __REPO_LIST__;

function init() {
  var statsEl = document.getElementById('stats');
  statsEl.textContent = 'Generated: ' + ATLAS.generated + ' | ' + ATLAS.total + ' hypotheses | ' + ATLAS.constant_maps.length + ' constant maps';

  var repoDiv = document.getElementById('repo-filters');
  ALL_REPOS.forEach(function(r) {
    var lbl = document.createElement('label');
    lbl.className = 'active';
    var cb = document.createElement('input');
    cb.type = 'checkbox';
    cb.checked = true;
    cb.value = r;
    cb.addEventListener('change', function() {
      if (this.checked) { activeRepos.add(r); lbl.classList.add('active'); }
      else { activeRepos.delete(r); lbl.classList.remove('active'); }
      render();
    });
    var span = document.createElement('span');
    span.className = repoClass(r);
    span.textContent = r;
    lbl.appendChild(cb);
    lbl.appendChild(span);
    repoDiv.appendChild(lbl);
  });

  var grades = collectGrades();
  var gradeDiv = document.getElementById('grade-filters');
  grades.forEach(function(g) {
    var lbl = document.createElement('label');
    lbl.className = 'active';
    var cb = document.createElement('input');
    cb.type = 'checkbox';
    cb.checked = true;
    cb.value = g;
    cb.addEventListener('change', function() {
      if (activeGrades === null) {
        activeGrades = new Set(grades);
      }
      if (this.checked) { activeGrades.add(g); lbl.classList.add('active'); }
      else { activeGrades.delete(g); lbl.classList.remove('active'); }
      render();
    });
    var span = document.createElement('span');
    span.textContent = g || '(none)';
    lbl.appendChild(cb);
    lbl.appendChild(span);
    lbl.appendChild(document.createTextNode(' '));
    gradeDiv.appendChild(lbl);
  });

  document.getElementById('search').addEventListener('input', function() {
    searchText = this.value.toLowerCase();
    render();
  });

  render();
}

function collectGrades() {
  var seen = {};
  ATLAS.hypotheses.forEach(function(h) {
    var g = h.grade || '(none)';
    if (!seen[g]) seen[g] = 0;
    seen[g]++;
  });
  var arr = Object.keys(seen);
  arr.sort(function(a, b) { return seen[b] - seen[a]; });
  return arr.slice(0, 12);
}

function repoClass(r) {
  return 'repo-' + r.toLowerCase().replace('-', '-');
}

function repoCssClass(r) {
  if (r === 'TECS-L') return 'repo-tecs-l';
  if (r === 'SEDI') return 'repo-sedi';
  if (r === 'anima') return 'repo-anima';
  return '';
}

function esc(s) {
  if (!s) return '';
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function shortId(fullId) {
  var idx = fullId.indexOf(':');
  return idx >= 0 ? fullId.substring(idx + 1) : fullId;
}

function matches(item, text) {
  var fields = [item.id, item.title, item.grade, item.domain, item.repo, item.name, item.file, item.type, item.category];
  for (var i = 0; i < fields.length; i++) {
    if (fields[i] && String(fields[i]).toLowerCase().indexOf(text) >= 0) return true;
  }
  return false;
}

function cmp(a, b) {
  var va = a[sortCol], vb = b[sortCol];
  if (va == null) va = '';
  if (vb == null) vb = '';
  if (typeof va === 'number' && typeof vb === 'number') return sortAsc ? va - vb : vb - va;
  va = String(va).toLowerCase();
  vb = String(vb).toLowerCase();
  if (va < vb) return sortAsc ? -1 : 1;
  if (va > vb) return sortAsc ? 1 : -1;
  return 0;
}

function sortBy(col) {
  if (sortCol === col) { sortAsc = !sortAsc; }
  else { sortCol = col; sortAsc = true; }
  render();
}

function switchTab(tab) {
  currentTab = tab;
  document.getElementById('tab-hypotheses').className = tab === 'hypotheses' ? 'tab active' : 'tab';
  document.getElementById('tab-constants').className = tab === 'constants' ? 'tab active' : 'tab';
  document.getElementById('tab-graph').className = tab === 'graph' ? 'tab active' : 'tab';
  document.getElementById('tab-tree').className = tab === 'tree' ? 'tab active' : 'tab';
  document.getElementById('hypotheses-table').style.display = tab === 'hypotheses' ? '' : 'none';
  document.getElementById('constants-table').style.display = tab === 'constants' ? '' : 'none';
  document.getElementById('graph-container').style.display = tab === 'graph' ? 'block' : 'none';
  document.getElementById('tree-container').style.display = tab === 'tree' ? 'block' : 'none';
  sortCol = null;
  sortAsc = true;
  if (tab === 'graph') { setTimeout(initGraph, 50); }
  render();
}

function render() {
  if (currentTab === 'hypotheses') renderHypotheses();
  else if (currentTab === 'constants') renderConstants();
  else if (currentTab === 'graph') renderGraph();
}

function sortArrow(col) {
  if (sortCol !== col) return '<span class="sort-arrow"></span>';
  return '<span class="sort-arrow ' + (sortAsc ? 'asc' : 'desc') + '"></span>';
}

function renderHypotheses() {
  var data = ATLAS.hypotheses.filter(function(h) {
    if (!activeRepos.has(h.repo)) return false;
    if (activeGrades !== null) {
      var g = h.grade || '(none)';
      if (!activeGrades.has(g)) return false;
    }
    if (searchText && !matches(h, searchText)) return false;
    return true;
  });
  if (sortCol) data.sort(cmp);
  var cols = ['id', 'title', 'grade', 'domain', 'repo', 'file'];
  var html = '<table><thead><tr>';
  cols.forEach(function(c) {
    html += '<th onclick="sortBy(\'' + c + '\')">' + c + sortArrow(c) + '</th>';
  });
  html += '</tr></thead><tbody>';
  if (data.length === 0) {
    html += '<tr><td colspan="' + cols.length + '" class="no-results">No matching hypotheses</td></tr>';
  }
  data.forEach(function(h) {
    var rc = repoCssClass(h.repo);
    html += '<tr>';
    html += '<td class="' + rc + '">' + esc(shortId(h.id)) + '</td>';
    html += '<td class="title-col">' + esc(h.title || '') + '</td>';
    html += '<td>' + esc(h.grade || '-') + '</td>';
    html += '<td>' + esc(h.domain || '-') + '</td>';
    html += '<td class="' + rc + '">' + esc(h.repo) + '</td>';
    html += '<td>' + esc(h.file || '') + '</td>';
    html += '</tr>';
  });
  html += '</tbody></table>';
  document.getElementById('hypotheses-table').innerHTML = html;
  document.getElementById('count').textContent = data.length + ' / ' + ATLAS.hypotheses.length;
}

function renderConstants() {
  var data = ATLAS.constant_maps.filter(function(c) {
    if (!activeRepos.has(c.repo)) return false;
    if (searchText && !matches(c, searchText)) return false;
    return true;
  });
  if (sortCol) data.sort(cmp);
  var cols = ['name', 'repo', 'file', 'type', 'size', 'category', 'evaluable'];
  var html = '<table><thead><tr>';
  cols.forEach(function(c) {
    html += '<th onclick="sortBy(\'' + c + '\')">' + c + sortArrow(c) + '</th>';
  });
  html += '</tr></thead><tbody>';
  if (data.length === 0) {
    html += '<tr><td colspan="' + cols.length + '" class="no-results">No matching constants</td></tr>';
  }
  data.forEach(function(c) {
    var rc = repoCssClass(c.repo);
    html += '<tr>';
    html += '<td>' + esc(c.name) + '</td>';
    html += '<td class="' + rc + '">' + esc(c.repo) + '</td>';
    html += '<td>' + esc(c.file) + ':' + c.line + '</td>';
    html += '<td>' + esc(c.type || '-') + '</td>';
    html += '<td>' + c.size + '</td>';
    html += '<td>' + esc(c.category || '-') + '</td>';
    html += '<td>' + (c.evaluable ? 'Y' : '-') + '</td>';
    html += '</tr>';
  });
  html += '</tbody></table>';
  document.getElementById('constants-table').innerHTML = html;
  document.getElementById('count').textContent = data.length + ' / ' + ATLAS.constant_maps.length;
}

// ── Static graph (pre-computed layout, no simulation) ──
var G = null;
var graphInited = false;
// Grade-based colors (emoji → color)
function gradeColor(grade) {
  if (!grade) return '#556677';
  if (grade.indexOf('\u2b50') >= 0 || grade.indexOf('\u2605') >= 0) return '#FFD700';
  if (grade.indexOf('\uD83D\uDFE9') >= 0) return '#2ECC71';
  if (grade.indexOf('\uD83D\uDFE7') >= 0) return '#E67E22';
  if (grade.indexOf('\uD83D\uDFE6') >= 0) return '#3498DB';
  if (grade.indexOf('\u2705') >= 0) return '#27AE60';
  if (grade.indexOf('\u26AA') >= 0) return '#7F8C8D';
  if (grade.indexOf('\u2B1B') >= 0) return '#2C3E50';
  return '#556677';
}

function gradeRadius(grade, deg, maxDeg) {
  var base = 3;
  if (grade) {
    if (grade.indexOf('\u2b50') >= 0 || grade.indexOf('\u2605') >= 0) base = 6;
    else if (grade.indexOf('\uD83D\uDFE9') >= 0) base = 5;
    else if (grade.indexOf('\uD83D\uDFE7') >= 0) base = 4;
  }
  // Degree-proportional scaling: sqrt(deg) for visual area proportionality
  // deg=1 → 1x, deg=10 → ~3.2x, deg=24 → ~5x
  var degScale = 1 + 2.5 * Math.sqrt((deg || 0) / Math.max(maxDeg || 1, 1));
  return Math.round(base * degScale);
}

// Cluster colors (12 distinct muted tones for background)
var CLUSTER_COLORS = [
  'rgba(74,144,217,0.08)', 'rgba(230,126,34,0.08)', 'rgba(46,204,113,0.08)',
  'rgba(155,89,182,0.08)', 'rgba(241,196,15,0.08)', 'rgba(231,76,60,0.08)',
  'rgba(26,188,156,0.08)', 'rgba(52,152,219,0.08)', 'rgba(243,156,18,0.08)',
  'rgba(142,68,173,0.08)', 'rgba(39,174,96,0.08)', 'rgba(192,57,43,0.08)',
];
var CLUSTER_LABEL_COLORS = [
  'rgba(74,144,217,0.5)', 'rgba(230,126,34,0.5)', 'rgba(46,204,113,0.5)',
  'rgba(155,89,182,0.5)', 'rgba(241,196,15,0.5)', 'rgba(231,76,60,0.5)',
  'rgba(26,188,156,0.5)', 'rgba(52,152,219,0.5)', 'rgba(243,156,18,0.5)',
  'rgba(142,68,173,0.5)', 'rgba(39,174,96,0.5)', 'rgba(192,57,43,0.5)',
];

function hexToRgba(hex, alpha) {
  var r = parseInt(hex.slice(1,3), 16);
  var g = parseInt(hex.slice(3,5), 16);
  var b = parseInt(hex.slice(5,7), 16);
  return 'rgba(' + r + ',' + g + ',' + b + ',' + alpha + ')';
}

function edgeColor(w, highlighted) {
  if (highlighted) return 'rgba(255,255,100,0.8)';
  if (w >= 5) return 'rgba(255,200,50,0.5)';
  if (w >= 3) return 'rgba(180,180,255,0.4)';
  if (w >= 2) return 'rgba(140,140,200,0.3)';
  return 'rgba(100,100,100,0.2)';
}

function edgeWidth(w, highlighted) {
  if (highlighted) return Math.max(2, w * 0.8);
  return Math.max(0.3, Math.min(w * 0.6, 4));
}

function initGraph() {
  if (graphInited) return;
  graphInited = true;
  var canvas = document.getElementById('graph-canvas');
  var container = document.getElementById('graph-container');
  canvas.width = container.offsetWidth || document.body.clientWidth - 40;
  if (canvas.width < 100) canvas.width = document.body.clientWidth - 40;
  canvas.height = 900;

  var maxDeg = GRAPH.maxDeg || 1;
  var clusters = GRAPH.clusters || [];
  var categories = GRAPH.categories || [];

  var nodes = GRAPH.nodes.map(function(n, i) {
    var shortId = n.id.indexOf(':') >= 0 ? n.id.substring(n.id.indexOf(':') + 1) : n.id;
    return {
      idx: i, id: n.id, shortId: shortId, title: n.title, repo: n.repo,
      grade: n.grade, color: gradeColor(n.grade),
      radius: gradeRadius(n.grade, n.deg, maxDeg),
      deg: n.deg || 0, cl: n.cl || 0,
      x: n.x, y: n.y,
      hidden: false, dimmed: false
    };
  });

  var edges = GRAPH.edges;
  var adj = {};
  nodes.forEach(function(n, i) { adj[i] = new Set(); });
  edges.forEach(function(e) { adj[e.source].add(e.target); adj[e.target].add(e.source); });

  // Find top hub nodes
  var hubThreshold = Math.max(3, maxDeg * 0.4);

  document.getElementById('graph-stats').textContent = nodes.length + ' nodes, ' + edges.length + ' edges | ' + clusters.length + ' clusters | hub threshold: deg>' + Math.round(hubThreshold);

  G = {
    nodes: nodes, edges: edges, adj: adj, canvas: canvas,
    clusters: clusters, categories: categories,
    centerX: GRAPH.centerX || 2500, centerY: GRAPH.centerY || 2500,
    hubThreshold: hubThreshold,
    ctx: canvas.getContext('2d'),
    transform: { x: 0, y: 0, k: 1 },
    selected: null, isPanning: false, panStart: null
  };

  // Auto-fit: compute bounding box of all nodes → fit to canvas
  var mnx = Infinity, mny = Infinity, mxx = -Infinity, mxy = -Infinity;
  for (var i = 0; i < nodes.length; i++) {
    if (nodes[i].x < mnx) mnx = nodes[i].x;
    if (nodes[i].y < mny) mny = nodes[i].y;
    if (nodes[i].x > mxx) mxx = nodes[i].x;
    if (nodes[i].y > mxy) mxy = nodes[i].y;
  }
  var dataW = mxx - mnx + 100, dataH = mxy - mny + 100;
  var fitScale = Math.min(canvas.width / dataW, canvas.height / dataH, 1.0);
  G.transform.k = fitScale;
  G.transform.x = canvas.width / 2 - ((mnx + mxx) / 2) * fitScale;
  G.transform.y = canvas.height / 2 - ((mny + mxy) / 2) * fitScale;

  setupGraphEvents();
  drawGraph();
}

function drawGraph() {
  if (!G) return;
  var ctx = G.ctx;
  var W = G.canvas.width, H = G.canvas.height;
  ctx.clearRect(0, 0, W, H);
  ctx.save();
  ctx.translate(G.transform.x, G.transform.y);
  ctx.scale(G.transform.k, G.transform.k);

  var nodes = G.nodes, edges = G.edges;
  var hasSel = G.selected !== null;

  // ── Draw center n=6 hub ──
  var centerX = G.centerX, centerY = G.centerY;
  // Radial guide lines from center to each category
  for (var ci = 0; ci < G.categories.length; ci++) {
    var cat = G.categories[ci];
    var catCx = cat.x + cat.w / 2, catCy = cat.y + cat.h / 2;
    ctx.strokeStyle = hexToRgba(cat.color, 0.15);
    ctx.lineWidth = 1;
    ctx.setLineDash([6, 4]);
    ctx.beginPath(); ctx.moveTo(centerX, centerY); ctx.lineTo(catCx, catCy); ctx.stroke();
    ctx.setLineDash([]);
  }
  // Center node
  ctx.fillStyle = '#FFD700';
  ctx.beginPath(); ctx.arc(centerX, centerY, 18, 0, Math.PI * 2); ctx.fill();
  ctx.strokeStyle = '#fff';
  ctx.lineWidth = 3;
  ctx.beginPath(); ctx.arc(centerX, centerY, 18, 0, Math.PI * 2); ctx.stroke();
  if (G.transform.k > 0.2) {
    ctx.fillStyle = '#000';
    ctx.font = 'bold 14px monospace';
    ctx.textAlign = 'center';
    ctx.fillText('n=6', centerX, centerY + 5);
    ctx.textAlign = 'left';
  }

  // ── Draw category boxes (Level 1) ──
  for (var ci = 0; ci < G.categories.length; ci++) {
    var cat = G.categories[ci];
    // Background
    ctx.fillStyle = hexToRgba(cat.color, 0.06);
    ctx.fillRect(cat.x, cat.y, cat.w, cat.h);
    // Border
    ctx.strokeStyle = hexToRgba(cat.color, 0.4);
    ctx.lineWidth = 2;
    ctx.strokeRect(cat.x, cat.y, cat.w, cat.h);
    // Category title at top
    if (G.transform.k > 0.15) {
      ctx.fillStyle = cat.color;
      ctx.font = 'bold 16px monospace';
      ctx.fillText(cat.name, cat.x + 10, cat.y + 18);
    }
  }

  // ── Draw cluster rectangles (Level 2 — sub-domain boxes) ──
  for (var ci = 0; ci < G.clusters.length; ci++) {
    var cl = G.clusters[ci];
    var cIdx = cl.id % CLUSTER_COLORS.length;
    var bx = cl.x1, by = cl.y1, bw = cl.x2 - cl.x1, bh = cl.y2 - cl.y1;
    // Background fill
    ctx.fillStyle = CLUSTER_COLORS[cIdx];
    ctx.fillRect(bx, by, bw, bh);
    // Border
    ctx.strokeStyle = CLUSTER_LABEL_COLORS[cIdx];
    ctx.lineWidth = 1;
    ctx.setLineDash([3, 2]);
    ctx.strokeRect(bx, by, bw, bh);
    ctx.setLineDash([]);
    // Label at top-left
    if (G.transform.k > 0.25) {
      ctx.fillStyle = CLUSTER_LABEL_COLORS[cIdx];
      ctx.font = '10px monospace';
      ctx.fillText(cl.name + ' (' + cl.n + ')', bx + 4, by - 3);
    }
  }

  // ── Draw edges with weight-based thickness/color ──
  for (var i = 0; i < edges.length; i++) {
    var e = edges[i];
    var s = nodes[e.source], t = nodes[e.target];
    if (s.hidden || t.hidden) continue;
    var edgeDim = s.dimmed && t.dimmed;
    var edgeHi = hasSel && (e.source === G.selected || e.target === G.selected);
    var w = e.w || 1;
    if (edgeDim) {
      ctx.strokeStyle = 'rgba(100,100,100,0.05)';
      ctx.lineWidth = 0.3;
    } else {
      ctx.strokeStyle = edgeColor(w, edgeHi);
      ctx.lineWidth = edgeWidth(w, edgeHi);
    }
    ctx.beginPath(); ctx.moveTo(s.x, s.y); ctx.lineTo(t.x, t.y); ctx.stroke();
  }

  // ── Draw nodes with hub highlighting ──
  for (var i = 0; i < nodes.length; i++) {
    var n = nodes[i];
    if (n.hidden) continue;
    var isHi = hasSel && (i === G.selected || G.adj[G.selected].has(i));
    var isHub = n.deg >= G.hubThreshold;
    ctx.fillStyle = n.dimmed ? 'rgba(80,80,80,0.3)' : (isHi ? '#fff' : n.color);
    ctx.beginPath(); ctx.arc(n.x, n.y, n.radius, 0, Math.PI * 2); ctx.fill();
    // Hub ring (double outline)
    if (isHub && !n.dimmed) {
      ctx.strokeStyle = '#FFD700';
      ctx.lineWidth = 2;
      ctx.beginPath(); ctx.arc(n.x, n.y, n.radius + 3, 0, Math.PI * 2); ctx.stroke();
    }
    if (isHi) { ctx.strokeStyle = n.color; ctx.lineWidth = 2; ctx.stroke(); }
    // Labels: show for hubs or large nodes
    var showLabel = (n.radius >= 7 || isHub) && G.transform.k > 0.4 && !n.dimmed;
    if (showLabel) {
      ctx.fillStyle = isHub ? '#FFD700' : '#ddd';
      ctx.font = isHub ? 'bold 10px monospace' : '9px monospace';
      ctx.fillText(n.shortId, n.x + n.radius + 4, n.y + 3);
      if (isHub) {
        ctx.font = '8px monospace';
        ctx.fillStyle = '#888';
        ctx.fillText('deg:' + n.deg, n.x + n.radius + 4, n.y + 13);
      }
    }
  }
  ctx.restore();
}

function canvasToWorld(cx, cy) {
  return { x: (cx - G.transform.x) / G.transform.k, y: (cy - G.transform.y) / G.transform.k };
}
function findNodeAt(wx, wy) {
  for (var i = G.nodes.length - 1; i >= 0; i--) {
    var n = G.nodes[i]; if (n.hidden) continue;
    var dx = n.x - wx, dy = n.y - wy;
    if (dx*dx + dy*dy <= (n.radius+3)*(n.radius+3)) return i;
  }
  return -1;
}

function setupGraphEvents() {
  var canvas = G.canvas;
  var tooltip = document.getElementById('graph-tooltip');

  canvas.addEventListener('mousedown', function(ev) {
    var rect = canvas.getBoundingClientRect();
    var mx = ev.clientX - rect.left, my = ev.clientY - rect.top;
    G.isPanning = true;
    G.panStart = { mx: mx, my: my, tx: G.transform.x, ty: G.transform.y };
  });

  canvas.addEventListener('mousemove', function(ev) {
    var rect = canvas.getBoundingClientRect();
    var mx = ev.clientX - rect.left, my = ev.clientY - rect.top;
    if (G.isPanning && G.panStart) {
      G.transform.x = G.panStart.tx + (mx - G.panStart.mx);
      G.transform.y = G.panStart.ty + (my - G.panStart.my);
      drawGraph();
    } else {
      var w = canvasToWorld(mx, my);
      var idx = findNodeAt(w.x, w.y);
      if (idx >= 0) {
        var n = G.nodes[idx];
        var clInfo = G.clusters.find(function(cl) { return cl.id === n.cl; });
        var clName = clInfo ? clInfo.name : '?';
        tooltip.innerHTML = '<b>' + esc(n.shortId) + '</b> ' + esc(n.grade || '') + '<br>' + esc(n.title) + '<br><span style="color:' + n.color + '">' + esc(n.repo) + '</span> | cluster: ' + esc(clName) + ' | deg: ' + n.deg;
        tooltip.style.display = 'block';
        tooltip.style.left = (mx + 12) + 'px';
        tooltip.style.top = (my - 10) + 'px';
        canvas.style.cursor = 'pointer';
      } else {
        tooltip.style.display = 'none';
        canvas.style.cursor = 'grab';
      }
    }
  });

  canvas.addEventListener('mouseup', function(ev) {
    if (G.isPanning) { G.isPanning = false; G.panStart = null; return; }
    var rect = canvas.getBoundingClientRect();
    var mx = ev.clientX - rect.left, my = ev.clientY - rect.top;
    var w = canvasToWorld(mx, my);
    var idx = findNodeAt(w.x, w.y);
    G.selected = (idx >= 0 && G.selected !== idx) ? idx : null;
    drawGraph();
  });

  canvas.addEventListener('mouseleave', function() {
    tooltip.style.display = 'none';
    G.isPanning = false;
  });

  canvas.addEventListener('wheel', function(ev) {
    ev.preventDefault();
    var rect = canvas.getBoundingClientRect();
    var mx = ev.clientX - rect.left, my = ev.clientY - rect.top;
    var delta = ev.deltaY > 0 ? 0.9 : 1.1;
    var newK = Math.max(0.1, Math.min(5, G.transform.k * delta));
    var ratio = newK / G.transform.k;
    G.transform.x = mx - (mx - G.transform.x) * ratio;
    G.transform.y = my - (my - G.transform.y) * ratio;
    G.transform.k = newK;
    drawGraph();
  }, { passive: false });

  // ── Touch events (mobile) ──
  var lastTouchDist = 0;

  canvas.addEventListener('touchstart', function(ev) {
    ev.preventDefault();
    var rect = canvas.getBoundingClientRect();
    if (ev.touches.length === 1) {
      var t = ev.touches[0];
      var mx = t.clientX - rect.left, my = t.clientY - rect.top;
      G.isPanning = true;
      G.panStart = { mx: mx, my: my, tx: G.transform.x, ty: G.transform.y };
    } else if (ev.touches.length === 2) {
      var dx = ev.touches[1].clientX - ev.touches[0].clientX;
      var dy = ev.touches[1].clientY - ev.touches[0].clientY;
      lastTouchDist = Math.sqrt(dx * dx + dy * dy);
    }
  }, { passive: false });

  canvas.addEventListener('touchmove', function(ev) {
    ev.preventDefault();
    var rect = canvas.getBoundingClientRect();
    if (ev.touches.length === 1 && G.isPanning && G.panStart) {
      var t = ev.touches[0];
      var mx = t.clientX - rect.left, my = t.clientY - rect.top;
      G.transform.x = G.panStart.tx + (mx - G.panStart.mx);
      G.transform.y = G.panStart.ty + (my - G.panStart.my);
      drawGraph();
    } else if (ev.touches.length === 2) {
      var dx = ev.touches[1].clientX - ev.touches[0].clientX;
      var dy = ev.touches[1].clientY - ev.touches[0].clientY;
      var dist = Math.sqrt(dx * dx + dy * dy);
      if (lastTouchDist > 0) {
        var scale = dist / lastTouchDist;
        var cx = (ev.touches[0].clientX + ev.touches[1].clientX) / 2 - rect.left;
        var cy = (ev.touches[0].clientY + ev.touches[1].clientY) / 2 - rect.top;
        var newK = Math.max(0.1, Math.min(5, G.transform.k * scale));
        var ratio = newK / G.transform.k;
        G.transform.x = cx - (cx - G.transform.x) * ratio;
        G.transform.y = cy - (cy - G.transform.y) * ratio;
        G.transform.k = newK;
        drawGraph();
      }
      lastTouchDist = dist;
    }
  }, { passive: false });

  canvas.addEventListener('touchend', function(ev) {
    if (ev.touches.length === 0) {
      if (G.isPanning) { G.isPanning = false; G.panStart = null; }
      lastTouchDist = 0;
    }
  });
}

function renderGraph() {
  if (!G) return;
  var hasSearch = searchText.length > 0;
  var visibleCount = 0;
  for (var i = 0; i < G.nodes.length; i++) {
    var n = G.nodes[i];
    n.hidden = !activeRepos.has(n.repo);
    n.dimmed = hasSearch && !matches(n, searchText);
    if (!n.hidden && !n.dimmed) visibleCount++;
  }
  document.getElementById('count').textContent = visibleCount + ' / ' + G.nodes.length + ' nodes';
  drawGraph();
}

init();
</script>
</body>
</html>'''


def write_html(atlas, htmlpath):
    """Write atlas data as a self-contained interactive HTML file.

    Embeds a slimmed-down version of the atlas JSON (constant_maps without
    values/keys) directly into the HTML as a JavaScript variable.

    Args:
        atlas: dict returned by build_atlas().
        htmlpath: Path to the output .html file.
    """
    # Strip values/keys from constant_maps to keep HTML small
    slim_constants = []
    for cm in atlas.get("constant_maps", []):
        slim_constants.append({
            "name": cm["name"],
            "repo": cm["repo"],
            "file": cm["file"],
            "line": cm["line"],
            "type": cm["type"],
            "size": cm["size"],
            "category": cm["category"],
            "evaluable": cm["evaluable"],
        })

    slim_atlas = {
        "generated": atlas["generated"],
        "total": atlas["total"],
        "stats": atlas["stats"],
        "constant_stats": atlas.get("constant_stats", {}),
        "hypotheses": atlas["hypotheses"],
        "constant_maps": slim_constants,
    }

    atlas_json = json.dumps(slim_atlas, ensure_ascii=False)

    # Build graph data (only connected nodes)
    id_lookup = {}
    for h in atlas["hypotheses"]:
        full_id = h["id"]
        short = full_id.split(":", 1)[1] if ":" in full_id else full_id
        if short not in id_lookup:
            id_lookup[short] = full_id

    edges = []
    connected = set()
    for h in atlas["hypotheses"]:
        for ref in h.get("refs", []):
            target = id_lookup.get(ref)
            if target and target != h["id"]:
                edges.append({"source": h["id"], "target": target})
                connected.add(h["id"])
                connected.add(target)

    hyp_by_id = {h["id"]: h for h in atlas["hypotheses"]}
    graph_nodes = []
    node_idx = {}
    for hid in sorted(connected):
        h = hyp_by_id.get(hid)
        if not h:
            continue
        idx = len(graph_nodes)
        node_idx[hid] = idx
        graph_nodes.append({
            "id": hid,
            "title": (h.get("title") or "")[:60],
            "repo": h["repo"],
            "grade": h.get("grade") or "",
        })

    # ── Compute edge weights ──
    # Build ref sets per hypothesis for shared-ref calculation
    ref_sets = {}
    for h in atlas["hypotheses"]:
        targets = set()
        for ref in h.get("refs", []):
            t = id_lookup.get(ref)
            if t and t != h["id"]:
                targets.add(t)
        ref_sets[h["id"]] = targets

    # Build edge pair → weight
    edge_pair_weight = {}
    for e in edges:
        pair = (e["source"], e["target"])
        rev = (e["target"], e["source"])
        key = tuple(sorted(pair))
        w = edge_pair_weight.get(key, 0)
        # Mutual reference: if A→B and B→A, each direction adds 1
        w += 1
        # Same domain bonus
        hs = hyp_by_id.get(e["source"])
        ht = hyp_by_id.get(e["target"])
        if hs and ht and hs.get("domain") and hs["domain"] == ht.get("domain"):
            w += 1
        # Shared refs bonus (both reference same third node)
        rs = ref_sets.get(e["source"], set())
        rt = ref_sets.get(e["target"], set())
        shared = rs & rt - {e["source"], e["target"]}
        w += min(len(shared), 3)  # cap at 3
        edge_pair_weight[key] = w

    graph_edges = []
    seen_edge_pairs = set()
    for e in edges:
        si = node_idx.get(e["source"])
        ti = node_idx.get(e["target"])
        if si is not None and ti is not None:
            key = tuple(sorted((e["source"], e["target"])))
            if key not in seen_edge_pairs:
                seen_edge_pairs.add(key)
                w = edge_pair_weight.get(key, 1)
                graph_edges.append({"source": si, "target": ti, "w": w})

    # ── Compute degree centrality (hub detection) ──
    degree = [0] * len(graph_nodes)
    for e in graph_edges:
        degree[e["source"]] += 1
        degree[e["target"]] += 1
    max_deg = max(degree) if degree else 1
    for i, n in enumerate(graph_nodes):
        n["deg"] = degree[i]

    # ── Semantic hierarchical clustering ──
    import math, random

    # Top-level categories → sub-domains mapping
    CATEGORY_MAP = {
        "PURE MATH": ["NT", "ALGGEOM", "COMB", "CYCL", "HARMONIC", "KTHY",
                       "LATT", "LIE", "MOTIV", "OPERAD", "PACK", "SPEC",
                       "SPOR", "CF", "CODE", "MP"],
        "PHYSICS": ["PH", "SIM", "CERN", "GEO", "SLE", "UD", "EN",
                     "CLIFFORD", "ROB", "SEDI"],
        "BIOLOGY": ["BIO", "DNA", "CHEM"],
        "CONSCIOUSNESS": ["CX", "CA", "CS", "AX"],
        "ENGINEERING": ["EE", "AF", "TOP", "NOBEL"],
    }

    # Reverse map: domain → category
    domain_to_cat = {}
    for cat, doms in CATEGORY_MAP.items():
        for d in doms:
            domain_to_cat[d] = cat

    # Step 1: Assign raw domain + category
    for i, n in enumerate(graph_nodes):
        h = hyp_by_id.get(n["id"])
        dom = (h.get("domain") or "") if h else ""
        repo = h.get("repo", "other") if h else "other"
        # For nodes without domain (TECS-L numbered hypotheses), use repo
        if not dom:
            dom = repo
        n["_domain"] = dom
        n["_cat"] = domain_to_cat.get(dom, "OTHER")

    # Step 2: Build leaf clusters (split large ones by number range)
    domain_counts = {}
    for n in graph_nodes:
        domain_counts[n["_domain"]] = domain_counts.get(n["_domain"], 0) + 1

    MAX_CLUSTER = 40
    domain_clusters = {}
    cluster_id = 0
    for n in graph_nodes:
        dom = n["_domain"]
        cat = n["_cat"]
        if domain_counts[dom] > MAX_CLUSTER:
            hid = n["id"].split(":", 1)[1] if ":" in n["id"] else n["id"]
            m = re.search(r'(\d+)', hid)
            num = int(m.group(1)) if m else 0
            bucket = num // 200
            sub_key = f"{cat}/{dom}-{bucket}"
            label = f"{dom} {bucket*200}-{bucket*200+199}"
        else:
            sub_key = f"{cat}/{dom}"
            label = dom

        if sub_key not in domain_clusters:
            domain_clusters[sub_key] = (cluster_id, label, cat)
            cluster_id += 1
        n["cl"] = domain_clusters[sub_key][0]

    cluster_names = {cid: label for _, (cid, label, _) in domain_clusters.items()}
    cluster_cat = {cid: cat for _, (cid, _, cat) in domain_clusters.items()}

    # ── Radial tree layout: n=6 at center, categories radiate outward ──
    #
    #  Center:   n=6 hub node
    #  Ring 1:   Category sectors (PURE MATH, PHYSICS, BIO, CONSCIOUSNESS, ...)
    #  Ring 2+:  Sub-domain cluster boxes within each sector
    #
    random.seed(42)
    N = len(graph_nodes)
    NODE_SPACE = 35

    # Group clusters by category
    cl_members = {}
    for i, n in enumerate(graph_nodes):
        cl_members.setdefault(n["cl"], []).append(i)

    cat_clusters = {}
    for cid in cl_members:
        cat = cluster_cat.get(cid, "OTHER")
        cat_clusters.setdefault(cat, []).append(cid)

    # Sort categories by total node count (largest gets most angle)
    cat_order = sorted(cat_clusters.keys(),
                       key=lambda c: -sum(len(cl_members[cid]) for cid in cat_clusters[c]))
    total_nodes = sum(len(cl_members[cid]) for cid in cl_members)

    # Compute leaf cluster box sizes
    cl_box = {}
    for cid in cl_members:
        n_nodes = len(cl_members[cid])
        side = max(NODE_SPACE * math.sqrt(n_nodes), 55)
        cl_box[cid] = {"w": side * 1.2, "h": side}

    # Canvas: large enough for radial spread
    CX, CY = 2500, 2500  # center point
    INNER_R = 180   # inner ring start (category labels)
    CLUSTER_R = 280  # where cluster boxes start

    # Assign angular sectors to categories proportional to node count
    angle_cursor = -math.pi / 2  # start at top
    cat_sectors = {}
    MIN_ANGLE = math.pi / 8  # minimum sector width

    for cat in cat_order:
        cat_nodes = sum(len(cl_members[cid]) for cid in cat_clusters[cat])
        angle_span = max((cat_nodes / total_nodes) * 2 * math.pi, MIN_ANGLE)
        cat_sectors[cat] = {
            "start": angle_cursor,
            "span": angle_span,
            "mid": angle_cursor + angle_span / 2,
        }
        angle_cursor += angle_span

    # Normalize if total exceeds 2*pi
    total_angle = sum(s["span"] for s in cat_sectors.values())
    if total_angle > 2 * math.pi:
        scale = 2 * math.pi / total_angle
        a = -math.pi / 2
        for cat in cat_order:
            cat_sectors[cat]["span"] *= scale
            cat_sectors[cat]["start"] = a
            cat_sectors[cat]["mid"] = a + cat_sectors[cat]["span"] / 2
            a += cat_sectors[cat]["span"]

    # Place cluster boxes along radial spokes within each sector
    cl_pos = {}
    cat_layout = {}

    for cat in cat_order:
        sector = cat_sectors[cat]
        cids = sorted(cat_clusters[cat], key=lambda c: -len(cl_members[c]))
        n_cls = len(cids)

        # Distribute clusters within the sector angle range
        for idx, cid in enumerate(cids):
            bw, bh = cl_box[cid]["w"], cl_box[cid]["h"]
            # Angle for this cluster within sector
            if n_cls == 1:
                angle = sector["mid"]
            else:
                t = idx / (n_cls - 1)
                angle = sector["start"] + sector["span"] * 0.1 + t * sector["span"] * 0.8

            # Radial distance: further out for more clusters, stagger to avoid overlap
            row = idx // 3  # max 3 per radial level
            r = CLUSTER_R + row * (max(bw, bh) + 40)

            # Place box center
            box_cx = CX + math.cos(angle) * r
            box_cy = CY + math.sin(angle) * r
            cl_pos[cid] = (box_cx - bw / 2, box_cy - bh / 2)

        # Category arc info for rendering
        cat_layout[cat] = {
            "start": sector["start"], "span": sector["span"],
            "mid": sector["mid"],
        }

    # Resolve any remaining overlaps between cluster boxes (greedy push-out)
    cl_ids_list = list(cl_pos.keys())
    for iteration in range(100):
        moved = False
        for i in range(len(cl_ids_list)):
            ci = cl_ids_list[i]
            ax1, ay1 = cl_pos[ci]
            aw, ah = cl_box[ci]["w"], cl_box[ci]["h"]
            ax2, ay2 = ax1 + aw, ay1 + ah
            for j in range(i + 1, len(cl_ids_list)):
                cj = cl_ids_list[j]
                bx1, by1 = cl_pos[cj]
                bw2, bh2 = cl_box[cj]["w"], cl_box[cj]["h"]
                bx2, by2 = bx1 + bw2, by1 + bh2
                # Check overlap with gap
                gap = 15
                if ax1 - gap < bx2 and ax2 + gap > bx1 and ay1 - gap < by2 and ay2 + gap > by1:
                    # Push apart along center-to-center vector
                    ca_x, ca_y = ax1 + aw / 2, ay1 + ah / 2
                    cb_x, cb_y = bx1 + bw2 / 2, by1 + bh2 / 2
                    dx = cb_x - ca_x
                    dy = cb_y - ca_y
                    d = math.sqrt(dx * dx + dy * dy) + 0.1
                    # Push outward from center
                    push = 8
                    cl_pos[ci] = (ax1 - push * dx / d, ay1 - push * dy / d)
                    cl_pos[cj] = (bx1 + push * dx / d, by1 + push * dy / d)
                    moved = True
        if not moved:
            break

    # Compute bounding box
    all_x1 = min(cl_pos[c][0] for c in cl_pos)
    all_y1 = min(cl_pos[c][1] for c in cl_pos)
    all_x2 = max(cl_pos[c][0] + cl_box[c]["w"] for c in cl_pos)
    all_y2 = max(cl_pos[c][1] + cl_box[c]["h"] for c in cl_pos)
    W = int(all_x2 - all_x1 + 200)
    H = int(all_y2 - all_y1 + 200)

    # Place nodes within their cluster box using local force layout
    for cid, members in cl_members.items():
        bx, by = cl_pos[cid]
        bw, bh = cl_box[cid]["w"], cl_box[cid]["h"]
        cx, cy = bx + bw / 2, by + bh / 2

        # Initialize in circle around center
        for idx_m, ni in enumerate(members):
            angle = 2 * math.pi * idx_m / max(len(members), 1)
            r = min(bw, bh) * 0.3 * random.uniform(0.2, 1.0)
            graph_nodes[ni]["x"] = cx + math.cos(angle) * r
            graph_nodes[ni]["y"] = cy + math.sin(angle) * r
            graph_nodes[ni]["vx"] = 0.0
            graph_nodes[ni]["vy"] = 0.0

        # Local force: repulsion + intra-cluster links + boundary constraint
        intra_links = []
        for e in graph_edges:
            if e["source"] in members and e["target"] in members:
                intra_links.append((e["source"], e["target"]))
            elif graph_nodes[e["source"]]["cl"] == cid and graph_nodes[e["target"]]["cl"] == cid:
                intra_links.append((e["source"], e["target"]))
        member_set = set(members)
        intra_links = [(s, t) for s, t in intra_links if s in member_set and t in member_set]

        for tick in range(200):
            alpha = max(0.01, 1.0 - tick / 200)
            for ii in range(len(members)):
                i = members[ii]
                ni = graph_nodes[i]
                for jj in range(ii + 1, len(members)):
                    j = members[jj]
                    nj = graph_nodes[j]
                    dx = nj["x"] - ni["x"]
                    dy = nj["y"] - ni["y"]
                    d = math.sqrt(dx * dx + dy * dy) + 0.1
                    force = -300.0 / (d * d) * alpha
                    if d < 20:
                        force *= 4
                    fx = force * dx / d
                    fy = force * dy / d
                    ni["vx"] -= fx
                    ni["vy"] -= fy
                    nj["vx"] += fx
                    nj["vy"] += fy

            for si, ti in intra_links:
                s, t = graph_nodes[si], graph_nodes[ti]
                dx = t["x"] - s["x"]
                dy = t["y"] - s["y"]
                d = math.sqrt(dx * dx + dy * dy) + 1.0
                force = (d - 40) * 0.01 * alpha
                fx = force * dx / d
                fy = force * dy / d
                s["vx"] += fx
                s["vy"] += fy
                t["vx"] -= fx
                t["vy"] -= fy

            # Center gravity within box
            for ni in members:
                n = graph_nodes[ni]
                n["vx"] += (cx - n["x"]) * 0.005 * alpha
                n["vy"] += (cy - n["y"]) * 0.005 * alpha

            for ni in members:
                n = graph_nodes[ni]
                n["vx"] *= 0.6
                n["vy"] *= 0.6
                n["x"] += n["vx"]
                n["y"] += n["vy"]
                # Hard boundary constraint
                margin = 12
                n["x"] = max(bx + margin, min(bx + bw - margin, n["x"]))
                n["y"] = max(by + margin, min(by + bh - margin, n["y"]))

    # Strip velocity fields
    for n in graph_nodes:
        del n["vx"]
        del n["vy"]
        del n["_domain"]
        n["x"] = round(n["x"], 1)
        n["y"] = round(n["y"], 1)

    # Cluster metadata
    clusters_meta = []
    for cid in sorted(cluster_names.keys()):
        name = cluster_names[cid]
        if cid not in cl_pos:
            continue
        bx, by = cl_pos[cid]
        bw, bh = cl_box[cid]["w"], cl_box[cid]["h"]
        cat = cluster_cat.get(cid, "OTHER")
        clusters_meta.append({
            "id": cid, "name": name, "cat": cat, "n": len(cl_members.get(cid, [])),
            "x1": round(bx, 1), "y1": round(by, 1),
            "x2": round(bx + bw, 1), "y2": round(by + bh, 1),
        })

    # Category metadata (radial sectors)
    categories_meta = []
    CAT_COLORS = {
        "PURE MATH": "#4A90D9", "PHYSICS": "#E67E22", "BIOLOGY": "#2ECC71",
        "CONSCIOUSNESS": "#9B59B6", "ENGINEERING": "#1ABC9C", "OTHER": "#95A5A6",
    }
    for cat in cat_order:
        layout = cat_layout[cat]
        cat_cids = cat_clusters[cat]
        # Bounding box of all clusters in this category
        if cat_cids:
            cx1 = min(cl_pos[c][0] for c in cat_cids if c in cl_pos)
            cy1 = min(cl_pos[c][1] for c in cat_cids if c in cl_pos)
            cx2 = max(cl_pos[c][0] + cl_box[c]["w"] for c in cat_cids if c in cl_pos)
            cy2 = max(cl_pos[c][1] + cl_box[c]["h"] for c in cat_cids if c in cl_pos)
        else:
            cx1 = cy1 = cx2 = cy2 = 0
        pad = 25
        categories_meta.append({
            "name": cat, "color": CAT_COLORS.get(cat, "#95A5A6"),
            "x": round(cx1 - pad, 1), "y": round(cy1 - pad - 20, 1),
            "w": round(cx2 - cx1 + pad * 2, 1), "h": round(cy2 - cy1 + pad * 2 + 20, 1),
            "mid": round(layout["mid"], 4),
        })

    graph_data = json.dumps({
        "nodes": graph_nodes, "edges": graph_edges,
        "clusters": clusters_meta, "categories": categories_meta,
        "centerX": round(CX, 1), "centerY": round(CY, 1),
        "maxDeg": max_deg
    }, ensure_ascii=False)

    # Build repo list from atlas data
    repos = list(atlas.get("stats", {}).keys())
    repo_list_json = json.dumps(repos, ensure_ascii=False)

    # Load ASCII tree from file
    tree_path = Path(__file__).resolve().parent / "atlas_tree.txt"
    tree_ascii = ""
    if tree_path.exists():
        tree_ascii = tree_path.read_text(encoding='utf-8', errors='replace')
    # Escape HTML entities in tree
    tree_ascii = tree_ascii.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    html = HTML_TEMPLATE.replace("__ATLAS_JSON__", atlas_json)
    html = html.replace("__GRAPH_JSON__", graph_data)
    html = html.replace("__REPO_LIST__", repo_list_json)
    html = html.replace("__TREE_ASCII__", tree_ascii)

    with open(htmlpath, 'w', encoding='utf-8') as f:
        f.write(html)


# ── README summary ────────────────────────────────────────────────

def generate_readme_summary(atlas):
    """Generate a markdown summary for README marker insertion.

    Produces a compact overview (~170 lines) of the atlas suitable for
    injection between <!-- SHARED:ATLAS:START --> / <!-- SHARED:ATLAS:END -->
    markers in README files.

    Args:
        atlas: dict returned by build_atlas().

    Returns:
        str: Markdown text.
    """
    lines = []
    total_h = atlas["total"]
    cm_count = len(atlas.get("constant_maps", []))

    lines.append("### Math Atlas (auto-generated)")
    lines.append("")
    lines.append(
        f"> {total_h:,} hypotheses + {cm_count} constant maps across 3 repos"
        " | [Interactive page](https://need-singularity.github.io/TECS-L/math_atlas.html)"
    )
    lines.append("")

    # ── Per-repo summary table ──
    # Count grade categories per repo
    star_chars = ("\u2b50", "\u2605")   # ⭐ ★
    green_char = "\U0001f7e9"           # 🟩
    orange_char = "\U0001f7e7"          # 🟧

    repo_grades = {}  # repo -> {star, green, orange}
    for h in atlas["hypotheses"]:
        repo = h["repo"]
        if repo not in repo_grades:
            repo_grades[repo] = {"star": 0, "green": 0, "orange": 0}
        g = h.get("grade") or ""
        if any(c in g for c in star_chars):
            repo_grades[repo]["star"] += 1
        if green_char in g:
            repo_grades[repo]["green"] += 1
        if orange_char in g:
            repo_grades[repo]["orange"] += 1

    lines.append("| Repo | Hypotheses | ⭐ Major | 🟩 Confirmed | 🟧 Structural | Constant Maps |")
    lines.append("|------|-----------|---------|-------------|---------------|--------------|")

    totals = {"h": 0, "star": 0, "green": 0, "orange": 0, "cm": 0}
    for repo in ["TECS-L", "SEDI", "anima"]:
        h_count = atlas["stats"].get(repo, 0)
        c_count = atlas.get("constant_stats", {}).get(repo, 0)
        rg = repo_grades.get(repo, {"star": 0, "green": 0, "orange": 0})
        star_str = str(rg["star"]) if rg["star"] else "-"
        green_str = str(rg["green"]) if rg["green"] else "-"
        orange_str = str(rg["orange"]) if rg["orange"] else "-"
        lines.append(
            f"| {repo} | {h_count:,} | {star_str} | {green_str} | {orange_str} | {c_count} |"
        )
        totals["h"] += h_count
        totals["star"] += rg["star"]
        totals["green"] += rg["green"]
        totals["orange"] += rg["orange"]
        totals["cm"] += c_count

    lines.append(
        f"| **Total** | **{totals['h']:,}** | **{totals['star']}** "
        f"| **{totals['green']}** | **{totals['orange']}** | **{totals['cm']}** |"
    )
    lines.append("")

    # ── Top Discoveries (⭐) ──
    star_hyps = []
    for h in atlas["hypotheses"]:
        g = h.get("grade") or ""
        if any(c in g for c in star_chars):
            short_id = h["id"].split(":", 1)[1] if ":" in h["id"] else h["id"]
            star_hyps.append({
                "id": short_id,
                "title": (h.get("title") or "")[:80],
                "repo": h["repo"],
            })

    if star_hyps:
        lines.append("#### Top Discoveries (\u2b50)")
        lines.append("")
        lines.append("| ID | Title | Repo |")
        lines.append("|-----|-------|------|")
        for sh in star_hyps:
            lines.append(f"| {sh['id']} | {sh['title']} | {sh['repo']} |")
        lines.append("")

    # ── Constant Maps by Category ──
    cmaps = atlas.get("constant_maps", [])
    if cmaps:
        cat_data = {}  # category -> {count, examples}
        for cm in cmaps:
            cat = cm.get("category", "other")
            if cat not in cat_data:
                cat_data[cat] = {"count": 0, "examples": []}
            cat_data[cat]["count"] += 1
            if len(cat_data[cat]["examples"]) < 3:
                cat_data[cat]["examples"].append(cm["name"])

        lines.append("#### Constant Maps by Category")
        lines.append("")
        lines.append("| Category | Count | Example Maps |")
        lines.append("|----------|-------|-------------|")
        for cat, data in sorted(cat_data.items(), key=lambda x: -x[1]["count"]):
            examples = ", ".join(data["examples"])
            if data["count"] > 3:
                examples += ", ..."
            lines.append(f"| {cat} | {data['count']} | {examples} |")
        lines.append("")

    return "\n".join(lines)


# ── CLI ──────────────────────────────────────────────────────────

def main():
    """CLI entry point for the Math Atlas scanner."""
    parser = argparse.ArgumentParser(
        description="Math Atlas — scan hypothesis files across repos",
    )
    parser.add_argument("--json", action="store_true",
                        help="Print full atlas as JSON to stdout")
    parser.add_argument("--summary", action="store_true",
                        help="Print stats (total, per-repo, grade distribution)")
    parser.add_argument("--save", action="store_true",
                        help="Save JSON, SQLite, DOT to .shared/")
    parser.add_argument("--query",
                        help="Filter: FIELD=VALUE (e.g. grade=green, domain=CX)")
    parser.add_argument("--repo", choices=["TECS-L", "SEDI", "anima"],
                        help="Filter to a single repo")
    parser.add_argument("--readme-summary", action="store_true",
                        help="Print README marker summary to stdout (used by sync script)")
    args = parser.parse_args()

    # Default: --save --summary
    if not (args.json or args.summary or args.save or args.query or args.readme_summary):
        args.save = True
        args.summary = True

    atlas = build_atlas()

    # --readme-summary (print and exit)
    if args.readme_summary:
        print(generate_readme_summary(atlas))
        return

    # --repo filter
    if args.repo:
        atlas["hypotheses"] = [
            h for h in atlas["hypotheses"] if h["repo"] == args.repo
        ]
        atlas["total"] = len(atlas["hypotheses"])

    # --json
    if args.json:
        print(json.dumps(atlas, indent=2, ensure_ascii=False))
        return

    # --save
    if args.save:
        out_dir = Path(__file__).resolve().parent
        json_path = out_dir / "math_atlas.json"
        db_path = out_dir / "math_atlas.db"
        dot_path = out_dir / "math_atlas.dot"

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(atlas, f, indent=2, ensure_ascii=False)
        print(f"  JSON: {json_path}")

        write_sqlite(atlas, str(db_path))
        print(f"  SQLite: {db_path}")

        write_dot(atlas, str(dot_path))
        print(f"  DOT: {dot_path}")

        md_path = out_dir / "MATH_ATLAS.md"
        write_markdown(atlas, str(md_path))
        print(f"  Markdown: {md_path}")

        html_path = out_dir / "math_atlas.html"
        write_html(atlas, str(html_path))
        print(f"  HTML: {html_path}")

    # --summary
    if args.summary:
        print(f"\n=== Math Atlas Summary ===")
        print(f"  Total hypotheses: {atlas['total']}")
        print(f"  Generated: {atlas.get('generated', 'N/A')}")
        print()
        print("  Per-repo:")
        for repo, count in atlas.get("stats", {}).items():
            print(f"    {repo:10s} {count:>5d}")
        print()

        # Grade distribution (group by first emoji)
        grade_dist = {}
        for h in atlas["hypotheses"]:
            g = h.get("grade") or "(none)"
            key = "(none)"
            for emoji in GRADE_EMOJIS:
                if emoji in g:
                    key = emoji
                    break
            if key == "(none)" and g != "(none)":
                key = g[:6]  # short label for non-emoji grades
            grade_dist[key] = grade_dist.get(key, 0) + 1

        print("  Grade distribution (top 10):")
        for grade, count in sorted(grade_dist.items(), key=lambda x: -x[1])[:10]:
            bar = "#" * min(count // 5, 40)
            print(f"    {grade:6s} {count:>5d}  {bar}")

        # Constant map stats
        cmaps = atlas.get("constant_maps", [])
        if cmaps:
            print(f"\n  Constant maps: {len(cmaps)}")
            cstats = atlas.get("constant_stats", {})
            for repo, count in sorted(cstats.items()):
                print(f"    {repo:10s} {count:>5d}")
            # Category distribution
            cat_dist = {}
            for cm in cmaps:
                cat = cm.get("category", "other")
                cat_dist[cat] = cat_dist.get(cat, 0) + 1
            print("  By category:")
            for cat, count in sorted(cat_dist.items(), key=lambda x: -x[1]):
                print(f"    {cat:16s} {count:>5d}")
            evaluable = sum(1 for cm in cmaps if cm.get("evaluable"))
            print(f"  Evaluable: {evaluable}/{len(cmaps)}")

    # --query FIELD=VALUE
    if args.query:
        if "=" not in args.query:
            print(f"Error: --query must be FIELD=VALUE (e.g. domain=CX)", file=sys.stderr)
            sys.exit(1)
        field, value = args.query.split("=", 1)
        matches = []
        for h in atlas["hypotheses"]:
            hval = str(h.get(field, ""))
            if value.lower() in hval.lower():
                matches.append(h)
        print(f"\n  Query: {field}={value} ({len(matches)} matches)")
        for h in matches[:30]:
            g = h.get("grade") or "-"
            print(f"    {g:4s} {h['id']:30s} {(h.get('title') or '')[:50]}")
        if len(matches) > 30:
            print(f"    ... and {len(matches) - 30} more")


if __name__ == "__main__":
    main()
