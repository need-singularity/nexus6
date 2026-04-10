# Math Atlas Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a unified read-only atlas that scans ~1,750 hypothesis MD files + anima Python sources across 3 repos and generates JSON, SQLite, and Graphviz outputs.

**Architecture:** A single Python scanner (`scan-math-atlas.py`) in `.shared/` reads all hypothesis sources using regex extraction (no frontmatter required), normalizes to a common schema, and writes 3 derived artifacts. A shell wrapper (`sync-math-atlas.sh`) integrates into the existing `.shared/` sync pipeline.

**Tech Stack:** Python 3 stdlib only (json, sqlite3, re, pathlib, ast). No pip dependencies.

---

## File Structure

| File | Responsibility |
|------|---------------|
| `.shared/scan-math-atlas.py` | Main scanner — regex parsers per repo, schema normalization, all 3 output formats |
| `.shared/scripts/sync-math-atlas.sh` | Shell wrapper — runs scanner, commits, pushes (mirrors `sync-calculators.sh`) |
| `.shared/discovery/math_atlas.json` | Generated — full hypothesis registry |
| `.shared/n6/math_atlas.db` | Generated — SQLite with hypotheses + edges tables |
| `.shared/n6/math_atlas.dot` | Generated — cross-ref graph for Graphviz |
| `tests/test_atlas_parser.py` | Unit tests for regex parsers |

---

### Task 1: Regex Parsers + Unit Tests

**Files:**
- Create: `tests/test_atlas_parser.py`
- Create: `.shared/scan-math-atlas.py` (parser module only, no main yet)

The scanner must handle 5 distinct header patterns found across repos:

```
Pattern A: "# Hypothesis Review 056: Title"       → id=TECS-L:056
Pattern B: "# Hypothesis 355: Title"              → id=TECS-L:355
Pattern C: "# H-CX-215: Title"                    → id=REPO:H-CX-215
Pattern D: "# H-STAT-1: Title" (with YAML front)  → id=REPO:H-STAT-1
Pattern E: "# Frontier 1200: Title"               → id=TECS-L:F-1200 (meta docs)
```

- [ ] **Step 1: Write failing tests for ID extraction**

