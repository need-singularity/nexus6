#!/usr/bin/env python3
"""H-NEXUSPATH safe fixer — $HOME/Dev/<proj> → $<PROJ> with fallback.

Transformations by file type:
  .sh : $HOME/Dev/<p> → ${<P>:-$HOME/Dev/<p>}
         ${HOME}/Dev/<p> → ${<P>:-$HOME/Dev/<p>}
         /Users/<u>/Dev/<p> → ${<P>:-$HOME/Dev/<p>} (literal user)
         ~/Dev/<p> → ${<P>:-$HOME/Dev/<p>}
  .hexa: env("HOME") + "/Dev/<p>" → env("<P>")  (+ canonical @allow-devpath fallback kept)
         "$HOME/Dev/<p>" literal → "$<P>"
  .md/.json/.jsonl: $HOME/Dev/<p> → $<P>
                    ~/Dev/<p> → $<P>
                    /Users/<u>/Dev/<p> → $<P>

Exclusions:
  - .git/, archive/, _archive/, node_modules/
  - .claude*/, .growth*/, .runtime/, .worktrees/
  - Log jsonl basenames (lint_log, mistakes, observations, etc.)
  - Lines with @allow-devpath token
  - Canonical fallback patterns already using ${PROJ:-...}

Modes: dry-run (default) | apply (--apply)
"""
import re, pathlib, sys, os

PROJ_MAP = {
    "nexus": "NEXUS",
    "anima": "ANIMA",
    "hexa-lang": "HEXA_LANG",
    "n6-architecture": "N6_ARCH",
    "airgenome": "AIRGENOME",
    "void": "VOID",
    "papers": "PAPERS",
}

EXCLUDE_DIRS = {".git", "archive", "_archive", "node_modules"}
EXCLUDE_DIR_PREFIXES = (".claude", ".growth", ".runtime", ".worktrees")
EXCLUDE_LOG_BASENAMES = {
    "mistakes.jsonl", "lint_log.jsonl", "gc_log.jsonl",
    "rules_usage.jsonl", "autofix_proposals.jsonl", "cleanup_log.jsonl",
    "lockdown_log.jsonl", "errors.jsonl", "sync_log.jsonl",
    "hexa_pitfalls_log.jsonl", "porting_log.jsonl",
    "topology_mk2.jsonl", "pitfalls.jsonl",
    "work_registry.jsonl", "genomes.index.jsonl",
    "observations.jsonl", "sandbox_breaches.jsonl",
}
EXT_ALLOW = {".sh", ".hexa", ".md", ".json"}  # .jsonl excluded — too many append-only logs

# Regex alternations for <proj> (literal match — no word boundaries inside path)
PROJ_ALT = "(" + "|".join(re.escape(k) for k in PROJ_MAP.keys()) + ")"

# User home prefix alternations
HOME_ALT = r"(?:\$HOME|\$\{HOME\}|\$HOME_DIR|\$\{HOME_DIR\}|/Users/[A-Za-z0-9_.-]+|/home/[A-Za-z0-9_.-]+|~)"

# Patterns
# Match: <HOME>/Dev/<proj>[/ or $ or " or boundary] — to know where the proj name ends
PAT = re.compile(HOME_ALT + r"/Dev/" + PROJ_ALT + r"\b")

# Shell canonical fallback to skip: ${PROJ:-...}
FALLBACK_SKIP = re.compile(r"\$\{(NEXUS|ANIMA|HEXA_LANG|N6_ARCH|AIRGENOME|VOID|PAPERS):-")


def should_skip_path(p: pathlib.Path) -> bool:
    parts = p.parts
    for part in parts:
        if part in EXCLUDE_DIRS:
            return True
        for pref in EXCLUDE_DIR_PREFIXES:
            if part.startswith(pref):
                return True
    if p.name in EXCLUDE_LOG_BASENAMES:
        return True
    return False


def transform_line(line: str, ext: str) -> tuple[str, int]:
    """Return (new_line, n_replacements). Keeps line if @allow-devpath or fallback pattern."""
    if "@allow-devpath" in line:
        return line, 0
    if FALLBACK_SKIP.search(line):
        # Line has canonical fallback — but may also have bare match before it.
        # Conservative: skip line entirely to avoid double-fallback.
        return line, 0

    def repl(m):
        proj = m.group(1)
        var = PROJ_MAP[proj]
        if ext == ".sh":
            return "${" + var + ":-" + m.group(0) + "}"
        # .hexa / .md / .json / .jsonl: simple $VAR
        return "$" + var

    new, n = PAT.subn(repl, line)
    return new, n


def process_file(p: pathlib.Path, apply: bool) -> int:
    ext = p.suffix
    if ext not in EXT_ALLOW:
        return 0
    try:
        text = p.read_text()
    except Exception:
        return 0

    lines = text.split("\n")
    total = 0
    for i, line in enumerate(lines):
        new, n = transform_line(line, ext)
        if n > 0:
            total += n
            lines[i] = new

    if total > 0 and apply:
        new_text = "\n".join(lines)
        if new_text != text:
            p.write_text(new_text)
    return total


def scan_project(root: pathlib.Path, apply: bool) -> tuple[int, int]:
    files_changed = 0
    total_fixes = 0
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if should_skip_path(p.relative_to(root)):
            continue
        n = process_file(p, apply)
        if n > 0:
            files_changed += 1
            total_fixes += n
    return files_changed, total_fixes


if __name__ == "__main__":
    apply = "--apply" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    projects = args or ["papers"]

    for pname in projects:
        root = pathlib.Path(os.path.expanduser(f"~/Dev/{pname}"))
        if not root.exists():
            print(f"SKIP {pname}: not found")
            continue
        files, fixes = scan_project(root, apply)
        mode = "APPLY" if apply else "DRY-RUN"
        print(f"{mode} {pname}: {files} files, {fixes} replacements")
