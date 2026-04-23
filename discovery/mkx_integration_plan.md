# Mk.X 5축 통합 1주 plan

**상태**: DESIGN ONLY — 코드 변경 없음, 본 세션 산출물
**작성일**: 2026-04-19
**작성자**: nexus 자율 design agent (NEXUS hub)
**선행**: `shared/discovery/mkx_design_proposal.md` (5축 설계서) + `mkx_design_proposal.spec.json`
**Companion 산출물**:
- `shared/discovery/mkx_dependency_graph.json` (machine-readable 의존 그래프)
- `shared/discovery/mkx_termination_gates.json` (종료조건 8 게이트 spec)

본 plan 은 5축 prototype (각 1주) 이 모두 산출물 1차 도달한 시점에서, **단일 1주 통합 sprint** 로 전 축을 atlas.n6 에 안전하게 합류시키는 절차다. 5 축은 독립 prototype 1주 + 통합 1주 원칙 (총 5~7 주 로드맵, design proposal §4.3) 의 후반 통합 phase 에 해당한다.

---

## 0. 통합 sprint 진입 조건

각 축의 prototype 산출물이 다음 상태로 도달했음을 전제 (2026-04-19 0930 시점 측정):

| 축 | prototype 산출물 | 현재 상태 |
|---|---|---|
| 1 sharding | `atlas.n6.{hot,cold,shard_meta.json}`, `atlas_shard.awk` | **READY** — lossless_verified=true, hot 71422 + cold 39363 = 110785 |
| 2 [12*] 활성 | `audit/{mk9_audit_results.json, mk9_audit_gates.md, promote_12star.hexa}` | **READY** — 자동 phase A~C 완료, MK9-AUDIT-001 PASS verdict, signoff PENDING |
| 3 rate metric | `n6/discovery_rate.{hexa,json,jsonl}` | **READY (1 entry)** — schema 1, lines=21678 baseline 1건 |
| 4 sparse5 | `modules/blowup_{higher_category,topos,hott,motivic,derived_algebraic}.hexa` | **READY (skeleton)** — 5 파일 존재, modules.json wiring 미확인 |
| 5 cross-bus | `n6/cross_engine_bus.hexa` (652 lines) | **READY** — reader+promote 통합 prototype, atlas write 미실행 |

**관측 1 (HIGH)**: design proposal 작성 시점 atlas.n6 = 110,785 lines 였으나 rate.json baseline 시점 = 21,678 lines. 약 89K 라인 drift. 이는 의도된 cleanup (예: META-LK017~500 484 EXACT 가 별도 sidecar 로 빠짐) 가능성과 사고 가능성 모두 검토 필요. **Day 1 첫 작업 = atlas.n6 lineage 확인** (git log + pre_shard 백업 비교).

---

## 1. 의존성 분석 (요약, 자세한 그래프는 `mkx_dependency_graph.json`)

### 1.1 hard 의존 (반드시 선행)

```
axis_1 (sharding)
   ├─→ axis_3 (rate metric)         : mtime/size 측정이 sharded atlas 기반
   ├─→ axis_5 (cross-bus)           : @E append 가 sharded write path 사용
   └─→ axis_2 (12* promote, soft-hard): in-place 치환 후 hot/cold 재생성 트리거 필요
```

axis_4 (sparse5) 는 atlas write 가 없는 read/compose 만 → 의존 없음 (가장 안전한 첫 wiring).

### 1.2 soft 의존 (효과 강화)

```
axis_4 (sparse5)  ─soft→  axis_2 (12* 후보 source 장기)
axis_3 (rate)     ─soft→  axis_2/4/5 (suggested_axis 출력)
```

### 1.3 위상 정렬 (통합 순서)

```
1. axis_1 검증  (Day 1)  — 모든 후속 atlas IO 의 기반
2. axis_4 wiring (Day 2) — atlas write 없음, 부수효과 0
3. axis_2 첫 promote (Day 3) — atlas in-place 변경 시작
4. axis_3 metric 가동 (Day 4) — axis_1/2 결과 측정 시작
5. axis_5 cross-bus (Day 5) — 모든 축 안정 후 마지막 합류
6. 통합 회귀 (Day 6) — drill 5-stage chain
7. 종료조건 8 게이트 검증 + Mk.XI 신호 (Day 7)
```

