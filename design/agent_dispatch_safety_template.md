# Agent Dispatch Safety Template (Tier-1 i20)

> origin: `design/hexa_sim/2026-04-26_improvement_ideas_omega_cycle.json` axis i20
>
> trigger: 본 세션 (2026-04-26) 의 dedup Tier-1 patch SIGKILL 사례 — agent 가 hexa_sim_atlas_ingest.hexa 에 +146 LoC patch 했으나 selftest 무한루프/OOM, half-side patch (omega_cycle_atlas_ingest 미적용), recovery 비용 큼.

---

## Mandatory elements (모든 future agent dispatch prompt 포함 권장)

### 1. **Pre-flight self-check 의무**

agent 가 patch/edit 시작 전:
- 대상 파일 의 기존 selftest 가 PASS 인지 확인 (baseline 측정)
- runtime health: `tool/hexa_runtime_check.sh` PASS 인지 (runtime 가능성)
- 이 두 baseline 가 PASS 안 한 상태에서는 patch 진행 금지 (no-op + 상태 보고)

### 2. **Line cap 의무**

shell exec 또는 grep/awk pipe 가 큰 파일 (atlas.n6 21850 lines, .raw 1614 lines 등) 대상 시:
- `head -N`, `tail -N`, `awk 'NR<=N'` 으로 line count cap (default N=5000)
- N 초과 시 fast-skip (graceful degrade) + 명시적 보고
- infinite loop 위험 차단

### 3. **Atomic rollback 가능 패턴**

patch 가 multi-file 인 경우:
- 각 file edit 직후 selftest — FAIL 시 즉시 git checkout 으로 revert
- 또는 새 file 만 작성 (기존 미수정), main thread 가 통합 결정
- partial patch (한 file PASS + 한 file FAIL) 회피

### 4. **Selftest extension 의무**

새 기능 추가 시:
- 기존 selftest 의 case 수 보존
- 새 기능 의 case 추가 (최소 3 case: positive + negative + edge)
- 추가된 case 가 모두 PASS 인 경우만 selftest OK 보고

### 5. **Sentinel + exit code 일관성**

새 modes/flags 시:
- sentinel 형식 보존 (`__<TOOL>__ PASS|FAIL ...`)
- exit code 매핑 표 명시 (0=PASS, 1=usage, 2=schema, 3=conflict, 4=runtime, 5=hello)
- 새 exit code 가 필요하면 사유 명시

### 6. **Polyfill 회피**

hexa stdlib gap 시:
- 첫 번째 시도: builtin method (`s.index_of()`, `s.contains()`, `len(s)` 등) 활용
- 그래도 미충족 시: per-file inline polyfill (다른 파일 의존 X)
- `str_find` 같은 generic polyfill 정의 + 다수 호출자 패턴 회피 (sed-replace 시 함수 정의도 깨질 위험 — 본 세션 직접 발견)

### 7. **Backward-compat 명시**

기존 modes 가 깨지지 않음 보장:
- 새 flag 추가 시 default 값 = 이전과 동일
- 기존 sentinel 출력 보존
- 기존 selftest 모두 PASS

### 8. **Reporting 형식**

agent 보고:
- LoC delta (added/removed)
- selftest 결과 (case 수 + PASS/FAIL 분포)
- live verification 결과 (예: --json-summary 출력 sample)
- residual gaps (정직 보고, 회피 안 함)
- file 목록 (수정된 파일 절대경로)

### 9. **Commit 금지 (main thread 가 통합)**

- agent 는 절대 commit 안 함
- working tree 만 수정
- main thread 가 selftest 재검증 → atomic commit
- 이유: agent 의 selftest 결과 가 약속과 불일치 가능 (이번 세션 발견)

### 10. **Hexa runtime fallback 가이드**

hexa 도구 작성 시:
- `tool/hexa_runtime_check.sh` 통과 확인 후 selftest
- runtime down 시: bash/Python 으로 fallback 기능 작성 (self-host 회피)
- 예: `hexa_runtime_check.sh` 자체가 bash (hexa 없이 작동) — 본 세션 i2 axis

---

## Anti-patterns (이번 세션 직접 발견)

### A1. **Bulk sed across function defs**

