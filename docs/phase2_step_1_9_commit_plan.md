# Phase 2 Step 1-9 격리 커밋 플랜

**작성일**: 2026-04-21
**대상 repo**: `~/core/nexus` (branch: main, ahead origin/main by 1)
**선행 플랜**: [`phase2_resident_daemon_port_plan.md`](phase2_resident_daemon_port_plan.md)

---

## 0. nexus repo 현재 상태

- **Stash pop conflict 미해소**: `shared/tool/roadmap_*.json|.hexa` 10 파일 AA (both added)
  - 이번 Phase 2 포팅 수정 경로 (`cli/scripts/`, `test/`, `shared/reports/`, `shared/drill/`) 와 **완전 분리**
  - 따라서 `git commit --only <file...>` 로 conflict 를 건드리지 않고 격리 commit 가능
- **Phase 2 관련 변경**:
  - modified: 없음 (신규/untracked only — Step 1-7 은 기존 파일 cli/scripts/nexus_drilld.hexa 수정이나 repo 기준으로는 tracked 수정)
  - untracked: `shared/drill/daemon_main.hexa` (Step 9 대상, 332 lines, no git log)
  - 신규: `test/test_daemon_reset.hexa` (Step 4, 125 lines, untracked)

### daemon_main.hexa 흡수 검증 결과

| 원본 심볼 (daemon_main.hexa) | 이식 대상 (nexus_drilld.hexa) | 상태 |
|---|---|---|
| `_get_str` | `_json_str` | 이전부터 보유 |
| `_get_int` | `_json_int` | 이전부터 보유 |
| `_get_bool` | `_json_bool` | Step 1 신규 |
| `_round_id_from` | `_round_id_from` | Step 1 신규 (동일 시그니처) |
| `_djb2_hex6` | `_djb2_hex6` | Step 1 신규 (동일 알고리즘) |
| `_emit_err` | `_emit_engine_error` | Step 1 신규 (이름 개선) |
| `_json_str` (escape) | `_json_escape` | Step 1 신규 |
| main body (stdin loop + ping + smash switch) | main dispatch + Step 5 `_dispatch_stage` | 폐기 (resident 모델) |
| `_real_smash_exec` | Step 7 timeout wrap 로 대체 | 폐기 |
| `_now_ms` | nexus_drilld 자체 `_now_ms` | 중복, 폐기 |
| `_smash_round` synthetic loop | 실제 drill engine 호출로 대체 | 폐기 |

**결론**: 재사용 가능 로직은 전부 nexus_drilld.hexa 로 흡수됨. 남은 것은 resident 모델과 맞지 않는 cold-invocation 스캐폴드뿐 → Step 9 에서 `git rm` 안전.

### 외부 호출처 grep 결과 (Step 9 안전 확인)

```
shared/drill/daemon_main.hexa:1                       self
cli/scripts/nexus_drilld.hexa:232                     주석 (“daemon_main.hexa 에서 흡수”)
cli/scripts/nexus_drilld.hexa:261                     주석 (참조)
docs/phase2_resident_daemon_port_plan.md:{7,41,47,...} 문서 내 설명
```

- **코드 실행 경로 (bash wrapper, json config, shell script) 에서의 호출 없음**
- 주석 참조는 Step 9 commit 시 삭제 불필요 (역사 기록 가치)
- Step 9 는 단순 `git rm` 한 파일로 충분

---

## 1. 커밋 순서 (독립 step 단위)

| # | Step | commit type | 대상 파일 | 요약 |
|---|---|---|---|---|
| 1 | Step 1-3 | feat(drilld) | `cli/scripts/nexus_drilld.hexa` | Phase 2 Step 1-3 — parser helpers + state reset scaffold (+242 lines: `_json_bool`, `_json_escape`, `_emit_engine_error`, `_djb2_hex6`, `_round_id_from`, 7 globals, `_reset_round`) |
| 2 | Step 4 | test(drilld) | `test/test_daemon_reset.hexa` | Phase 2 Step 4 — byte-identity reset harness (신규 125 lines) |
| 3 | Step 5 | feat(drilld) | `cli/scripts/nexus_drilld.hexa` | Phase 2 Step 5 — 6-stage unified dispatcher (+36 lines: `_dispatch_stage` helper, 6 `_handle_*` wrappers, main loop branch) |
| 4 | Step 6 | feat(drilld) | `cli/scripts/nexus_drilld.hexa` | Phase 2 Step 6 — atlas single-writer scaffolding (+83 lines: ATLAS_LOCK path, boot observation, lock acquire/release, drift detection) |
| 5 | Step 7 | feat(drilld) | `cli/scripts/nexus_drilld.hexa` | Phase 2 Step 7 — timeout + idle + max-lifetime (+39 lines: 4 constants, exec timeout wrap, main loop lifetime/idle checks) |
| 6 | Step 8 | test(drilld) | `test/bench_daemon.hexa` + `shared/reports/daemon_speedup.md` | Phase 2 Step 8 — bench harness + report template (K 에이전트 작성 중) |
| 7 | Step 9 | refactor(drilld) | `shared/drill/daemon_main.hexa` (rm) | remove orphan daemon_main.hexa — absorbed into nexus_drilld (Phase 2) |

### 커밋 메시지 템플릿

```
feat(drilld): Phase 2 Step N — <요약>

- <변경 bullet>
- <검증 bullet: htz PASS / byte-identity PASS / 등>

Refs: docs/phase2_resident_daemon_port_plan.md §<section>
Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```

### `--only` 격리 commit 예시