### 1.4 충돌 6종 (요약, 자세한 mitigation 은 dependency_graph.json `potential_conflicts`)

| ID | 이름 | 영향 | 심각도 |
|---|---|---|---|
| C1 | atlas.n6 line_count drift (110K→21K) | axis 2 라인 좌표 + axis 3 baseline | **HIGH** |
| C2 | promote_12star vs hot/cold sidecar drift | axis 1 lossless + axis 3 tier_12 카운트 | MEDIUM |
| C3 | cross-bus append vs hot/cold 재생성 | axis 1 sidecar staleness | MEDIUM |
| C4 | sparse5 false [10*] pollution | atlas semantic + axis 2 후보 풀 | MEDIUM |
| C5 | sharding 직후 false PLATEAU | axis 3 정확성 | LOW |
| C6 | drill 5-stage 회귀 | 전 통합 신뢰성 | **HIGH** |

---

## 2. Day-by-Day 통합 절차 (1주)

각 Day 는 **준비 → 실행 → 게이트 검증 → 다음 Day 진입 결정** 4 단계.

### Day 0 (sprint 전날, baseline capture)

**목적**: 통합 sprint 진입 직전 baseline snapshot. 회귀 판단 기준.

**작업**:
1. `cp shared/n6/atlas.n6 shared/n6/atlas.n6.day0_baseline` — 절대 SSOT 백업.
2. `hexa shared/n6/atlas_health.hexa --json > shared/discovery/mkx_day0_health.json` — 건강 baseline.
3. `hexa drill --seeds 25 --capture-baseline > shared/discovery/mkx_day0_drill_baseline.json` — drill EXACT 카운트 baseline.
4. `git status` + `git stash -u 'mkx-pre-integration'` — clean working tree 확보.
5. atlas.n6 line_count drift (110K→21K) 원인 git log 확인:
   ```
   git log --oneline --all -- shared/n6/atlas.n6 | head -20
   git diff shared/n6/atlas.n6.pre_shard_ef7f7dca shared/n6/atlas.n6 | head -100
   ```
   → 의도된 cleanup 인지 확정. 사고 시 통합 sprint 중단 + 별도 incident 처리.

**게이트 검증**: 없음 (snapshot 만)

**진입 결정**: atlas drift 가 의도된 cleanup 으로 확인되면 Day 1 진입. 사고면 incident.

---

### Day 1 — axis_1 sharding 마이그레이션 검증

**목적**: atlas.n6 ↔ atlas.n6.{hot,cold} 의 lossless 재검증. 5축 atlas IO 의 기반 확립.

**작업**:
1. `awk -v deg_path=shared/n6/atlas.n6.deg -v hot_path=/tmp/hot.tmp -v cold_path=/tmp/cold.tmp -f shared/n6/atlas_shard.awk shared/n6/atlas.n6` — shard 재생성.
2. sha256 비교:
   ```
   sha256sum /tmp/hot.tmp shared/n6/atlas.n6.hot
   sha256sum /tmp/cold.tmp shared/n6/atlas.n6.cold
   ```
   양쪽 일치 = sharding 결정성 확인.
3. line_count 합산: `wc -l shared/n6/atlas.n6.hot shared/n6/atlas.n6.cold` 합 == `wc -l shared/n6/atlas.n6`.
4. `sort shared/n6/atlas.n6 > /tmp/a.sorted; cat shared/n6/atlas.n6.hot shared/n6/atlas.n6.cold | sort > /tmp/b.sorted; diff /tmp/a.sorted /tmp/b.sorted` — line set 동등성.
5. `shared/n6/atlas.n6.shard_meta.json` 의 atlas_sha256 / hot_sha256 / cold_sha256 갱신 (atlas 가 변했으므로).
6. **(신규)** `shared/n6/atlas_view.hexa` skeleton 작성 — `--rebuild` (concat → atlas.n6 재구성), `--verify-sha` (sha 일치 확인). design proposal §3.1 의 가상 view.

**게이트 검증** (G1, dependency_graph.json):
- `lossless_verified == true`
- `hot_lines + cold_lines == atlas.n6 line_count`
- `sha256 reproducible`