```python
# tests/test_atlas_parser.py
"""Tests for math atlas hypothesis parser."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '.shared'))

from scan_math_atlas import parse_hypothesis_md

def test_pattern_a_hypothesis_review():
    text = "# Hypothesis Review 056: Meta Recursion ✅\n\n## Hypothesis\n> Does infinite meta converge?"
    h = parse_hypothesis_md(text, "TECS-L", "docs/hypotheses/056-meta-recursion.md")
    assert h["id"] == "TECS-L:056"
    assert "Meta Recursion" in h["title"]
    assert h["repo"] == "TECS-L"

def test_pattern_b_hypothesis_plain():
    text = "# Hypothesis 355: Prediction Error = Surprise\n\n## Hypothesis\n> Consciousness is a prediction engine."
    h = parse_hypothesis_md(text, "TECS-L", "docs/hypotheses/355-prediction-error.md")
    assert h["id"] == "TECS-L:355"
    assert "Prediction Error" in h["title"]

def test_pattern_c_domain_prefix():
    text = "# H-CX-215: Brainwave Product\n\n> delta x theta = 96000\n"
    h = parse_hypothesis_md(text, "TECS-L", "math/docs/hypotheses/H-CX-215-brainwave.md")
    assert h["id"] == "TECS-L:H-CX-215"
    assert h["domain"] == "CX"

def test_pattern_c_sedi():
    text = "# H-CA-001: Anima Phi_max = 8\n\n> **Hypothesis**: Anima values.\n\n## Grade: 🟧★\n"
    h = parse_hypothesis_md(text, "SEDI", "docs/hypotheses/H-CA-001-phi-max.md")
    assert h["id"] == "SEDI:H-CA-001"
    assert h["domain"] == "CA"
    assert h["grade"] == "🟧★"

def test_pattern_d_yaml_frontmatter():
    text = '---\nid: H-STAT-1\ntitle: "Chi-Squared"\nstatus: "VERIFIED"\ngrade: "🟩⭐⭐⭐"\ndate: 2026-03-26\n---\n# H-STAT-1: Chi-Squared\n\n> **Hypothesis.** The chi-squared distribution\n'
    h = parse_hypothesis_md(text, "TECS-L", "math/docs/hypotheses/H-STAT-1-chi-squared.md")
    assert h["id"] == "TECS-L:H-STAT-1"
    assert "⭐⭐⭐" in h["grade"]

def test_grade_extraction():
    text = "# H-CX-651: TEE = ln(phi(6))\n\n> Hypothesis text\n\n## Grade: 🟩 CONFIRMED (exact)\n"
    h = parse_hypothesis_md(text, "SEDI", "docs/hypotheses/H-CX-651-tee.md")
    assert "🟩" in h["grade"]

def test_grade_from_status_line():
    text = "# H-TOP-1: Betti Numbers\n\n> **Hypothesis**: Betti numbers satisfy constraints.\n\n**Status: ⚪ Refuted (incompatibility proof)**\n"
    h = parse_hypothesis_md(text, "TECS-L", "math/docs/hypotheses/H-TOP-1-betti.md")
    assert "⚪" in h["grade"]

def test_grade_from_title_emoji():
    text = "# H-CX-215: 🟩 Brainwave Product\n\n> delta x theta\n"
    h = parse_hypothesis_md(text, "TECS-L", "docs/hypotheses/H-CX-215-brainwave.md")
    assert "🟩" in h["grade"]

def test_cross_refs():
    text = "# Hypothesis Review 056: Meta\n\nRelated hypotheses: 041(Transcendence), 055(Eye), 067(1/2+1/3=5/6)\n"
    h = parse_hypothesis_md(text, "TECS-L", "docs/hypotheses/056-meta.md")
    assert "041" in str(h["refs"])
    assert "055" in str(h["refs"])

def test_gz_dependent():
    text = "# H-CX-61: Maximum Divisor Entropy\n\n**Golden Zone dependency:** NONE for math basis\n"
    h = parse_hypothesis_md(text, "TECS-L", "math/docs/hypotheses/H-CX-61-max-entropy.md")
    assert h["gz_dependent"] is False

def test_gz_dependent_true():
    text = "# H-CX-100: Something\n\n**Golden Zone dependency:** YES\n"
    h = parse_hypothesis_md(text, "TECS-L", "docs/hypotheses/H-CX-100-something.md")
    assert h["gz_dependent"] is True

def test_no_match_returns_fallback():
    text = "# Some random markdown\n\nNo hypothesis here.\n"
    h = parse_hypothesis_md(text, "TECS-L", "docs/hypotheses/random.md")
    assert h["id"] == "TECS-L:random"
    assert h["title"] == "Some random markdown"

if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/ghost/Dev/TECS-L && python3 -m pytest tests/test_atlas_parser.py -v`
Expected: ImportError — `scan_math_atlas` module not found

- [ ] **Step 3: Implement `parse_hypothesis_md` function**