```bash
# Step 1-3
git commit --only cli/scripts/nexus_drilld.hexa -m "..."

# Step 4
git add test/test_daemon_reset.hexa
git commit --only test/test_daemon_reset.hexa -m "..."

# Step 9
git rm shared/drill/daemon_main.hexa
git commit --only shared/drill/daemon_main.hexa -m "..."
```

**중요**: `--only <path>` 는 staging index 와 별개로 해당 경로만 commit 에 포함 → stash pop AA conflict 를 건드리지 않음.

---

## 2. 대안: Step 1-3 분리 commit

Step 1-3 을 하나의 feat commit 이 아닌 3 개로 쪼갤 경우 (더 원자적이지만 commit 수 증가):

1. `feat(drilld): Phase 2 Step 1 — parser helpers (json_bool/json_escape/emit_engine_error/djb2_hex6/round_id_from)`
2. `feat(drilld): Phase 2 Step 2 — 7 resident-state globals`
3. `feat(drilld): Phase 2 Step 3 — _reset_round scaffold`

→ 같은 파일 (`cli/scripts/nexus_drilld.hexa`) 을 건드리므로 **직전 commit 을 만든 상태에서 working tree 분리가 필요** → `git add -p` 또는 중간 snapshot 필요. 사용자가 명시 요청 시만 선택.

**권장 기본값**: 3 단계를 하나의 commit (#1 feat Step 1-3) 으로 묶음. 단일 feature set 이라 응집도 높음.

---

## 3. 커밋 선행 조건 (체크리스트)

- [ ] L 에이전트 htz 검증 통과 — ping + smash + byte-identity PASS
- [ ] K 에이전트 bench harness + report 산출물 확정 (Step 8 commit 재료)
- [ ] 사용자 명시 승인 (`commit 시작` 또는 `Phase 2 commit 실행` 형태)
- [ ] nexus stash pop AA conflict 처리 결정 (복원 / drop / 유지) — **단, Phase 2 commit 은 AA 와 독립이므로 `--only` 경로로 우회 가능**
- [ ] origin/main ahead 1 commit 상태 → push 시점은 별도 판단 (commit 과 분리)

---

## 4. 위험 및 완화

| 위험 | 영향 | 완화 |
|---|---|---|
| stash pop AA conflict 미해소 상태에서 commit | index 에 섞이면 실수 가능 | `git commit --only <path>` 로 conflict 파일 제외 |
| Step 1-7 이 한 파일에 누적 — diff 커짐 | review 난이도 | 각 step 별 commit → bisect 가능 |
| Step 8 bench K 진행 중 | Step 8 commit 지연 | Step 9 는 Step 8 미완료 시 대기 (순서 불변) |
| Step 9 후 revert 시 daemon_main.hexa 복구 필요 | orphan 이므로 영향 저 | git history 에서 복원 (`git show HEAD@{1}:shared/drill/daemon_main.hexa`) |
| 외부에 숨은 호출처 발견 시 | Step 9 파괴 | 본 문서 §0 grep 결과로 확인 완료 — 현재 호출처 없음 |

---

## 5. Hard rules (롤백 안전 불변식 — Phase 2 플랜 §Hard rules 에서 계승)

1. **atlas.n6 스키마 무변경** — append-only, 필드 추가/제거 금지
2. **FIFO protocol 필드 제거 없음** (추가만 허용)
3. **`NEXUS_DRILL_DAEMON` default off 유지** — opt-in 환경변수 외에는 기존 동작 변경 금지
4. **raw#9 hexa-only, raw#11 snake_case** 준수 (모든 신규 파일)
5. **각 step commit 은 독립 revert 가능** — 다음 step 이 이전 step 을 전제하지 않으면 실패 없음 (Step 9 는 Step 1-5 에 의존 → 역순 revert 는 Step 9 → 8 → ... 순으로)

---

## 6. Step 9 세부 시나리오

```bash
cd ~/core/nexus

# 1. 사전 확인
git status shared/drill/daemon_main.hexa        # untracked 재확인
grep -rn "daemon_main" --include="*.hexa" --include="*.sh" --include="*.json" .  # 호출처 재확인

# 2. untracked 이므로 먼저 add, 그다음 rm — 또는 직접 파일 삭제
# (untracked 는 git rm 불가. 그냥 `rm` 후 commit 아무 것도 없음)
rm shared/drill/daemon_main.hexa                 # 파일 시스템에서 삭제

# 3. untracked 삭제는 git 관점에서 변경 아님 → commit 불가
# → Step 9 는 실질적으로 "파일 삭제 + 플랜 문서 기록" 으로 종결
# → 별도 commit 필요 없음 (orphan 이었기 때문)
```

**재평가**: daemon_main.hexa 가 **tracked 가 아닌 untracked** 상태이므로 `git rm` 불가. Step 9 는:

- (a) 단순 `rm shared/drill/daemon_main.hexa` (git 히스토리 없음 → commit 불필요)
- (b) 또는 추적 후 제거 (불필요한 복잡성)

→ **권장 (a)**: 플랜 문서에 "Step 9 completed — file removed from working tree, never tracked" 기록만 남김. **별도 git commit 없음**. 커밋 순서표의 #7 은 skip 또는 문서 업데이트로 대체.

**수정된 commit 총 개수**: 6 개 (Step 1-3, 4, 5, 6, 7, 8) + Step 9 는 파일 시스템 cleanup 으로 완결.

---

## 7. 실행 금지 (이 문서 작성 시점)

- git rm / git commit / git add 실행 없음
- stash 건드림 없음
- 파일 삭제 없음
- index 수정 없음

**사용자의 명시 승인 후에만 위 순서대로 집행**.