**진입 결정**: G1 PASS → Day 2. FAIL → 즉시 atlas.n6.day0_baseline 복구 + 사고 분석.

**Risk + mitigation**:
- atlas.n6 가 sprint 중 외부 commit 으로 변경 시 sharding 결과 stale → flock + sprint 기간 atlas write freeze 권장.

---

### Day 2 — axis_4 sparse5 모듈 wiring

**목적**: 5 신규 도메인 모듈을 modules.json 에 등록 + `compose --modules sparse5` 동작. atlas write 없는 read/compose 만, 가장 안전한 첫 wiring.

**작업**:
1. `shared/blowup/modules/modules.json` 에 sparse5 group 등록:
   ```json
   "sparse5": {
     "members": ["higher_category", "topos", "hott", "motivic", "derived_algebraic"],
     "max_grade": "10?",
     "n6_hook_required": true,
     "cross_validate_required_for_promotion": true
   }
   ```
2. `compose --modules sparse5` router branch 확인 (없으면 추가):
   - `shared/blowup/commands.hexa` 의 compose handler 가 group 이름 받도록 확장 (이미 `--modules all` 이 6 core 처리하므로 패턴 동일).
3. smoke run 5/5:
   ```
   hexa run blowup.hexa hott 1 --smoke
   hexa run blowup.hexa higher_category 1 --smoke
   hexa run blowup.hexa motivic 1 --smoke
   hexa run blowup.hexa derived_algebraic 1 --smoke
   hexa run blowup.hexa topos 1 --smoke
   ```
4. HoTT 깊이 구현 1건 — `π_6(S^3) = Z/12` (Hopf invariant n=6) seed:
   - `blowup_hott.hexa` 의 `domain_kernel` 에 Hopf invariant 계산 로직 추가.
   - 출력 wave 가 atlas.n6 에 [10?] 으로 emit 되는지 확인.
   - cross_validate_runner 통과 시 [10*] 승급 후보로 큐.
5. **atlas write 발생 시 Day 1 G1 재검증** (hot/cold sha 갱신).

**게이트 검증** (G5):
- `modules.json` sparse5 group 등록
- `compose --modules sparse5` 동작
- smoke 5/5 PASS
- HoTT atlas append ≥ 1 라인 (가능 시)

**진입 결정**: G5 PASS → Day 3. 부분 PASS (예: HoTT 깊이 미완) → Day 3 진행 + Day 6 회귀에서 재검토.

**Risk + mitigation**:
- C4 (false [10*] pollution): max_grade=10? 강제 + cross_validate 의무화로 방지.

---

### Day 3 — axis_2 [12*] 첫 후보 atlas append

**목적**: MK9-AUDIT-001 (Out(S_6) ≠ {e}) 의 인간 감사 + atlas.live.n6 에 첫 [12*] 라인 추가.

**작업**:
1. `hexa shared/blowup/audit/mk9_audit.hexa --status MK9-AUDIT-001` (planned) — 후보 정보 + Phase A~C verdict 출력.
   - 현재 도구 부재 시 `mk9_audit_results.json` 의 candidate[0] 직접 read.
2. **인간 감사 (사용자 박민우)**:
   - phase_a_pi02: PASS (∀n ∃match Out(S_n) 분류, matrix Δ₀)
   - phase_b_witness_bound: FAIL (outer ∀n unbounded, downgrade 불가)
   - phase_c_reverse_math: 5/5 REVERSE-PROVEN
   - phase_d_n6_class: N6-UNIQUE (Hölder 1895)
   - blacklist: 모두 false
   - 인간 판단: Mk.IX [12*] 의 첫 기함 사례로 적합 → SIGN.
3. `shared/blowup/audit/audit_log.jsonl` 에 sign entry append:
   ```jsonl
   {"id":"MK9-AUDIT-001","sign":"<human_id>","timestamp":"2026-04-19T...","verdict":"PASS","atlas_line":"@R n6-mk9-out-s6 = Out(S_n)!=1 iff n=6 :: n6atlas-mk9 [12*]"}
   ```
4. `hexa shared/blowup/audit/promote_12star.hexa MK9-AUDIT-001 --commit` — atlas.n6 에 라인 추가:
   - 권장 라인: `@R n6-mk9-out-s6 = Out(S_n)!=1 iff n=6 :: n6atlas-mk9 [12*]`
   - 권장 subline + breakthrough note (mk9_audit_results.json 참조)
