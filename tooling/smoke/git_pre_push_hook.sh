#!/bin/bash
# tooling/smoke/git_pre_push_hook.sh — git pre-push smoke gate (option A from CI integration spec).
#
# 사용:
#   ln -sf ../../tooling/smoke/git_pre_push_hook.sh .git/hooks/pre-push
#
# 동작: smoke 6/6 또는 7/7 (validate 포함) 실행. 1+ FAIL → push 차단.
# 우회: git push --no-verify (응급용).

set -e
REPO_ROOT="$(git rev-parse --show-toplevel)"
SMOKE="$REPO_ROOT/tooling/smoke/mk2_atlas_smoke.sh"

if [[ ! -x "$SMOKE" ]]; then
  echo "[pre-push] smoke script missing: $SMOKE — skipping" >&2
  exit 0
fi

echo "[pre-push] running mk2 atlas smoke..."
if "$SMOKE"; then
  echo "[pre-push] smoke PASS"
  exit 0
else
  echo "[pre-push] smoke FAIL — push blocked. Use --no-verify to bypass." >&2
  exit 1
fi