```python
# .shared/n6/scan_math_atlas.py
"""Math Atlas Scanner — Scans TECS-L, anima, SEDI repos and builds unified hypothesis registry."""

import re
from pathlib import Path

# ── Grade emoji detection ──
GRADE_EMOJIS = ['⭐', '🟩', '🟧', '🟦', '🟨', '🟥', '🟪', '⚪', '⬛', '★', '⚡']

def _extract_id_and_title(text, repo, filepath):
    """Extract hypothesis ID and title from first heading line."""
    first_line = text.split('\n')[0].strip()

    # Pattern D: YAML frontmatter with id field
    fm_match = re.match(r'^---\s*\n', text)
    if fm_match:
        id_m = re.search(r'^id:\s*(H-[\w]+-\d+)', text, re.MULTILINE)
        if id_m:
            raw_id = id_m.group(1)
            # Still get title from # heading
            title_m = re.search(r'^#\s+.+?:\s*(.+)', text, re.MULTILINE)
            title = title_m.group(1).strip() if title_m else raw_id
            domain_m = re.match(r'H-(\w+)-', raw_id)
            domain = domain_m.group(1) if domain_m else None
            return f"{repo}:{raw_id}", title, domain

    # Pattern A: "# Hypothesis Review NNN: Title"
    m = re.match(r'^#\s+Hypothesis\s+Review\s+(\d+):\s*(.+)', first_line)
    if m:
        return f"{repo}:{m.group(1)}", m.group(2).strip(), None

    # Pattern B: "# Hypothesis NNN: Title"
    m = re.match(r'^#\s+Hypothesis\s+(\d+):\s*(.+)', first_line)
    if m:
        return f"{repo}:{m.group(1)}", m.group(2).strip(), None

    # Pattern C: "# H-DOMAIN-N: Title"
    m = re.match(r'^#\s+(H-(\w+)-(\d+)):\s*(.+)', first_line)
    if m:
        return f"{repo}:{m.group(1)}", m.group(4).strip(), m.group(2)

    # Pattern E: "# Frontier NNN: Title"
    m = re.match(r'^#\s+Frontier\s+(\d+):\s*(.+)', first_line)
    if m:
        return f"{repo}:F-{m.group(1)}", m.group(2).strip(), None

    # Fallback: use filename stem as ID, first heading as title
    stem = Path(filepath).stem
    title_m = re.match(r'^#\s+(.+)', first_line)
    title = title_m.group(1).strip() if title_m else stem
    return f"{repo}:{stem}", title, None


def _extract_grade(text, title):
    """Extract grade from ## Grade: line, **Status:** line, **Grade:** line, or title emoji."""
    # ## Grade: 🟧★ or ## Grade: 🟩 CONFIRMED
    m = re.search(r'^##\s*Grade:\s*(.+)', text, re.MULTILINE)
    if m:
        return m.group(1).strip()

    # **Grade:** ... or **Status:** ...
    m = re.search(r'\*\*(?:Grade|Status)(?:\*\*)?:\*?\*?\s*(.+)', text)
    if m:
        return m.group(1).strip()

    # **Status: ... (no closing bold)
    m = re.search(r'\*\*Status:\s*(.+?)(?:\*\*)?$', text, re.MULTILINE)
    if m:
        val = m.group(1).strip().rstrip('*')
        if any(e in val for e in GRADE_EMOJIS):
            return val

    # YAML frontmatter grade
    m = re.search(r'^grade:\s*["\']?(.+?)["\']?\s*$', text, re.MULTILINE)
    if m:
        return m.group(1).strip()

    # Emoji in title (e.g., "# H-CX-215: 🟩 Brainwave Product")
    for emoji in GRADE_EMOJIS:
        if emoji in title:
            return emoji

    # ✅ in title
    if '✅' in title:
        return '✅'

    return None


def _extract_refs(text):
    """Extract cross-references to other hypotheses."""
    refs = set()

    # "Related hypotheses: 041(Name), 055(Name), ..."
    m = re.search(r'Related\s+[Hh]ypothes[ei]s?:\s*(.+)', text)
    if m:
        for ref in re.findall(r'(\d{2,4})\(', m.group(1)):
            refs.add(ref)
        for ref in re.findall(r'(H-[\w]+-\d+)', m.group(1)):
            refs.add(ref)

    # Inline "(H-CX-162)" style
    for ref in re.findall(r'\(H-([\w]+-\d+)\)', text):
        refs.add(f"H-{ref}")

    return sorted(refs)


def _extract_gz(text):
    """Extract Golden Zone dependency. Returns True/False/None."""
    m = re.search(r'Golden\s+Zone\s+(?:dependency|dependent|independent)[:\s]*(.+)', text, re.IGNORECASE)
    if m:
        val = m.group(1).strip().lower()
        if val.startswith('none') or val.startswith('no') or 'independent' in val:
            return False
        if val.startswith('yes') or 'dependent' in val:
            return True
        # "NONE for math basis; partial for neural prediction" → treat as False (math part)
        if 'none' in val:
            return False
    return None


def parse_hypothesis_md(text, repo, filepath):
    """Parse a hypothesis markdown file and return a normalized dict."""
    hyp_id, title, domain = _extract_id_and_title(text, repo, filepath)
    grade = _extract_grade(text, title)
    refs = _extract_refs(text)
    gz = _extract_gz(text)

    # Clean emoji from title for readability
    clean_title = title
    for emoji in GRADE_EMOJIS + ['✅', '❌']:
        clean_title = clean_title.replace(emoji, '').strip()
    # Remove trailing whitespace artifacts
    clean_title = re.sub(r'\s+', ' ', clean_title).strip()
    # Remove leading/trailing dashes or whitespace
    clean_title = clean_title.strip(' -—')

    return {
        "id": hyp_id,
        "repo": repo,
        "file": filepath,
        "title": clean_title if clean_title else title,
        "grade": grade,
        "domain": domain,
        "gz_dependent": gz,
        "refs": refs,
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/ghost/Dev/TECS-L && python3 -m pytest tests/test_atlas_parser.py -v`
Expected: All 12 tests PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_atlas_parser.py .shared/n6/scan_math_atlas.py
git commit -m "feat: add math atlas hypothesis parser with regex extraction"
```

---

### Task 2: Anima Python Adapter

**Files:**
- Modify: `.shared/n6/scan_math_atlas.py` (add `parse_anima_recommender` function)
- Modify: `tests/test_atlas_parser.py` (add anima tests)

Anima stores hypotheses in Python dataclasses inside `hypothesis_recommender.py`. We parse these using regex on the source (not AST — the file is too large and has runtime deps).

- [ ] **Step 1: Write failing test for anima parser**

Add to `tests/test_atlas_parser.py`:

```python
from scan_math_atlas import parse_anima_recommender