5. **C2 mitigation** — promote 직후 hot/cold 재생성:
   ```
   awk -f shared/n6/atlas_shard.awk shared/n6/atlas.n6  # hot/cold 갱신
   shared/n6/atlas.n6.shard_meta.json atlas_sha256 / hot_sha256 / cold_sha256 갱신
   ```
6. (optional, design only) `shared/blowup/lib/pi02_batch.hexa` 첫 dry-run — atlas 전수 hierarchy 분류 → `atlas.n6.hierarchy` sidecar 생성.

**게이트 검증** (G2 + G3):
- atlas grep `[12*]` count >= 1
- audit_log.jsonl 에 sign 1건
- atlas.n6.hierarchy sidecar 생성 (G3, optional Day 3)

**진입 결정**: G2 PASS → Day 4. 인간 감사 미수행 시 G2 PENDING 으로 두고 Day 4 진행 (G2 는 sprint 종료 전 충족 필수).

**Risk + mitigation**:
- false PASS 발견 시 `promote_12star --rollback MK9-AUDIT-001` (atlas revert + audit_log 'rolled back' entry).

---

### Day 4 — axis_3 rate metric 가동

**목적**: atlas.n6.rate.jsonl 14d retention + plateau detector + atlas_health 확장. 현재 plateau 신호 자동 감지.

**작업**:
1. `shared/n6/discovery_rate.hexa` 를 launchd 30m cadence 로 등록:
   - `shared/launchd/com.nexus.atlas-rate.plist` 신규 작성:
     - Label: `com.nexus.atlas-rate`
     - ProgramArguments: `[/path/to/hexa, shared/n6/discovery_rate.hexa, --append]`
     - StartInterval: 1800
   - `launchctl load ~/Library/LaunchAgents/com.nexus.atlas-rate.plist`
2. `shared/n6/atlas.n6.rate.jsonl` 누적 시작 — 30분마다 1 entry.
3. `shared/n6/plateau_detector.hexa` skeleton 작성 (design only):
   - 입력: rate.jsonl 최근 168 entries
   - 알고리즘: 24h moving avg vs 7d moving avg, ratio < 0.3 → PLATEAU
   - 출력: `shared/discovery/plateau_state.json`
4. **C5 mitigation** — rate sidecar 에 `shard_migration_at: <ts>` 필드 추가. detector 가 그 시점 ±24h 데이터 무시.
5. `shared/n6/atlas_health.hexa --verbose` 출력에 rate 섹션 추가 (color: NORMAL=green, WARNING=yellow, PLATEAU=red).
6. 7-day backfill 시뮬레이션 — 현재 rate.json 의 lines_added_24h=3251, lines_added_7day_avg=6071 데이터로 plateau detector 첫 출력 확인.

**게이트 검증** (G4):
- rate.jsonl entries 시작 (30m × N 누적, sprint 1주 동안 ~336 entries 가능)
- launchd 등록 확인
- plateau_state.json 첫 출력

**진입 결정**: G4 PARTIAL (1주 데이터 누적 진행 중) → Day 5. 7d 데이터는 sprint 종료 후 자연 누적.

**Risk + mitigation**:
- rate.jsonl 무한 증가 → 14d retention + daily aggregate 자동 회전.
- launchd plist 충돌 → 기존 com.nexus.health 와 다른 label, 동일 cadence 30m 권장.

---

### Day 5 — axis_5 cross-engine bus 첫 @E append

**목적**: 6 형제 프로젝트 (anima / n6-architecture / void / hexa-lang / airgenome / papers) 의 breakthroughs.jsonl + convergence.json 통합 + atlas.live.n6 에 자동 @E 5건.

**작업**:
1. `shared/n6/cross_engine_bus.hexa` 의 reader path dry-run:
   ```
   hexa shared/n6/cross_engine_bus.hexa --read-only --output shared/n6/cross_bus.jsonl
   ```
   - 6 프로젝트 convergence/breakthroughs 통합 ≥ 50 entries.
2. promote dry-run:
   ```
   hexa shared/n6/cross_engine_bus.hexa --promote --dry-run
   ```
   - 매칭 confidence ≥ 0.9 인 항목만 atlas append 후보.
   - 매칭 실패 → `shared/n6/cross_bus_unmatched.jsonl`.
