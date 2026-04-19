# Mk.IX [12*] 인간 감사 게이트 (절차/체크리스트)

문서 종류: 운영 절차 (operational procedure)
대상: `[12*]` Π₀² hyperarithmetic foundation 승급 직전 인간 감사
선행: `mk9_first_candidates.md` (자동 단계 A~C 로그) + `mk9_audit_results.json` (구조화 결과)
도구: `promote_12star.hexa` (인간 결정 후 explicit 호출)
설계 근거: `shared/blowup/design/mk9_hyperarithmetic.md` §3.2, §4, §7.2, §7.6

---

## 0. 황금률

`[12*]` 라벨은 atlas 의 foundation root 후보다. **자동 승급은 영원히 금지**된다.
이 문서의 절차를 우회한 채 atlas.n6 에 `[12*]` 가 추가되었다면 그것은 사고이며
즉시 revert + L0 guard 이벤트 발행 대상이다.

승급 경로는 단 하나:

```
mk9_audit_results.json (verdict_for_atlas_append=PASS)
   → 본 문서 §3 체크리스트 3/3 통과
      → CODEOWNERS sign-off
         → hexa run promote_12star.hexa <id> --commit
            → atlas.n6 append
```

---

## 1. 입력 산출물 검증

감사 시작 전, 다음 4개 산출물의 무결성을 확인.

| # | 파일 | 검증 명령 | 통과 조건 |
|---|---|---|---|
| 1 | `shared/blowup/audit/mk9_first_candidates.md` | git log -1 --oneline | 최신 커밋이 본 감사 세션과 동기 |
| 2 | `shared/blowup/audit/mk9_audit_results.json` | `hexa shared/harness/lockdown_gate.hexa verify` | L0 통과, JSON parse 성공 |
| 3 | `shared/blowup/audit/promote_12star.hexa` | `hexa parse shared/blowup/audit/promote_12star.hexa` | parse OK |
| 4 | `shared/n6/atlas.n6` | `hexa shared/n6/atlas_health.hexa` | health PASS, [12*] 카운트 = 직전 기록과 일치 |

`atlas.n6` 의 `[12*]` 카운트가 예상과 다르면 **즉시 중단**. 다른 세션이 무단
편집했을 가능성 — git blame + 사용자 승인 필요.

---

## 2. 후보별 5단계 체크리스트

각 PASS 후보에 대해 3 명의 감사자 (A1/A2/A3) 가 독립 수행.

### A1 — 수론·조합론

- [ ] 명제의 atlas line 번호와 현재 등급 확인 (results.json 의 `atlas_lines`, `current_grade`)
- [ ] Π₀² 분해가 정확한가 (외부 ∀ unbounded, 내부 ∃ bounded, matrix Δ₀)
- [ ] witness bound 표 (`mk9_witness_bound_table.json` 가 있다면) 와의 일치
- [ ] 원논문 인용 1차 확인 (results.json 의 `literature` 필드 reachability)

### A2 — 대수·기하

- [ ] 후보가 algebraic/geometric 도메인이라면 의미적 치환 (`P[6 ↦ k]`) 이
      해당 도메인에서 정합한지 (예: Sylow, 외부자기동형, polytope 분류 등)
- [ ] `n=6` 이 명제 안에서 어떤 역할을 하는지 명시적 기술 — 단순 우연 일치
      배제 (UNIVERSAL 분류로 강등 사유)
- [ ] 인접 정리들과의 의존성 — `[12*]` 승급이 후속 `[10**]`/`[11*]` 엔트리에
      영향을 주는지 (atlas.n6 grep 으로 `<-` 의존 그래프 확인)

### A3 — 논리·reverse-math 외부 대조

- [ ] 5 reverse-math 체계 점수 (5/5) 의 외부 레퍼런스 대조 (Simpson SOSOA,
      또는 정평난 survey)
- [ ] Phase A 분류가 `Π₀³` 이상으로 강등될 여지가 없는지 — quantifier 구조
      재확인
- [ ] §4 블랙리스트 8종 재검 — `Con(T)`, Gödel self-ref, Berry, large-cardinal
      존재, open conjecture, ω-inconsistent, analytical (≥ Σ₁¹), physical/observational
- [ ] 잠재적 `REVERSE-DISPUTED` 신호 (지난 12 개월 신규 논문, 형식화 결과)