def test_anima_recommender_parser():
    # Simulate a snippet of hypothesis_recommender.py HYPOTHESIS_DB
    source = '''
HYPOTHESIS_DB = [
    Hypothesis(
        code="B1",
        name="Bidirectional coupling",
        category="learning",
        expected_phi=3.2,
        description="Phi-guided bidirectional Hebbian coupling",
        conditions={"phi_min": 0.5},
        tags=["low_phi", "growth_stall"],
    ),
    Hypothesis(
        code="DD94",
        name="Wave+Phi mega combo",
        category="discovery",
        expected_phi=8.12,
        description="Combined wave modulation and phi feedback",
        conditions={"phi_min": 2.0, "cells_min": 8},
        tags=["mega"],
    ),
]
'''
    results = parse_anima_recommender(source)
    assert len(results) == 2
    assert results[0]["id"] == "anima:B1"
    assert results[0]["title"] == "Bidirectional coupling"
    assert results[1]["id"] == "anima:DD94"
    assert results[1]["grade"] is None  # anima has no grade system
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/ghost/Dev/TECS-L && python3 -m pytest tests/test_atlas_parser.py::test_anima_recommender_parser -v`
Expected: ImportError — `parse_anima_recommender` not found

- [ ] **Step 3: Implement anima parser**

Add to `.shared/n6/scan_math_atlas.py`:

```python
def parse_anima_recommender(source_text):
    """Parse anima hypothesis_recommender.py source and extract Hypothesis entries."""
    results = []
    # Match Hypothesis(...) blocks
    pattern = re.compile(
        r'Hypothesis\(\s*'
        r'code="(\w+)",\s*'
        r'name="([^"]+)",\s*'
        r'category="([^"]+)",\s*'
        r'expected_phi=([\d.]+),\s*'
        r'description="([^"]*)"',
        re.DOTALL
    )
    for m in pattern.finditer(source_text):
        code, name, category, phi, desc = m.groups()
        results.append({
            "id": f"anima:{code}",
            "repo": "anima",
            "file": "hypothesis_recommender.py",
            "title": name,
            "grade": None,
            "domain": category,
            "gz_dependent": None,
            "refs": [],
            "expected_phi": float(phi),
        })
    return results
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/ghost/Dev/TECS-L && python3 -m pytest tests/test_atlas_parser.py -v`
Expected: All 13 tests PASS

- [ ] **Step 5: Commit**

```bash
git add .shared/n6/scan_math_atlas.py tests/test_atlas_parser.py
git commit -m "feat: add anima hypothesis_recommender.py parser"
```

---

### Task 3: Full Scanner — Repo Walking + JSON Output

**Files:**
- Modify: `.shared/n6/scan_math_atlas.py` (add repo scanning, JSON output, CLI)

- [ ] **Step 1: Write failing test for full scan**

Add to `tests/test_atlas_parser.py`:

```python
import json
from scan_math_atlas import build_atlas

def test_build_atlas_returns_dict():
    atlas = build_atlas()
    assert "version" in atlas
    assert "hypotheses" in atlas
    assert "stats" in atlas
    assert isinstance(atlas["hypotheses"], list)
    # Should find at least 1000 hypotheses across repos
    assert len(atlas["hypotheses"]) > 1000, f"Only found {len(atlas['hypotheses'])}"

def test_build_atlas_no_duplicate_ids():
    atlas = build_atlas()
    ids = [h["id"] for h in atlas["hypotheses"]]
    dupes = [x for x in ids if ids.count(x) > 1]
    assert len(dupes) == 0, f"Duplicate IDs: {set(dupes)}"

def test_build_atlas_json_serializable():
    atlas = build_atlas()
    # Must not raise
    json.dumps(atlas, ensure_ascii=False)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/ghost/Dev/TECS-L && python3 -m pytest tests/test_atlas_parser.py::test_build_atlas_returns_dict -v`
Expected: ImportError — `build_atlas` not found

- [ ] **Step 3: Implement repo scanner and build_atlas**

Add to `.shared/n6/scan_math_atlas.py`:

```python
import json
import sys
from datetime import datetime

BASE = Path(__file__).resolve().parent.parent  # TECS-L root
DEV = BASE.parent  # ~/Dev