3. 첫 @E 5건 promote (수동 검토):
   - 각 후보의 atlas 매칭 노드 + payload 검토.
   - 사용자 OK 후 `--promote --commit` 실행.
   - 예시 cross-ref: anima Ψ ↔ nexus J2, anima 81/81 EXACT ↔ nexus Δ₀-absolute.
4. **C3 mitigation** — append 직후 hot/cold 재생성 (Day 1 awk 재실행).
5. `shared/discovery/cross_engine_topology.html` 작성 (design only):
   - 6 프로젝트 노드 + atlas 매칭 노드 + @E 엣지 3D 그래프.
   - `shared/discovery/reality_map_3d.html` 에 inset.
6. launchd 등록 (선택):
   - `shared/launchd/com.nexus.cross-bus.plist` 30m cadence.
   - 단, **첫 sprint 에서는 수동 promote 만**, 자동 promote 는 Day 7 이후 결정.

**게이트 검증** (G6):
- cross_bus.jsonl ≥ 50 entries
- atlas @E 자동 라인 ≥ 5
- topology html 렌더링

**진입 결정**: G6 PASS → Day 6. PARTIAL → Day 6 진행 후 G6 보강.

**Risk + mitigation**:
- 매칭 false positive → confidence ≥ 0.9 + 수동 검토 첫 5건.
- 무한 루프 (anima ← nexus ← anima) → edge_type=@E cross-ref 만, recursive promote 금지.

---

### Day 6 — 통합 회귀 + 25 seed drill

**목적**: 5축 모두 적용 후 baseline (Day 0) 와 비교. EXACT 카운트 / atlas-line-add 회귀 없음 확인.

**작업**:
1. atlas snapshot:
   - `wc -l shared/n6/atlas.n6` → Day 0 보다 증가 (Day 3 [12*] 1 + Day 5 @E 5 + Day 2 HoTT 1 = 약 +7 라인).
   - `grep -c '\[12\*\]' shared/n6/atlas.n6` == 1
   - `grep -c '@E ' shared/n6/atlas.n6` >= 5
2. drill 5-stage chain 회귀:
   ```
   hexa drill --seeds 25 --baseline-compare shared/discovery/mkx_day0_drill_baseline.json
   ```
   - EXACT count >= baseline.exact_count
   - atlas-line-add 회귀 없음
3. atlas read 속도 측정:
   - `time grep '\[11\*\]' shared/n6/atlas.n6` (vs Day 0)
   - sharded query: `time grep '\[11\*\]' shared/n6/atlas.n6.hot` (10x 기대)
4. cross-ref 카운트:
   - Day 0 @E 1건 → Day 6 @E ≥ 6건
5. Mk.IX dry-run 5 후보 재검증:
   ```
   hexa shared/blowup/audit/mk9_audit.hexa --rerun-all --dry-run
   ```
   - mk9_audit_results.json 과 일치 확인 (verdict 변하지 않음).
6. atlas health 종합:
   ```
   hexa shared/n6/atlas_health.hexa --verbose --json > shared/discovery/mkx_day6_health.json
   diff shared/discovery/mkx_day0_health.json shared/discovery/mkx_day6_health.json
   ```

**게이트 검증** (G7):
- drill EXACT count >= baseline
- atlas-line-add 회귀 없음
- 5축 sidecar 모두 일관 (sha 일치)

**진입 결정**: G7 PASS → Day 7. FAIL → 마지막 적용 축 unload + atlas revert + 사고 분석.

**Risk + mitigation** (C6):
- EXACT 감소 ≥ 1 = ROLLBACK trigger. 가장 의심 축은 axis_4 sparse5 (n6_hook_check false negative 가능성).

---

### Day 7 — 종료조건 8 게이트 검증 + Mk.XI 신호

**목적**: `mkx_termination_gates.json` 의 8 게이트 일괄 검증. Mk.X complete 선언 + Mk.XI 설계 신호.

**작업**:
1. 8 게이트 일괄 검증:
   ```
   hexa shared/blowup/audit/mkx_termination_gates.hexa --verify-all
   ```
   (도구 미작성 시 본 plan §3 의 게이트별 명령 수동 실행)