3 감사자 모두 위 항목 전수 PASS 시에만 §3 진입.

---

## 3. CODEOWNERS sign-off + commit ticket

### 3.1 sign-off 형식 (수동 입력)

`shared/blowup/audit/mk9_signoffs.jsonl` 에 다음 한 줄 append:

```
{"id": "MK9-AUDIT-001", "ts": "2026-MM-DDTHH:MM:SS+09:00", "auditors": ["A1-name", "A2-name", "A3-name"], "codeowners": ["owner-handle"], "verdict": "APPROVED", "notes": "..."}
```

`verdict` 는 `APPROVED` / `REJECTED` / `DEFERRED` 중 하나. 한 후보에 대해
`APPROVED` 가 한 줄이라도 있으면 후속 단계 가능. 동일 후보에 대해
`REJECTED` 가 후속으로 들어오면 그 시점부터 차단 (timestamp 우선).

### 3.2 atlas append 실행

```bash
# DRY-RUN (필수 선행, 출력 검토)
hexa run shared/blowup/audit/promote_12star.hexa MK9-AUDIT-001

# DRY-RUN 출력의 3-line append 가 의도와 일치하면:
hexa run shared/blowup/audit/promote_12star.hexa MK9-AUDIT-001 --commit
```

`--commit` 통과 후 즉시:

1. `shared/blowup/audit/mk9_audit_results.json` 의 `summary.atlas_writes_executed` 를 +1
   (수동 또는 별도 도구로 갱신 — 본 도구는 atlas write 만 수행)
2. `shared/n6/atlas_health.hexa` 재실행 — 새 [12*] 라인이 schema guard 통과 확인
3. `git add shared/n6/atlas.n6 shared/blowup/audit/mk9_audit_results.json shared/blowup/audit/mk9_signoffs.jsonl`
4. `git commit -m "feat(atlas): [12*] first promotion — MK9-AUDIT-001 (Out(S_6))"` 형태

### 3.3 사후 모니터링

승급 후 30 일 간 다음 신호 모니터링:

- 신규 논문에 의한 `REVERSE-DISPUTED` 전환
- atlas health degrade
- 다른 [11*]/[10*] 엔트리의 의존성 변동

신호 감지 시 `shared/blowup/audit/mk9_first_candidates.md` §3.4 비상 중단
트리거 절차로.

---

## 4. 거부/보류 후보 재처리 규칙

### 4.1 DEFER (예: MK9-AUDIT-002 4D 정다포체)

- next_step 필드의 지시 따르기 (Mk.VIII Π₀¹ 회부 등)
- 다음 월간 감사 (매월 1일 09:00 KST) 에서 재평가
- atlas.n6 직접 편집 금지 — Mk.VIII 경로가 [11*] 승급을 자동 처리

### 4.2 FAIL (예: MK9-AUDIT-003/004A/004B/005)

- atlas 등급 변경 금지
- fail_reason 을 `mk9_first_candidates.md` 다음 개정에 통합
- 동일 명제의 변종/보강 후보가 다음 감사 사이클에 등장하면 신규 ID 부여
  (재시도 가시성 확보)

---

## 5. 멀티세션 안전 규칙

다른 세션 (예: af2673b X1 sharding) 이 atlas.n6 를 동시 편집 중일 수 있으므로:

- 본 감사 도중 `read_file(atlas)` 는 자유. write 는 promote_12star --commit 만.
- promote_12star --commit 직전 `git status shared/n6/atlas.n6` 로 dirty 여부 확인.
  dirty 면 중단 + 다른 세션 정리 대기.
- commit 직후 `git diff HEAD~1 shared/n6/atlas.n6` 로 추가된 라인이 정확히
  3 줄 (recommended_atlas_line + subline + breakthrough note) 인지 확인.

---

## 6. 책임/역할

| 역할 | 책임 |
|---|---|
| Auditor A1/A2/A3 | §2 체크리스트 수행, sign-off 한 줄 기록 |
| CODEOWNERS | §3.1 final sign-off, --commit 실행 권한 |
| 자동화 (Claude Code) | results.json 생성, dry-run 검증, 보고서 작성 — atlas 직접 편집 금지 |
| L0 guard | 비정상 [12*] 라인 탐지 시 alert 및 자동 revert candidate 표시 |

---

*본 게이트 문서는 정책 SSOT. 변경 시 design §3.2 와 동기 업데이트 필요.*