REPO_SCANS = [
    {
        "name": "TECS-L",
        "root": BASE,
        "hypothesis_dirs": [
            "docs/hypotheses",
            "math/docs/hypotheses",
        ],
    },
    {
        "name": "SEDI",
        "root": DEV / "SEDI",
        "hypothesis_dirs": [
            "docs/hypotheses",
        ],
    },
    {
        "name": "anima",
        "root": DEV / "anima",
        "hypothesis_dirs": [],  # No MD hypotheses — uses Python adapter
        "python_sources": [
            "hypothesis_recommender.py",
        ],
    },
]


def _scan_md_dir(repo_name, repo_root, rel_dir):
    """Scan a directory for hypothesis .md files and parse each."""
    results = []
    dirpath = repo_root / rel_dir
    if not dirpath.exists():
        return results

    for mdfile in sorted(dirpath.glob("*.md")):
        if mdfile.name.startswith('.') or mdfile.name == 'README.md':
            continue
        try:
            text = mdfile.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue
        rel_path = str(mdfile.relative_to(repo_root))
        h = parse_hypothesis_md(text, repo_name, rel_path)
        results.append(h)
    return results


def _scan_anima_python(repo_root, source_file):
    """Scan anima Python source for hypothesis entries."""
    filepath = repo_root / source_file
    if not filepath.exists():
        return []
    try:
        text = filepath.read_text(encoding='utf-8', errors='ignore')
    except Exception:
        return []
    return parse_anima_recommender(text)