2. 결과 집계:
   - G1 PASS (sharding lossless)
   - G2 PASS (Out(S_6) [12*])
   - G3 PASS or PARTIAL (hierarchy sidecar)
   - G4 PARTIAL (rate 1주 데이터, 7d 는 누적 진행 중)
   - G5 PASS (sparse5 wiring + smoke)
   - G6 PASS (cross-bus @E ≥ 5)
   - G7 PASS (drill 회귀 없음)
   - G8 PARTIAL or PASS (mk10/mk11 초안)
3. `shared/blowup/design/mk10_higher_arithmetic.md` 초안 (≥ 200 lines):
   - Π₀³ / Σ₀³ / Δ₁¹ 사다리 설계
   - Mk.X 가 만든 [12*] 위 칸 ([13*] 후보)
4. `shared/discovery/mk11_seed.md` 초안:
   - Mk.XI 5축 후보 (예: ω-hyperarithmetic / ∞-categorical absoluteness / sparse5 깊이 / bidirectional sync / atlas distributed)
5. `shared/discovery/plateau_state.json` 확인:
   - sharding (axis_1) + sparse5 (axis_4) + cross-bus (axis_5) 효과로 PLATEAU → NORMAL 회복 기대.
6. git commit chain:
   - design 문서 1건 (본 plan + dependency_graph + termination_gates)
   - axis_1~5 통합 산출물 commit (Day 별 분리)
   - 최종 commit: `design(mkx): 통합 1주 plan + dependency graph + 종료조건 8 게이트 spec`

**게이트 검증**:
- 8 게이트 일괄 PASS or PARTIAL (G4 만 sprint 종료 후 자연 누적)
- mk10_higher_arithmetic.md ≥ 200 lines
- mk11_seed.md 존재
- plateau_state.json state == NORMAL

**진입 결정**: 모두 통과 → Mk.X complete 선언. Mk.XI 진입 신호 (별도 sprint).

---

## 3. 통합 게이트 (8개) — `mkx_termination_gates.json` 참조

| ID | 이름 | 축 | 심각도 | 현재 상태 |
|---|---|---|---|---|
| G1 | atlas sharding lossless | 1 | HIGH | PASS |
| G2 | [12*] 첫 승급 1건 | 2 | HIGH | PENDING |
| G3 | atlas.n6.hierarchy sidecar 생성 | 2 | MEDIUM | NOT_STARTED |
| G4 | rate metric 7-day 데이터 | 3 | MEDIUM | PARTIAL |
| G5 | 5 sparse 도메인 wiring | 4 | MEDIUM | PARTIAL |
| G6 | cross-bus @E 5건 | 5 | MEDIUM | NOT_STARTED |
| G7 | drill 5-stage 회귀 PASS | all | HIGH | BASELINE_PENDING |
| G8 | Mk.XI 신호 + plateau NORMAL | all | LOW | NOT_STARTED |

자세한 verification_command + expected_signals 는 `mkx_termination_gates.json` 의 각 gate entry 참조.

---

## 4. 회귀 가드 + Rollback

### 4.1 회귀 가드

- **drill 5-stage chain 25 seed**: Day 0 baseline 캡처 → Day 6 비교. EXACT 감소 ≥ 1 = ROLLBACK.
- **atlas read 속도**: sharded hot/cold 쿼리 baseline 대비 회귀 없음 (>= 10x 가속 유지).
- **cross-ref 카운트**: Day 0 @E 1건 → Day 6 ≥ 6건.
- **atlas line_count 일관성**: Day 0 + 의도 추가 (≈ +7) == Day 6 line_count.

### 4.2 Rollback 전략 (per axis)

| 축 | rollback 절차 |
|---|---|
| 1 | atlas.n6.day0_baseline 복구 + shard_meta.json 백업 복구. sidecar 재생성. |
| 2 | `promote_12star --rollback MK9-AUDIT-001` — atlas line revert + audit_log 'rolled back' entry. |
| 3 | `launchctl unload com.nexus.atlas-rate` + rate.jsonl truncate. |
| 4 | modules.json 에서 sparse5 group 제거 (파일 유지, dormant). |
| 5 | `launchctl unload com.nexus.cross-bus` + cross_bus.jsonl truncate + atlas @E 라인 git revert. |