- 함수 정의 패턴 (`fn name(args)`) 도 매치 → syntax 깨짐
- 예: `sed 's/str_find(\1, \2)/\1.index_of(\2)/g'` 가 `fn str_find(s: string, needle: string)` 도 매치 → `fn s: string.index_of(needle: string)` 잘못된 syntax
- **fix**: replace 전 grep 으로 callers vs definers 구분, 또는 manual edit

### A2. **Heavy regex in tight loops**

- atlas.n6 21850 lines 대상 grep 을 매 dup-check 마다 호출 → O(N×M) 폭증
- 309 facts × 21850 lines ≈ 6.7M operations
- **fix**: 사전 인덱스 빌드 (i1 atlas-index axis)

### A3. **Awk pipe in shell substring**

- `awk 'BEGIN{f=0} ... print'` 같이 복잡한 awk 가 hexa 의 `exec()` wrapper 안에서 escape 문제 + 큰 input 시 hang/OOM
- **fix**: 단순 grep + && echo 패턴 (이번 세션 falsifier registry 에서 학습)

### A4. **Half-side patch (multi-file)**

- 두 도구 (hexa_sim_atlas_ingest + omega_cycle_atlas_ingest) 가 dedup 로직 공유 — 한 쪽만 patch → 비대칭
- **fix**: 두 file 동시 수정 + 둘 다 selftest PASS 까지 단일 atomic 단위

### A5. **Mixed-context test cases**

- selftest 가 isolated (단순 case) 만 PASS 하지만 integrated (실제 atlas 21850 lines) 에서 FAIL
- **fix**: selftest 에 minimal+real 두 카테고리, 둘 다 PASS 의무

---

## Template snippet (agent prompt 시작부 권장 inclusion)

```
**Pre-flight (mandatory):**
1. tool/hexa_runtime_check.sh --verbose → exit 0 확인
2. 기존 selftest baseline 측정 (수정 전)
3. 두 baseline PASS 안 시 → no-op + 상태 보고만

**Edit constraints (mandatory):**
1. Bulk sed 금지 — fn 정의 패턴 보존 (A1)
2. heavy loop 안 grep 금지 — 사전 cache (A2)
3. awk 복잡 pipe 금지 — 단순 grep + echo (A3)
4. Multi-file patch 시 둘 다 동시 수정 + 둘 다 selftest PASS (A4)

**Selftest extension (mandatory):**
- 기존 case 수 보존
- 신규 기능 case 최소 3개 (positive + negative + edge)
- minimal + real(integration) 두 카테고리 모두 PASS

**Reporting (mandatory):**
- LoC delta / selftest case 분포 / live --json-summary sample / residual gaps
- 절대 commit 금지

**Polyfill (recommended):**
- builtin 우선: s.index_of(), s.contains(), len(s)
- 미충족 시 per-file inline polyfill (다른 파일 의존 X)

**Runtime guard (recommended):**
- hexa-based 도구 작성 시 runtime down 가능성 명시
- self-host 가능성 회피 (예: 본 도구가 자기 검증 시 같은 runtime 사용)
```

---

## Reference: 본 세션 직접 적용 사례

| 사례 | 적용된 element | 결과 |
|------|--------------|------|
| codata_bridge agent (b1) | #1 baseline + #5 sentinel + #8 reporting | PASS, 366 LoC, 8 checks selftest |
| oeis_live_bridge agent (b2) | #1 + #5 + #8 + #9 (no commit) | PASS, 277 LoC, 4 sequence cross-check |
| Phase 2 omega_cycle agent | #6 polyfill 위배 (str_find 정의 + sed shadowed) | FAIL → revert + manual fix (commit becf3594) |
| dedup Tier-1 patch agent | #2 line cap 미적용 + #4 selftest extension 미검증 + #4 atomic rollback 미적용 | FAIL → SIGKILL → defer (commit 2243da20) |
| hexa_runtime_check (이 세션) | #10 self-host 회피 (bash) | PASS, 136 LoC, 5-stage detection |

---

## Adoption

- 이 template 은 nexus 내 agent dispatch 의 권장 — 강제 아님
- 다음 세션 의 모든 agent prompt 시작부에 위 snippet 인용 권장
- 본 doc 자체가 atlas 의 `@L meta_methodology [10*PASS_LITERATURE]` 후보
- 추가 anti-pattern 발견 시 본 doc 의 § Anti-patterns 에 append (raw 77 audit-append-only 적용)