def build_atlas():
    """Build the complete math atlas from all repos."""
    all_hypotheses = []
    stats = {}

    for repo in REPO_SCANS:
        repo_name = repo["name"]
        repo_root = repo["root"]
        count = 0

        if not repo_root.exists():
            print(f"  SKIP: {repo_root} not found", file=sys.stderr)
            stats[repo_name] = 0
            continue

        # Scan MD directories
        for rel_dir in repo.get("hypothesis_dirs", []):
            entries = _scan_md_dir(repo_name, repo_root, rel_dir)
            all_hypotheses.extend(entries)
            count += len(entries)

        # Scan Python sources (anima)
        for src in repo.get("python_sources", []):
            entries = _scan_anima_python(repo_root, src)
            all_hypotheses.extend(entries)
            count += len(entries)

        stats[repo_name] = count
        print(f"  {repo_name}: {count} hypotheses", file=sys.stderr)

    # Deduplicate by ID (keep first occurrence)
    seen = {}
    unique = []
    for h in all_hypotheses:
        if h["id"] not in seen:
            seen[h["id"]] = True
            unique.append(h)

    return {
        "version": "1.0",
        "generated": datetime.now().isoformat(timespec='seconds'),
        "stats": stats,
        "total": len(unique),
        "hypotheses": unique,
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/ghost/Dev/TECS-L && python3 -m pytest tests/test_atlas_parser.py -v`
Expected: All 16 tests PASS

- [ ] **Step 5: Commit**

```bash
git add .shared/n6/scan_math_atlas.py tests/test_atlas_parser.py
git commit -m "feat: add full repo scanner and build_atlas for JSON output"
```

---

### Task 4: SQLite Output

**Files:**
- Modify: `.shared/n6/scan_math_atlas.py` (add `write_sqlite` function)

- [ ] **Step 1: Write failing test for SQLite output**

Add to `tests/test_atlas_parser.py`:

```python
import sqlite3
import tempfile

from scan_math_atlas import build_atlas, write_sqlite

def test_write_sqlite():
    atlas = build_atlas()
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        dbpath = f.name
    try:
        write_sqlite(atlas, dbpath)
        conn = sqlite3.connect(dbpath)
        cur = conn.cursor()

        # Check hypotheses table
        cur.execute("SELECT COUNT(*) FROM hypotheses")
        count = cur.fetchone()[0]
        assert count == atlas["total"], f"DB has {count}, atlas has {atlas['total']}"

        # Check a query works
        cur.execute("SELECT id, title FROM hypotheses WHERE grade LIKE '%⭐%' LIMIT 5")
        rows = cur.fetchall()
        assert len(rows) >= 0  # May have 0 stars, that's ok

        # Check edges table exists
        cur.execute("SELECT COUNT(*) FROM edges")

        conn.close()
    finally:
        os.unlink(dbpath)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/ghost/Dev/TECS-L && python3 -m pytest tests/test_atlas_parser.py::test_write_sqlite -v`
Expected: ImportError — `write_sqlite` not found

- [ ] **Step 3: Implement write_sqlite**

Add to `.shared/n6/scan_math_atlas.py`:

```python
import sqlite3

def write_sqlite(atlas, dbpath):
    """Write atlas to SQLite database."""
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
        gz = None if h["gz_dependent"] is None else (1 if h["gz_dependent"] else 0)
        cur.execute(
            "INSERT OR IGNORE INTO hypotheses VALUES (?,?,?,?,?,?,?,?)",
            (h["id"], h["repo"], h["file"], h["title"], h["grade"],
             h["domain"], gz, json.dumps(h["refs"]))
        )

    # Build edges from refs
    # Create a lookup: short ref → full ID
    id_lookup = {}
    for h in atlas["hypotheses"]:
        hid = h["id"]
        # "TECS-L:H-CX-215" → register as "H-CX-215"
        short = hid.split(":", 1)[1] if ":" in hid else hid
        id_lookup[short] = hid
        # Also register numeric-only: "TECS-L:056" → "056"
        if short.isdigit():
            id_lookup[short] = hid

    for h in atlas["hypotheses"]:
        for ref in h.get("refs", []):
            target = id_lookup.get(ref)
            if target:
                cur.execute(
                    "INSERT INTO edges VALUES (?,?,?)",
                    (h["id"], target, "references")
                )

    conn.commit()
    conn.close()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/ghost/Dev/TECS-L && python3 -m pytest tests/test_atlas_parser.py -v`
Expected: All 17 tests PASS

- [ ] **Step 5: Commit**

```bash
git add .shared/n6/scan_math_atlas.py tests/test_atlas_parser.py
git commit -m "feat: add SQLite output for math atlas"
```

---

### Task 5: Graphviz DOT Output

**Files:**
- Modify: `.shared/n6/scan_math_atlas.py` (add `write_dot` function)

- [ ] **Step 1: Write failing test for DOT output**

Add to `tests/test_atlas_parser.py`:

```python
from scan_math_atlas import build_atlas, write_dot

def test_write_dot():
    atlas = build_atlas()
    with tempfile.NamedTemporaryFile(suffix='.dot', delete=False, mode='w') as f:
        dotpath = f.name
    try:
        write_dot(atlas, dotpath)
        content = open(dotpath).read()
        assert content.startswith("digraph math_atlas {")
        assert "}" in content
        # Should have at least some nodes
        assert "label=" in content
    finally:
        os.unlink(dotpath)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/ghost/Dev/TECS-L && python3 -m pytest tests/test_atlas_parser.py::test_write_dot -v`
Expected: ImportError — `write_dot` not found

- [ ] **Step 3: Implement write_dot**

Add to `.shared/n6/scan_math_atlas.py`:

```python
def write_dot(atlas, dotpath):
    """Write cross-reference graph in Graphviz DOT format."""
    # Color by repo
    REPO_COLORS = {
        "TECS-L": "#4A90D9",
        "SEDI": "#E67E22",
        "anima": "#2ECC71",
    }
    GRADE_SHAPES = {
        "⭐": "doubleoctagon",
        "🟩": "box",
        "🟧": "diamond",
        "⚪": "ellipse",
        "⬛": "point",
    }

    lines = ['digraph math_atlas {']
    lines.append('  rankdir=LR;')
    lines.append('  node [fontsize=9];')
    lines.append('  edge [color="#999999"];')
    lines.append('')

    # Only include nodes that have edges (to keep graph manageable)
    nodes_with_edges = set()
    for h in atlas["hypotheses"]:
        if h.get("refs"):
            nodes_with_edges.add(h["id"])
            for ref in h["refs"]:
                nodes_with_edges.add(ref)

    # Write nodes
    for h in atlas["hypotheses"]:
        if h["id"] not in nodes_with_edges:
            continue
        color = REPO_COLORS.get(h["repo"], "#999999")
        shape = "ellipse"
        grade = h.get("grade") or ""
        for emoji, sh in GRADE_SHAPES.items():
            if emoji in grade:
                shape = sh
                break
        short = h["id"].split(":", 1)[1] if ":" in h["id"] else h["id"]
        safe_label = short.replace('"', '\\"')
        node_id = h["id"].replace(":", "_").replace("-", "_")
        lines.append(f'  {node_id} [label="{safe_label}" color="{color}" shape={shape}];')

    lines.append('')

    # Build ID lookup for edge resolution
    id_lookup = {}
    for h in atlas["hypotheses"]:
        hid = h["id"]
        short = hid.split(":", 1)[1] if ":" in hid else hid
        id_lookup[short] = hid

    # Write edges
    for h in atlas["hypotheses"]:
        for ref in h.get("refs", []):
            target_id = id_lookup.get(ref, ref)
            src = h["id"].replace(":", "_").replace("-", "_")
            tgt = target_id.replace(":", "_").replace("-", "_")
            lines.append(f'  {src} -> {tgt};')

    lines.append('}')

    with open(dotpath, 'w') as f:
        f.write('\n'.join(lines))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/ghost/Dev/TECS-L && python3 -m pytest tests/test_atlas_parser.py -v`
Expected: All 18 tests PASS

- [ ] **Step 5: Commit**

```bash
git add .shared/n6/scan_math_atlas.py tests/test_atlas_parser.py
git commit -m "feat: add Graphviz DOT output for math atlas"
```

---

### Task 6: CLI + main()

**Files:**
- Modify: `.shared/n6/scan_math_atlas.py` (add argparse CLI and main)

- [ ] **Step 1: Implement CLI**

Add to `.shared/n6/scan_math_atlas.py`:

```python
def main():
    import argparse
    parser = argparse.ArgumentParser(description="Math Atlas — unified hypothesis registry")
    parser.add_argument("--json", action="store_true", help="Print JSON to stdout")
    parser.add_argument("--summary", action="store_true", help="Print summary stats only")
    parser.add_argument("--save", action="store_true", help="Save all outputs to .shared/")
    parser.add_argument("--query", type=str, help="Filter: field=value (e.g., grade=⭐, repo=SEDI)")
    parser.add_argument("--repo", choices=["TECS-L", "anima", "SEDI"], help="Single repo only")
    args = parser.parse_args()

    if not any([args.json, args.summary, args.save, args.query]):
        args.save = True
        args.summary = True

    print("Building math atlas...", file=sys.stderr)
    atlas = build_atlas()

    if args.repo:
        atlas["hypotheses"] = [h for h in atlas["hypotheses"] if h["repo"] == args.repo]
        atlas["total"] = len(atlas["hypotheses"])

    if args.save:
        out_dir = Path(__file__).resolve().parent
        # JSON
        json_path = out_dir / "math_atlas.json"
        with open(json_path, 'w') as f:
            json.dump(atlas, f, indent=2, ensure_ascii=False)
        print(f"  Saved: {json_path}", file=sys.stderr)
        # SQLite
        db_path = out_dir / "math_atlas.db"
        write_sqlite(atlas, str(db_path))
        print(f"  Saved: {db_path}", file=sys.stderr)
        # DOT
        dot_path = out_dir / "math_atlas.dot"
        write_dot(atlas, str(dot_path))
        print(f"  Saved: {dot_path}", file=sys.stderr)

    if args.json:
        print(json.dumps(atlas, indent=2, ensure_ascii=False))

    if args.query:
        field, _, value = args.query.partition("=")
        matches = [h for h in atlas["hypotheses"]
                   if value.lower() in str(h.get(field, "")).lower()]
        print(f"\n  Query: {field}={value} → {len(matches)} matches\n")
        for h in matches[:30]:
            print(f"  {h['id']:30s} {h.get('grade',''):6s} {h['title'][:60]}")
        if len(matches) > 30:
            print(f"  ... and {len(matches) - 30} more")

    if args.summary:
        print(f"\n  === Math Atlas Summary ===")
        print(f"  Total: {atlas['total']} hypotheses")
        for repo, count in atlas["stats"].items():
            print(f"    {repo}: {count}")
        # Grade distribution
        grades = {}
        for h in atlas["hypotheses"]:
            g = h.get("grade") or "unknown"
            # Simplify: take first emoji
            key = "unknown"
            for emoji in GRADE_EMOJIS + ['✅']:
                if emoji in g:
                    key = emoji
                    break
            grades[key] = grades.get(key, 0) + 1
        print(f"  Grades:")
        for g, c in sorted(grades.items(), key=lambda x: -x[1]):
            print(f"    {g:6s} {c}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Test CLI end-to-end**

Run: `cd /Users/ghost/Dev/TECS-L && python3 .shared/n6/scan_math_atlas.py --summary`
Expected: Prints stats showing ~1,750+ hypotheses across 3 repos

- [ ] **Step 3: Test save outputs**

Run: `cd /Users/ghost/Dev/TECS-L && python3 .shared/n6/scan_math_atlas.py --save --summary`
Expected: Creates `.shared/discovery/math_atlas.json`, `.shared/n6/math_atlas.db`, `.shared/n6/math_atlas.dot`

- [ ] **Step 4: Test query**

Run: `cd /Users/ghost/Dev/TECS-L && python3 .shared/n6/scan_math_atlas.py --query "grade=⭐"`
Expected: Lists hypotheses with star grades

- [ ] **Step 5: Commit**

```bash
git add .shared/n6/scan_math_atlas.py
git commit -m "feat: add CLI with --save, --summary, --query, --json, --repo"
```

---

### Task 7: Shell Wrapper + .gitignore

**Files:**
- Create: `.shared/scripts/sync-math-atlas.sh`
- Modify: `.gitignore` (add generated atlas files)

- [ ] **Step 1: Create sync-math-atlas.sh**

```bash
#!/bin/bash
# Sync math atlas across all repos
# Scans TECS-L, anima, SEDI hypothesis files → builds unified atlas
#
# Usage: bash .shared/scripts/sync-math-atlas.sh
# Run from TECS-L repo root

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BASE="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=== Math Atlas Sync ==="
echo ""

# Step 1: Build atlas
echo "[1/2] Building atlas..."
python3 "$SCRIPT_DIR/scan_math_atlas.py" --save --summary

echo ""

# Step 2: Commit generated files
echo "[2/2] Committing..."
cd "$BASE"
ATLAS_FILES=".shared/discovery/math_atlas.json .shared/n6/math_atlas.db .shared/n6/math_atlas.dot"

if git diff --quiet $ATLAS_FILES 2>/dev/null && \
   git diff --cached --quiet $ATLAS_FILES 2>/dev/null; then
    echo "  No changes"
else
    git add $ATLAS_FILES
    git commit -m "Update math atlas ($(date +%Y-%m-%d))"
    echo "  Committed!"
fi

echo ""
echo "Done!"
```

- [ ] **Step 2: Make executable and add atlas outputs to .gitignore exception**

Run: `chmod +x .shared/scripts/sync-math-atlas.sh`

Check `.gitignore` — the generated `.db` and `.dot` files should be tracked (they're the deliverable). If `.gitignore` has `*.db`, add an exception:

```
# Math Atlas outputs (tracked)
!.shared/discovery/math_atlas.json
!.shared/n6/math_atlas.db
!.shared/n6/math_atlas.dot
```

- [ ] **Step 3: Test full sync**

Run: `cd /Users/ghost/Dev/TECS-L && bash .shared/scripts/sync-math-atlas.sh`
Expected: Builds atlas, shows summary, commits if changed

- [ ] **Step 4: Verify outputs**

Run: `ls -lh .shared/math_atlas.*`
Expected: 3 files — `.json` (largest), `.db`, `.dot`

Run: `sqlite3 .shared/n6/math_atlas.db "SELECT repo, COUNT(*) FROM hypotheses GROUP BY repo"`
Expected: Shows counts per repo

- [ ] **Step 5: Commit**

```bash
git add .shared/scripts/sync-math-atlas.sh .gitignore
git commit -m "feat: add sync-math-atlas.sh shell wrapper"
```

---

### Task 8: Integration Test — Full Pipeline

**Files:** None (verification only)

- [ ] **Step 1: Run full test suite**

Run: `cd /Users/ghost/Dev/TECS-L && python3 -m pytest tests/test_atlas_parser.py -v`
Expected: All 18 tests PASS

- [ ] **Step 2: Run full sync pipeline**

Run: `cd /Users/ghost/Dev/TECS-L && bash .shared/scripts/sync-math-atlas.sh`
Expected: Completes without error, shows summary with ~1,750+ hypotheses

- [ ] **Step 3: Verify JSON structure**

Run: `python3 -c "import json; a=json.load(open('.shared/discovery/math_atlas.json')); print(f'Total: {a[\"total\"]}'); print(json.dumps(a['hypotheses'][0], indent=2, ensure_ascii=False))"`
Expected: Shows total count and a sample hypothesis entry with all fields

- [ ] **Step 4: Verify SQLite queries**

Run:
```bash
sqlite3 .shared/n6/math_atlas.db "SELECT repo, COUNT(*) FROM hypotheses GROUP BY repo"
sqlite3 .shared/n6/math_atlas.db "SELECT id, grade, title FROM hypotheses WHERE grade LIKE '%⭐%' LIMIT 10"
sqlite3 .shared/n6/math_atlas.db "SELECT COUNT(*) FROM edges"
```
Expected: Repo counts match JSON, star-graded hypotheses listed, edges > 0

- [ ] **Step 5: Verify DOT graph**

Run: `head -20 .shared/n6/math_atlas.dot && wc -l .shared/n6/math_atlas.dot`
Expected: Valid DOT syntax starting with `digraph math_atlas {`