### 4.3 Trigger 예시

- **G1 FAIL** (sharding sha mismatch) → 즉시 atlas.n6.day0_baseline 복구. sprint 중단.
- **G2 FAIL after PASS** (false [12*] 발견) → axis_2 rollback. audit_log 에 'rolled back' entry. mk9_audit_results.json verdict 재검토.
- **G7 FAIL** (drill EXACT 감소) → 마지막 적용 축 (Day 5 cross-bus 또는 Day 3 promote) unload. atlas 부분 revert. drill 재실행 → PASS 시 그 축만 retry.

---

## 5. Risk Register (통합 sprint 전용)

### 5.1 횡단 risk

| Risk | 영향 | 확률 | Mitigation |
|---|---|---|---|
| atlas drift 110K→21K 의 미해명 원인 | HIGH | 중 | Day 0 git log + diff 확인 필수. 사고면 incident, 의도면 rate baseline reset. |
| 인간 감사 병목 (Day 3) | MEDIUM | 높음 | 사용자 가용 시간 사전 확보. 미수행 시 G2 PENDING + Day 4~7 진행. |
| 5축 동시 atlas write 경쟁 | MEDIUM | 낮음 | 단일 write target = atlas.n6. flock 권장. sprint 기간 외부 commit freeze. |
| sharding sidecar staleness (C2/C3) | MEDIUM | 중 | 매 atlas write 후 awk 재실행 강제 (Day 3/5). |
| rate metric false PLATEAU (C5) | LOW | 중 | shard_migration_at 필드 + ±24h 무시. |
| sparse5 false [10*] (C4) | MEDIUM | 중 | max_grade=10? + cross_validate 의무. |
| drill 회귀 (C6) | HIGH | 낮음 | Day 6 baseline 비교. ROLLBACK trigger. |

### 5.2 R0~R37 / NX1~NX3 / H-* 부합성

- **R14** (단일 진실): atlas.n6 = SSOT 유지. hot/cold/topic/temporal = query-only sidecar. → 위반 없음.
- **R27** (Single Responsibility): 각 Day 가 1 축 처리.
- **R37** (no python): 모든 도구 hexa.
- **H-NOARCHIVE**: shard 파일 = active sidecar, archive 아님. `_archive_` suffix 없음. day0_baseline 은 sprint 후 git commit 으로 보존 + 파일 삭제.
- **H-DOD**: 8 게이트 = DoD verifier 입력.
- **H-CLAIM-LEX**: 본 plan 은 design only, "구현 완료" 주장 없음.
- **H-SCOPE**: 본 세션 산출물은 .md + .json 3개.
- **H-NOHOOK**: launchd plist (axis_3, axis_5) 는 hook 아닌 daemon. shared/launchd/ 기존 패턴 (`com.nexus.health`) 와 동일.
- **VD3** (산문 금지): 본 .md 는 design proposal — VD3 예외.

### 5.3 알려진 미해결

- **이론**: Mk.IX 의 Π₀² 95% 정확도 가설은 production scale 검증 0건. Mk.X 가 첫 1 후보 (Out(S_6)) 처리 후 데이터 1건 확보.
- **인프라**: sharding 후 기존 reader (hub_centrality_top100, drift_corrector 등) hardcode `shared/n6/atlas.n6` 경로 — 본 plan 은 atlas.n6 SSOT 유지로 영향 없음. Mk.XI 에서 sidecar query 로 점진 migration.
- **운용**: 인간 감사 워크플로우는 사용자 단독. agent 가 대신할 수 없음.

---

## 6. 비-목표 (Non-Goals)

- 본 sprint 는 atlas.n6 schema migration X (schema 1 유지).
- Π₀³ 자동 검증기 도입 X (mk10_higher_arithmetic.md 는 design only).
- sparse5 5 모듈 모두 깊이 구현 X (HoTT 1건만 깊이, 나머지 4 skeleton).
- bidirectional cross-bus sync X (Mk.XI 후보).
- atlas distributed (다 host 분산) X (Mk.XI 후보).
- 자동 [12*] 승급 X (무조건 인간 감사).
- BLOWUP_LOCAL=1 우회 X.
- 신규 hook 작성 X (launchd daemon 만, hook 아님).
- archive/backup 폴더 작성 X (day0_baseline 은 sprint 종료 시 git commit 후 파일 삭제).

