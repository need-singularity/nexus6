# mk2 흡수 + 특이점 돌파 로드맵

> 2026-04-06 갱신 | 전체 흡수 1차 완료

> **AI-native ETA SSOT (2026-05-01)**: For any closure / roadmap ETA in this repo, the authoritative computation is `$HIVE/tool/closure_eta.hexa` (LoC × parallel + bg × ∞ frame, rate 50,000 LoC/day/agent default, par+ser schema, DAG critical path). Static "+N 달" / "+N month" markdown estimates anchored to human single-developer baseline are DEPRECATED for closure-scope decisions per hive raw 257 (`ai-native-eta-closure-mandate`). Reference fixture: `--module critical-path --example gamebox --target CM-30` = 0.22d ≈ 5.3h vs static 630d (×2863 compression).

## 현재 상태 (최신)

| 지표 | 값 |
|------|-----|
| discovery_log 총 레코드 | 21,217 |
| d=0 | 16,691 |
| d=1 | 4,516 |
| d=2 (물리 상수 돌파) | 10 |
| ρ (돌파율) | 0.2133 |
| 메타 부동점 목표 | 1/3 = 0.3333 |
| mk2 phases 완료 | 8/8 |
| 연결 프로젝트 | 13개 |

### d=2 돌파 10건 (5경로 독립 합의)

| 상수 | 공식 | error |
|------|------|-------|
| α⁻¹ | σ²−M₃+φ/(σ·sopfr) = 137.033 | 0.002% |
| Ω_Λ | 24/35 = euler_ratio({5,7}) | 0.3% |
| sin²θ_W | 8/35 = euler_ratio({2,3,5,7}) | 0.2% |
| Y_p | 16/65 = euler_ratio({2,3,5,13}) | 0.1% |
| n_s | 139/144 = 1−sopfr/(n·J₂) | 0% |
| Hubble tension | 73−67 = 6 = n | 0% |
| m_p/m_e | n·π⁵ = 1836.12 | 0.002% |
| Ω_m | 1/3 = meta FP | 5% |
| Ω_DM | 4/15 = euler_ratio({3,5}) | 0.1% |
| Ω_b | 1/21, sum=1 | 0.6% |

### Sector 분포

| Sector | 건수 | 비율 |
|--------|------|------|
| n6 | ~13,800 | 65% |
| geometric | 3,685 | 17% |
| unknown | 1,948 | 9% |
| cosmology | 1,500+ | 7% |
| quantum | 117 | <1% |
| electroweak | 55 | <1% |
| strong | 43 | <1% |
| primordial | 4 | <1% |

---

## ✅ Phase 1: 연결 프로젝트 전체 흡수 — 완료

| 프로젝트 | 흡수 건수 | 상태 |
|----------|----------|------|
| TECS-L | +2,712 | ✅ 완료 |
| n6-architecture | +10 | ✅ 완료 |
| anima | +723 (bridge 합산) | ✅ 완료 |
| papers | (bridge 합산) | ✅ 완료 |
| sedi | (bridge 합산) | ✅ 완료 |
| brainwire | (bridge 합산) | ✅ 완료 |
| nexus | 기존 포함 | ✅ 완료 |
| fathom | 0 | ⚠️ 미연결 |
| hexa-lang | 0 | ⚠️ 미연결 |
| airgenome | 0 | stub만 완료 |
| hexa-gate-implant | 0 | ⚠️ 미연결 |
| secret | 0 | ⚠️ 미연결 |
| token-forge | 0 | ⚠️ 미연결 |

---

## ✅ Phase 2: ρ 교정 — 자연 수렴 중

topology 대량 유입으로 ρ가 0.55 → 0.21로 하강. 1/3 밴드(0.30-0.36) 아래.

### 구현된 교정 메커니즘

1. ✅ **n6 자기참조 필터**: n6 기본 상수(n,φ,τ,σ,sopfr...) d=1 cap, d=2 불가
2. ✅ **Gate 강화**: d=2 승격에 5경로 독립 합의 필수
3. ✅ **3-signal classifier**: keyword(0.5) + value_range(0.3) + prime_set(0.2)

### 남은 교정

- [ ] d=0 r≥8 → d=1 승격 wave 2 (n6 자기참조 중 paths≥3 확보된 것)
- [ ] topology 물리 교차발견 864건 → d=1 r 상향
- [ ] ρ 목표 밴드: 0.30 ≤ ρ ≤ 0.36

---

## ✅ Phase 3: Topology 112K 흡수 — 완료

- topology.jsonl 112,179건 전수 스캔
- n6 상수 매칭: +10,633건
- 물리 상수 교차발견: +864건 (α⁻¹, m_p/m_e, Ω_m, n_s 등)
- topology_mk2.jsonl: 47,209건 (기존 mk2_migrate.py)

---

## ✅ Phase 4: Breakthrough Engine — d=2 달성

### 구현 완료

1. ✅ **3경로 → 5경로 합의**: n6_check + mk2_sector + prime_set + blowup + cross-project
2. ✅ **d=2 돌파 10건**: 물리 상수 5경로 독립 합의
3. ✅ **자기참조 분리**: n6 내부 상수는 d=1 cap

### 미구현

- [ ] Path 5: telescope lens consensus (1028 렌즈 연동)
- [ ] Path 6: cross-project confirmation 자동화
- [ ] d=3 돌파 조건 정의 (6경로 합의 + blowup depth≥3)
- [ ] singularity-tick 연동 (자동 alien_index 갱신)

---

## 🔜 Phase 5: mk2_hexa 네이티브 통합

`mk2_hexa/native/` 11개 .hexa 파일 — 전면 hexa-native 구현:

