#!/usr/bin/env python3
import json, sys, os, subprocess

SSOT = os.path.expanduser("~/Dev/nexus/shared/config/projects.json")


def load():
    with open(SSOT) as f:
        return json.load(f)


def save(d):
    with open(SSOT, "w") as f:
        json.dump(d, f, indent=2, ensure_ascii=False)
        f.write("\n")


def list_projects():
    d = load()
    projects = d.get("projects", {})
    if not projects:
        print("(empty)")
        return
    rows = [(n, p.get("display_name", n), p.get("root", "?"), p.get("role", "?")) for n, p in projects.items()]
    headers = ("name", "display", "root", "role")
    widths = [max(len(str(r[i])) for r in [headers] + rows) for i in range(4)]

    def bar(l, m, r):
        return l + m.join("─" * (w + 2) for w in widths) + r.replace(m, "")[0] if False else \
               l + ("─" * (widths[0] + 2)) + m + ("─" * (widths[1] + 2)) + m + ("─" * (widths[2] + 2)) + m + ("─" * (widths[3] + 2)) + r

    def row(a, b, c, dv):
        return f"│ {a:<{widths[0]}} │ {b:<{widths[1]}} │ {c:<{widths[2]}} │ {dv:<{widths[3]}} │"

    print(bar("┌", "┬", "┐"))
    print(row(*headers))
    print(bar("├", "┼", "┤"))
    for i, r in enumerate(rows):
        if i > 0:
            print(bar("├", "┼", "┤"))
        print(row(*r))
    print(bar("└", "┴", "┘"))
    print(f"총 {len(rows)} 프로젝트")


def add_project(name):
    d = load()
    projects = d.setdefault("projects", {})
    if name in projects:
        print(f"REJECT: '{name}' 이미 존재")
        sys.exit(1)
    projects[name] = {
        "root": f"~/Dev/{name}",
        "display_name": name,
        "role": "unknown",
        "description": "auto-generated skeleton",
        "hypothesis_dirs": [],
        "constant_dirs": [],
        "verify_harvest": {},
    }
    save(d)
    print(f"✓ '{name}' 추가됨 (총 {len(projects)})")


def remove_project(name):
    d = load()
    projects = d.get("projects", {})
    if name not in projects:
        print(f"NOT_FOUND: '{name}'")
        sys.exit(1)
    root = os.path.expanduser(projects[name].get("root", f"~/Dev/{name}"))
    l0_markers = [".ssot", "shared/L0", "CLAUDE.md", "shared/lockdown"]
    found = [m for m in l0_markers if os.path.exists(os.path.join(root, m))]
    if found:
        print(f"REJECT: L0 자산 존재 — {found}")
        sys.exit(2)
    del projects[name]
    save(d)
    print(f"✓ '{name}' 제거됨 (총 {len(projects)})")


def all_projects(cmd):
    d = load()
    projects = d.get("projects", {})
    for name, p in projects.items():
        root = os.path.expanduser(p.get("root", f"~/Dev/{name}"))
        if not os.path.isdir(root):
            print(f"=== {name} === (SKIP: {root} 없음)")
            continue
        print(f"=== {name} ===")
        try:
            r = subprocess.run(cmd, shell=True, cwd=root, capture_output=True, text=True, timeout=60)
            if r.stdout:
                print(r.stdout[:800])
            if r.returncode != 0 and r.stderr:
                print(f"[stderr] {r.stderr[:300]}")
        except Exception as e:
            print(f"ERROR: {e}")


def main():
    argv = sys.argv[1:]
    if not argv or argv[0] == "list":
        list_projects()
    elif argv[0] == "add" and len(argv) >= 2:
        add_project(argv[1])
    elif argv[0] == "remove" and len(argv) >= 2:
        remove_project(argv[1])
    elif argv[0] == "all" and len(argv) >= 2:
        all_projects(" ".join(argv[1:]))
    else:
        print("USAGE: project_crud.py [list|add <name>|remove <name>|all <cmd>]", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
