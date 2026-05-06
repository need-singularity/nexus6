# mk2 atlas smoke — CI integration spec

> Status: design-only · 2026-05-06 · backlog from atlas_recall_cycle retro § 8 #4

## Motivation

`tooling/smoke/mk2_atlas_smoke.sh` 는 6/6 회귀 가드 (~10–15s 캐시 후). 현재 수동 호출만. 자동 통합으로 atlas KB 변경 시 회귀 즉시 감지.

## Options (4)

| 옵션 | 비용 | 효과 | 위험 |
|---|---|---|---|
| A. git pre-push hook | 0.5h | local push 차단 | 사용자 우회 가능 (`--no-verify`) |
| B. launchd plist 정기 실행 | 1h | 1h마다 적재 | latency, 디스크 |
| C. hive claude-hook-bind PostToolUse | 1–2h | atlas/* 수정 시 자동 | hook chain 부담 |
| D. GitHub Actions workflow | 0.5h (인프라 있으면) | PR 차단 | 설정 의존 |

## Recommendation

**A + C 조합**:
- A: 즉시 적용 (`tooling/smoke/git_pre_push_hook.sh` wrapper, 사용자가 `.git/hooks/pre-push` 에 symlink)
- C: hive claude-hook-bind PostToolUse phase 에 atlas/*.hexa 수정 트리거 (async, background, 실패 시 stderr 알림만)
- B/D 는 후속

## Implementation A (pre-push)

```bash
# tooling/smoke/git_pre_push_hook.sh (신규)
#!/bin/bash
set -e
REPO_ROOT="$(git rev-parse --show-toplevel)"
"$REPO_ROOT/tooling/smoke/mk2_atlas_smoke.sh" --quiet
```

사용자 가이드 (한 줄): `ln -sf ../../tooling/smoke/git_pre_push_hook.sh .git/hooks/pre-push`

## Implementation C (hook bind)

새 module `/Users/ghost/core/hive/hive-claude-hook-bind/module/atlas_smoke_post_write.hexa` (~150줄):
- PostToolUse phase
- payload 의 file_path 가 `mk2_hexa/mk2/src/atlas/*.hexa` 또는 `tooling/atlas-validator/*.hexa` 매칭 시 트리거
- async exec (background 호출, 결과는 `state/atlas_smoke_history.jsonl` 적재)
- selftest sentinel `__BIND_ATLAS_SMOKE_POST_WRITE_SELFTEST__ PASS`
- patch md 형식 (registry/main/manifest 갱신)

## Verification

- A: pre-push 시 smoke 6/6 PASS, push 성공
- A: 의도적 실패 (mod.hexa 깨기) → push 차단
- C: atlas/*.hexa 수정 후 history.jsonl 1줄 추가
- 회귀 0

## Follow-ups

- B (launchd): 후속, retro § 8 따라
- D (GitHub Actions): 인프라 있으면 후속
- smoke 스크립트 자체 개선 (병렬 실행, jsonl 적재) — 별도 트랙
