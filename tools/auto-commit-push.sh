#!/usr/bin/env bash
# Auto-commit + push of agent-generated changes.
# Runs every 30min. Commits shared/* + docs/hypotheses/* changes only.
# Skips if no changes or if inside a manual git operation.
set -euo pipefail

NEXUS6="${HOME}/Dev/nexus6"
cd "$NEXUS6"

# Skip if merge/rebase in progress
if [ -e .git/MERGE_HEAD ] || [ -e .git/REBASE_HEAD ] || [ -d .git/rebase-merge ]; then
    echo "[$(date -u +%FT%TZ)] skipped: git operation in progress"
    exit 0
fi

# Only auto-commit on feat/alien-index (not main)
BRANCH=$(git branch --show-current)
if [ "$BRANCH" != "feat/alien-index" ]; then
    echo "[$(date -u +%FT%TZ)] skipped: branch=$BRANCH (not feat/alien-index)"
    exit 0
fi

# Stage only agent-generated paths
git add shared/verified_constants.jsonl 2>/dev/null || true
git add shared/cycle/ 2>/dev/null || true
git add shared/self_improve_log.jsonl 2>/dev/null || true
git add shared/calc/auto_stubs/ 2>/dev/null || true
git add shared/alien_index_distribution.json 2>/dev/null || true
git add docs/hypotheses/ 2>/dev/null || true

# Skip if nothing staged
if git diff --cached --quiet; then
    echo "[$(date -u +%FT%TZ)] no changes to commit"
    exit 0
fi

# Get change stats
LINES_ADDED=$(git diff --cached --numstat | awk '{sum+=$1} END {print sum+0}')
FILES_CHANGED=$(git diff --cached --numstat | wc -l | tr -d ' ')

# Single-line commit message with agent marker
MSG="auto: agent sweep +${LINES_ADDED} lines ${FILES_CHANGED} files @ $(date -u +%FT%TZ)"

git -c commit.gpgsign=false commit -m "$MSG" -m "Auto-committed by tools/auto-commit-push.sh

Co-Authored-By: nexus6-auto-loop <noreply@need-singularity>
" 2>&1 | tail -3

# Push (non-blocking: retry once on failure, then give up)
if ! git push origin "$BRANCH" 2>&1 | tail -3; then
    sleep 5
    git push origin "$BRANCH" 2>&1 | tail -3 || echo "push failed, will retry next run"
fi

echo "[$(date -u +%FT%TZ)] auto-committed +${LINES_ADDED}L/${FILES_CHANGED}F"