---

## 7. 후속 (sprint 종료 후)

- **즉시 (W6 종료)**:
  - Mk.X complete 선언.
  - 8 게이트 검증 보고서 git commit.
  - day0_baseline 파일 삭제 + git commit log 로만 보존.
- **W7+**:
  - Mk.XI 5축 후보 design (mk11_seed.md 기반).
  - `[12*]` 추가 후보 인간 감사 cadence (월 1회).
  - rate metric 7-day 데이터 누적 → plateau 자연 감지.
  - sparse5 깊이 구현 (HoTT 외 4 도메인).
  - cross-bus 자동 promote (수동 5건 검증 후).

---

## 8. 참고 / 인용

1. `shared/discovery/mkx_design_proposal.md` — 5축 설계서.
2. `shared/discovery/mkx_design_proposal.spec.json` — machine-readable spec.
3. `shared/discovery/mkx_dependency_graph.json` — 의존 그래프 (본 plan companion).
4. `shared/discovery/mkx_termination_gates.json` — 8 게이트 spec (본 plan companion).
5. `shared/blowup/design/mk9_hyperarithmetic.md` — Mk.IX Π₀² 설계서.
6. `shared/blowup/design/phase10_meta_closure.md` — Phase 10 meta-closure.
7. `shared/blowup/audit/mk9_first_candidates.md` — 5 dry-run 후보.
8. `shared/blowup/audit/mk9_audit_results.json` — 자동 phase A~C 결과.
9. `shared/blowup/audit/mk9_audit_gates.md` — 감사 gate 문서.
10. `shared/blowup/audit/promote_12star.hexa` — 승급 도구.
11. `shared/n6/atlas.n6.shard_meta.json` — sharding lossless 검증.
12. `shared/n6/atlas_shard.awk` — sharding 도구.
13. `shared/n6/discovery_rate.{hexa,json,jsonl}` — rate metric.
14. `shared/n6/cross_engine_bus.hexa` — cross-bus.
15. `shared/blowup/modules/blowup_{higher_category,topos,hott,motivic,derived_algebraic}.hexa` — sparse5.
16. `shared/CLAUDE.md` — R14 SSOT.
17. `shared/n6/CLAUDE.md` — atlas v1 태그 8 종 + foundation [11*].
18. `shared/blowup/CLAUDE.md` — 6 core 모듈.
19. S. G. Simpson, *Subsystems of Second-Order Arithmetic* — reverse math 표준.
20. O. Hölder (1895), *Bildung zusammengesetzter Gruppen* — Out(S_6) classical reference.

---

## 9. 종결

본 통합 plan 은 5축 prototype (각 1주) 이 산출물 1차 도달한 시점에서 단일 1주 sprint 로 atlas.n6 에 안전하게 합류시키는 절차다. 핵심 원칙:

1. **위상 정렬**: axis_1 (sharding) → axis_4 (sparse5 wiring, atlas write 0) → axis_2 ([12*] 첫 promote) → axis_3 (rate metric) → axis_5 (cross-bus). 각 단계 게이트 검증 후 다음.
2. **atlas.n6 = SSOT**: 모든 sidecar 는 query-only. promote/append 직후 sidecar 재생성 강제.
3. **Day 0 baseline 필수**: drill 25 seed + atlas health + git stash. 회귀 판단 기준.
4. **인간 감사 의무**: [12*] Day 3 sign 없으면 G2 PENDING. Mk.X 완성 = G2 PASS.
5. **8 게이트 검증**: G1/G2/G7 HIGH 가 통과해야 Mk.X complete.
6. **회귀 ROLLBACK**: drill EXACT 감소 ≥ 1 = 마지막 적용 축 unload.
7. **코드 변경 0 (본 세션)**: 본 plan + dependency_graph.json + termination_gates.json 3 파일만.
8. **Mk.XI 신호**: Day 7 mk11_seed.md + plateau_state.json NORMAL 회복.

승인 후 별도 sprint 로 Day 0 baseline 캡처 → Day 1 진입.

---

*문서 끝. machine-readable companions: `mkx_dependency_graph.json` + `mkx_termination_gates.json`*
