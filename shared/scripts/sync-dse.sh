#!/bin/bash
# Sync .shared/dse/ (Universal DSE) across all repos
# Source of truth: TECS-L/.shared/dse/
#
# Since other repos symlink .shared/ → ../TECS-L/.shared/,
# DSE is already shared automatically. This script now only
# syncs to repos with their OWN dse copies (e.g. n6-architecture/tools/).
#
# Usage: bash .shared/sync-dse.sh

set -e

SHARED_DIR="$(cd "$(dirname "$0")" && pwd)"
DSE_SRC="$SHARED_DIR/dse"
BASE="$(cd "$SHARED_DIR/.." && pwd)"
PARENT="$(cd "$BASE/.." && pwd)"

if [ ! -d "$DSE_SRC" ]; then
  echo "Error: $DSE_SRC not found"
  exit 1
fi

DOMAIN_COUNT=$(ls "$DSE_SRC/domains/"*.toml 2>/dev/null | wc -l | tr -d ' ')

echo "=== Syncing Universal DSE ==="
echo "Source: $DSE_SRC ($DOMAIN_COUNT domains)"
echo ""

# ── n6-architecture: has its own tools/universal-dse/domains/ ──
N6_DSE="$PARENT/n6-architecture/tools/universal-dse/domains"
if [ -d "$N6_DSE" ]; then
  echo "[n6-architecture tools/universal-dse/domains/]"
  # .shared → n6 (add missing domains)
  added=0
  for f in "$DSE_SRC/domains/"*.toml; do
    base=$(basename "$f")
    if [ ! -f "$N6_DSE/$base" ]; then
      cp "$f" "$N6_DSE/$base"
      echo "  + $base"
      added=$((added + 1))
    fi
  done
  # n6 → .shared (reverse sync new domains)
  for f in "$N6_DSE/"*.toml; do
    base=$(basename "$f")
    if [ ! -f "$DSE_SRC/domains/$base" ]; then
      cp "$f" "$DSE_SRC/domains/$base"
      echo "  < $base (reverse)"
      added=$((added + 1))
    fi
  done
  if [ $added -eq 0 ]; then
    echo "  Already in sync"
  else
    echo "  Synced $added files"
  fi

  # Commit n6 if changed
  cd "$PARENT/n6-architecture"
  if ! git diff --quiet tools/universal-dse/ 2>/dev/null || \
     [ -n "$(git ls-files --others --exclude-standard tools/universal-dse/ 2>/dev/null | head -1)" ]; then
    git add tools/universal-dse/
    git commit -m "Sync DSE domains from TECS-L"
    git push
    echo "  Pushed!"
  fi
  cd - > /dev/null
fi

# ── Other repos: .shared/ is a symlink, no copy needed ──
echo ""
for repo in anima sedi brainwire papers; do
  repo_dir="$PARENT/$repo"
  if [ -L "$repo_dir/.shared" ]; then
    echo "[$repo] .shared/ is symlink — auto-synced ✓"
  elif [ -d "$repo_dir/.shared/dse" ]; then
    echo "[$repo] WARNING: .shared/ is NOT a symlink — manual sync needed"
  fi
done

# ── Commit TECS-L if .shared/dse changed ──
cd "$BASE"
if ! git diff --quiet .shared/dse/ 2>/dev/null || \
   [ -n "$(git ls-files --others --exclude-standard .shared/dse/ 2>/dev/null | head -1)" ]; then
  git add .shared/dse/
  git commit -m "Sync DSE domains (reverse sync from n6)"
  git push
  echo ""
  echo "TECS-L: Pushed reverse sync!"
fi

echo ""
echo "Done! ($DOMAIN_COUNT domains in .shared/dse/domains/)"
