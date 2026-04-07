#!/usr/bin/env python3
"""Generate projects.md from projects.json (Single Source of Truth).

Usage:
    python3 shared/gen_projects_md.py          # stdout
    python3 shared/gen_projects_md.py --save   # write to .shared/projects.md
"""
import json, os, sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(SCRIPT_DIR, "projects.json")
# .shared is in TECS-L; this script may run from nexus (symlinked)
TECS_SHARED = os.path.realpath(SCRIPT_DIR)
OUTPUT_PATH = os.path.join(TECS_SHARED, "projects.md")


def load():
    with open(JSON_PATH) as f:
        return json.load(f)


def gen(data):
    meta = data["_meta"]
    org = meta["github_org"]
    projects = data["projects"]
    order = meta["readme_order"]
    links = data.get("common_links", [])

    lines = []

    # --- common links ---
    lines.append("<!-- AUTO:COMMON_LINKS:START -->")
    parts = []
    for lk in links:
        if lk.get("public", True):
            parts.append(f"**[{lk['label']}]({lk['url']})**")
    lines.append(" · ".join(parts))
    lines.append("<!-- AUTO:COMMON_LINKS:END -->")
    lines.append("")

    # --- project entries ---
    visible = []
    for key in order:
        # absorbed project: "parent.child"
        if "." in key:
            parent_key, child_key = key.split(".", 1)
            parent = projects[parent_key]
            info = parent["absorbed_info"][child_key]
            name = info.get("display_name", child_key)
            icon = info["icon"]
            desc = info["description"]
            repo = child_key.lower()
            private = info.get("private", False)
        else:
            proj = projects[key]
            private = proj.get("private", False)
            name = proj.get("display_name", key)
            icon = proj["icon"]
            desc = proj["description"]
            repo = key

        if private:
            continue

        url = f"https://github.com/{org}/{repo}"

        # papers special: append browse link
        if key == "papers":
            browse = f"[Browse online](https://need-singularity.github.io/papers/)"
            if "Browse online" not in desc:
                desc = desc.rstrip(".") + f". {browse}"
            else:
                desc = desc.replace("Browse online", browse)

        visible.append(f"> **[{icon} {name}]({url})** — {desc}")

    for i, line in enumerate(visible):
        lines.append(line)
        if i < len(visible) - 1:
            lines.append(">")

    lines.append("")
    lines.append("<!-- private repos\ub294 projects.json\uc758 private_repos \ud544\ub4dc\uc5d0 \uc800\uc7a5\ub428 (\ub178\ucd9c \uae08\uc9c0) -->")

    return "\n".join(lines) + "\n"


def main():
    data = load()
    md = gen(data)

    if "--save" in sys.argv:
        with open(OUTPUT_PATH, "w") as f:
            f.write(md)
        print(f"Saved: {OUTPUT_PATH}")
    else:
        print(md)


if __name__ == "__main__":
    main()