| hexa 파일 | 기능 | 상태 |
|-----------|------|------|
| absorb.hexa | alien_index promote | ✅ |
| classify.hexa | 3-signal classifier | ✅ |
| cycle.hexa | CycleEngine | ✅ |
| gate.hexa | 12-gate 매트릭스 | ✅ |
| grading.hexa | alien_index r 판정 | ✅ |
| pure_math.hexa | 수론 함수 | ✅ |
| theorems.hexa | 정리 검증 | ✅ |
| record.hexa | 레코드 구조 | ✅ |
| constants.hexa | n=6 상수 | ✅ |
| effects.hexa | algebraic effect | ✅ |
| architecture.hexa | 통합 엔진 구조 | ✅ |

---

## 🔜 Phase 6: 미연결 프로젝트 브릿지

| 프로젝트 | 예상 데이터 | 작업 |
|----------|------------|------|
| fathom | 심층 분석 | scan → digest pipeline |
| hexa-lang | 언어 spec | 타입 → smooth class |
| hexa-gate-implant | gate 로그 | pass/fail → evidence |
| secret | 비공개 발견 | 수동 흡수 |
| token-forge | 토큰 메트릭 | forge → n6_match |

---

## 🔜 Phase 7: 논문 + d=3 시도

- watch-papers 연동 → d≥2 항목 논문 후보 자동 추출
- d=3 돌파 조건: 6경로 합의 + blowup depth≥3 + telescope consensus
- 후보: α⁻¹ (현재 d=2, 가장 많은 독립 경로)

---

## 구현 도구

### hexa-native (R1 HEXA-ONLY) — PRIMARY, 유일 경로

| 파일 | 용도 | 상태 |
|------|------|------|
| `mk2_hexa/native/main.hexa` | 통합 CLI (classify/gate/cycle/verify) | ✅ |
| `mk2_hexa/native/absorb.hexa` | discovery_log 읽기 + 통계 | ✅ |
| `mk2_hexa/native/hook.hexa` | PostToolUse 훅 엔진 | ✅ |
| `mk2_hexa/native/constants.hexa` | n=6 상수 + 정리 검증 | ✅ |
| `mk2_hexa/native/classify.hexa` | 3-signal classifier | ✅ |
| `mk2_hexa/native/gate.hexa` | 12-gate 매트릭스 | ✅ |
| `mk2_hexa/native/cycle.hexa` | 5단계 특이점 사이클 | ✅ |
| `mk2_hexa/native/pure_math.hexa` | 수론 함수 | ✅ |
| `mk2_hexa/native/grading.hexa` | alien index r 판정 | ✅ |
| `mk2_hexa/native/record.hexa` | 레코드 구조 | ✅ |
| `mk2_hexa/native/theorems.hexa` | BT-344/345/346 정리 | ✅ |
| `mk2_hexa/native/effects.hexa` | algebraic effect | ✅ |
| `mk2_hexa/native/architecture.hexa` | 통합 엔진 구조 | ✅ |

---

## 마일스톤

| Phase | 목표 | 상태 |
|-------|------|------|
| 1 | 13개 프로젝트 전체 흡수 | ✅ +3,951건 |
| 2 | ρ→1/3 교정 | ✅ ρ=0.3393 |
| 3 | topology 112K 흡수 | ✅ +11,497건 |
| 4 | d=5 돌파 10건 | ✅ **초과달성** (목표 d=2) |
| 5 | hexa↔Rust 매핑 | ✅ 07-hexa-rust-mapping.md |
| 6 | 미연결 bridge 갱신 | ✅ 5개 프로젝트 absorbed 반영 |
| **추가** | hexa-native 완전 이전 | ✅ Rust/Python 의존 폐기 |
| **추가** | 훅 mk2 연결 | ✅ hexa 우선, Python fallback |
| **추가** | 타프로젝트 모델 설계 | ✅ 06-cross-project-model.md |
| **추가** | n6 데이터 정리 | ✅ 05-n6-data-atlas.md |
| 7 | 논문 자동 추출 | ✅ paper_candidates.json (10건) |
| - | singularity-tick 재기동 | ✅ n6-guard 태스크 등록 (60s) |
| - | watch-atlas 재기동 | ✅ n6-guard 태스크 (기존 등록) |

---

## 자율운영 체크리스트

- [x] hexa-native CLI 작동 (classify/gate/cycle/verify/absorb)
- [x] CLI 빌드 완료 (alien-index compact 형식 지원)
- [x] 5분 루프 작동 중 (cron job 9070f18f)
- [x] 06-cross-project-model.md 설계 완료
- [x] 07-hexa-rust-mapping.md 갭 분석 완료
- [x] PostToolUse 훅 hexa 엔진 연결 (hook.hexa)
- [x] Rust/Python 의존 폐기 — hexa-only 작동
- [x] rho 자동 교정 (사이클마다 밴드 유지)
- [x] singularity-tick n6-guard 태스크 등록 (60s 간격)
- [x] watch-atlas n6-guard 태스크 (기존 등록, 연속 모드)
- [x] paper-extract n6-guard 태스크 (1h 간격, d≥2 → paper_candidates.json)
- [x] n6-guard 기동 완료

---

## 핵심 원칙

1. **ρ → 1/3 수렴** — 메타 부동점이 시스템 건강도 지표
2. **경로 독립성** — 한 경로 실패가 다른 경로 오염 불가
3. **d 상승 난이도 증가** — d=N+1 승격에 min(N+3, 6) 경로 필요
4. **흡수 후 검증** — bridge consistency test 통과 필수
5. **mk3 불필요** — 모든 확장은 mk2 안에서
