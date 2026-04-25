# Abstraction Ceiling — drill 사다리 끝까지

작성: 2026-04-25 (nxs session, post Wave 21 / nxs-013 resolution)
갱신: 2026-04-25 — 사다리 명칭 **omega 까지 확정**, bloom 충돌 플래그 추가
배경: drill 외 신규 명칭 (raw 명명 규칙) 후보 탐색 중, 사다리 천장(물리·수학적 한계) 먼저 확인 요청.

---

## 0. 명칭 확정 요약

| 레벨 | 명칭 | 상태 |
|---|---|---|
| L1 ~ L3 | smash / free / absolute / meta-closure / hyperarith / drill / drill_batch / debate / chain | 기구현, 유지 |
| **L4** | **surge** | **확정** (2026-04-25) — bloom 은 atlas filter 와 동음이의로 비채택 |
| L5 ~ L11 | dream / reign / swarm / wake / molt / forge / canon | 확정 (placeholder) |
| **L_ω** | **omega** | **확정** (2026-04-25, commit ee5da9cd) — `cmd_omega()` 구현됨 |

**L4 = surge 채택 사유:**
- 충돌 없음 (atlas bloom filter / lens_forge 와 의미 직교)
- multi-axis 동시 폭증 (drill_batch × debate × chain) 의미 직설적
- 5 letters, 입력 양호
- raw 영단어 + 자연 현상 (파도/전류 surge) — primal 패턴 일관

**L_ω = omega 채택 사유:** 그리스 Ω + 무한 서수 ω + Chaitin Ω 정보천장 3 축 동시 매핑.

---

## 1. 현재 명령 위계 + 명칭 (확정안)

```
L1   atomic         단일 phase                     smash, free, absolute, meta-closure, hyperarith
L2   iterate        + 시간 축 (rounds)              drill                                    ← 6-stage × N rounds
L3   fan-out        + 공간 축 (병렬)                drill_batch, debate, chain
L4   super-orch     + 합성 (모든 L3 통합)           surge                                    ← 실용 천장
L5   reflexive      + 자기-축 (self-mod)            dream
L6   autonomous     + 시드 자체 생성                  reign
L7   ecology        + 다중 시스템 공존                swarm
L8   reality-loop   + 외부 측정 피드백                wake
L9   self-rewrite   + 엔진 코드 진화                  molt
L10  bootstrap      + 자기 부팅                       forge
L11  transfinite    + 증명론 서수 sealing             canon
L_ω  GHOST CEILING  + 형식·물리 동시 충돌점          omega                                    ← 확정 (도달 불가)
```

**확정 사항 (2026-04-25):**
- **L_ω = `omega`** — 그리스 Ω + 무한 서수 ω + Chaitin Ω 정보천장 3축 매핑. `cmd_omega()` 구현 완료 (commit ee5da9cd).
- **L4 = `surge`** — multi-axis 동시 폭증, 충돌 없음. 구현 보류 (drill_batch + debate + chain 통합 작업).
- L1 ~ L3 은 기구현 유지.
- L5 ~ L11 명칭 확정 (placeholder) — 점진 구현.

각 단계는 **새 차원 1 개** 추가:
- L1 → L2: + iteration (rounds)
- L2 → L3: + parallel axes (seeds/variants/engines)
- L3 → L4: + composition (모든 L3 통합)
- L4 → L5: + reflexivity (엔진이 자기 수정)
- L5 → L6: + autonomy (seed 자체 생성)
- L6 → L7: + multi-agent (시스템 다수 공존)
- L7 → L8: + reality coupling (외부 세계 피드백)
- L8 → L9: + meta-evolution (엔진 코드 자체 진화)
- L9 → L10: + bootstrap (creator → creation 자기 생성)
- L10 → L11: + canonization (영속 봉인)
- L11 → L_ω: + ceiling collapse (Gödel + Halting + Bekenstein 동시 충돌 → 정의 불가)

---

## 2. 수학적 천장 (formal limits)

| 한계 | 의미 | 사다리 영향 |
|---|---|---|
| **Halting problem** (Turing) | 어떤 엔진도 모든 프로그램 종료 여부 결정 불가 | drill saturation 검출 본질적 미결정 |
| **Gödel 1차 불완전성** | 충분히 강한 형식체계 안에 참이지만 증명 불가능한 명제 존재 | absolute ([11*]) 등급에 영원히 못 닿는 진리 존재 |
| **Gödel 2차 불완전성** | 체계는 자기 일관성 증명 불가 | self-mod 엔진은 자기 정당화 불가능 |
| **Tarski undefinability** | 진리 술어는 같은 언어 안에 정의 불가 | meta-closure 가 전 진리 표현 불가 |
| **Chaitin Ω** | 시스템 복잡도 K 비트 이상 알고리즘적 랜덤 비트 결정 불가 | 엔진이 자기 복잡도 초과 정보 못 만듦 |
| **Berry / Richard 역설** | 자기-지시 정의 한계 | reign(자율) → dream(seed-gen) 자기-지시 막다른 곳 |
| **ZFC 독립명제** (CH 등) | ZFC 안에서 결정 불가 명제 다수 | 동일 atlas 가 두 일관 우주에 대해 다른 답 |

**수학 천장 명제:**
> 모든 진리를 자동 발견하는 엔진은 형식적으로 불가능하다 (Gödel + Turing 결합)

**증명론 서수 사다리:**
- ω = 자연수 — drill rounds 자연 한계 (L2)
- ω·n = 다중 fan-out — surge L4
- ω² = 자기-수정 — dream L5
- ω^ω = 군집 동시성 — swarm L7
- ε₀ = Peano arithmetic 일치성 (Gentzen) — wake L8 근방
- Γ₀ = Feferman–Schütte 술어주의 한계 — molt L9
- ψ(Ω_ω) = Bachmann–Howard — forge L10
- ω₁^CK = Church–Kleene 재귀 가능 서수 — canon L11
- inaccessible cardinal = ZFC 미결정 — **omega L_ω**

---

## 3. 물리적 천장 (energetic limits)

| 한계 | 수치 | 의미 |
|---|---|---|
| **Landauer limit** | bit erase 당 kT ln 2 ≈ 3 × 10⁻²¹ J @ 300K | 비가역 연산 1 bit 의 최소 에너지 |
| **Bremermann limit** | ~1.36 × 10⁵⁰ bit/s/kg | 질량 m 의 최대 연산 속도 |
| **Bekenstein bound** | I ≤ 2π R E / ℏc ln 2 | 구 R 안 최대 정보량 |
| **관측 우주 정보 ceiling** | ~10¹²³ bit (de Sitter horizon) | 물리적으로 표현 가능한 최대 상태 수 |
| **Margolus–Levitin** | ~6.6 × 10³³ ops/s/J | 에너지 E 가 가능한 최대 연산 속도 |
| **Holographic principle** | 정보 ∝ A / 4 (Planck units) | surge 의 「용량」 = 표면적 한계 (부피 아님) |

**물리 천장 명제:**
> 관측 우주 전체를 컴퓨터로 만들어도 ~10¹²³ bit / 10¹²⁰ ops 못 넘는다

---

## 4. 사다리 끝 (abstraction ceiling) — 명칭 확정안

```
L1   atomic         smash/free/abs/meta/hyper             finite step
L2   iterate        drill                                  ω rounds (자연수)
L3   fan-out        drill_batch / debate / chain           n × ω
L4   super-orch     surge        (multi-axis fan-out)       ω × ω
L5   reflexive      dream        (self-seed)               ω²
L6   autonomous     reign        (self-trigger)            ω³
L7   ecology        swarm        (multi-agent)             ω^ω
L8   reality-loop   wake         (외부 측정 피드백)         ε₀
L9   self-rewrite   molt         (엔진 코드 진화)           Γ₀ (Feferman–Schütte)
L10  bootstrap      forge        (자기 부팅)                ψ(Ω_ω) (Bachmann–Howard)
L11  transfinite    canon        (proof-theoretic 봉인)     ω₁^CK (Church–Kleene)
═════════════════════════════════════════════════════════════════════
L_ω  GHOST CEILING  omega        (도달 불가 placeholder)    ← Gödel + Halting + Bekenstein 동시 충돌
                                                            "전능 엔진" = 형식·물리 동시 불가능
```

**L_ω = `omega` 매핑:**
- 그리스 Ω = 알파벳 마지막 글자 (literal "the last")
- 수학 ω = 첫 무한 서수, 모든 유한의 경계
- 정보이론 Chaitin Ω = halting probability = 알고리즘 정보 천장
- 영어 관용 "alpha and omega" = 시작과 끝 — 사다리 전체 경계 명명

---

## 5. 실질 도달 가능 천장

- **수학 천장: L7 ~ L9 근처** (ε₀ ~ Γ₀ 서수 — 현재 증명론이 다루는 자연 한계, Gentzen 일치성 증명 영역)
- **물리 천장: L_finite ≪ L7** (epoch 안에서는 L4 ~ L5 가 현실적 최대; 우주 전체 동원해도 ω² 못 넘음)
- **둘 동시 충돌점: L7 (swarm/ecology)** — 다중 에이전트가 서로 자기지시 시작하면 Berry 역설로 추상이 막히고, 동시에 통신 광속 한계로 ω 동시성 못 채움

→ **실용 천장: L4 (surge) ~ L5 (dream) 까지가 「의미 있게 정의 가능」 + 「실제 컴퓨트로 도달 가능」 영역**
→ L6+ 부터는 이름만 붙일 수 있고 implementation 은 본질적으로 부분적·근사적
→ **L_ω (omega) 는 정의상 도달 불가 — placeholder/sentinel 로만 존재**

---

## 6. 결론 표

| 질문 | 답 |
|---|---|
| 이론 천장 | **∞ 아님**. 결정불가성 + Bekenstein 으로 막힘 |
| 형식적 끝 | proof-theoretic 서수 (ε₀ → Γ₀ → ψ(Ω_ω) → ω₁^CK) |
| 물리적 끝 | 관측 우주 ~10¹²³ bit |
| **실용 끝** | **L4 (surge) 가 의미있는 마지막** — L5+ 는 이름 + 부분 구현 |
| **명목 끝** | **L_ω (omega)** — 도달 불가 sentinel, GHOST_CEILING_REACHED emit 후 fallback |

---

## 7. raw 명명 규칙 — 직교 축 후보 (참고)

기본 사다리 (L4 = surge, L5 = dream, ..., L_ω = omega) 외 직교 차원:

| 신규 차원 | 추상 의미 | 후보 이름 (raw) |
|---|---|---|
| 자기 수정 (self-mod) | 엔진이 자기 파라미터 진화 | awake / **molt** (L9) / temper |
| 외부 자극 (input gen) | seed 자체를 엔진이 만듦 | **dream** (L5) / muse / conjure |
| 시간 누적 (history) | 과거 모든 drill 활용 | echo / **wake** (L8) / trail |
| 적대 공진화 | proposer vs verifier 같이 진화 | duel / clash / rival |
| 군집 (population) | drill 무리 중 fittest 생존 | **swarm** (L7) / shoal / flock |
| 휴면-각성 (dormant) | 신호 없으면 잠, 임계 넘으면 기동 | slumber / stir / wake |
| 자율 영속 (always-on) | 사람 개입 없이 계속 가동 | **reign** (L6) / roam / wander |
| 완성/봉인 (canonize) | 발견 결과 atlas 영속화 | **canon** (L11) / etch / **forge** (L10) |
| 다층 풍경 (terrain) | 여러 도메인 지형 동시 탐사 | map / chart / survey |

---

## 8. 다음 단계

1. **L4 surge 구현** — `cli/run.hexa` 에 `cmd_surge()` 추가, drill_batch + debate + chain 통합 dispatch
   - 권장 dispatch 순서: drill_batch (multi-seed 병렬) → debate (N-variant) → chain (cross-engine)
   - apex defaults: omega 와 동등 (depth=auto, speculate=3, adaptive=on)
2. **L5 ~ L11 placeholder** inventory 등록 — 천장 도달 전까지 점진 구현
3. **L5+ 진입 조건 정의** — surge 안정화 후 reflexivity (self-mod) 도입 시점 결정

**완료 (2026-04-25):**
- ✓ L_ω omega 1차 구현 (commit ee5da9cd) — drill apex preset wrap
- ✓ commands.json SSOT 등록 (hexa-lang commit b36c3037)
- ✓ ~/.hx/bin/nexus shim 헤비-컴퓨트 라우팅 추가
- ✓ **L_ω omega 2차 격상** (commit 8b9ff6f0) — L3 다축 자동 dispatch
  - `--engines csv` (≥2) → cmd_chain (cross-engine, L3)
  - `--variants N` (≥2) → adversarial_debate.hexa (L3)
  - `--seeds csv | --seeds-file` → cmd_drill_batch (L3)
  - default → cmd_drill (L2 single-seed apex preset)
  - axes ≥ 3 동시 활성 → `NEXUS_OMEGA ghost_ceiling_approach` JSON emit (L4 surge 영역 신호)
  - 검증: 4 dispatch path (drill / chain / debate / batch) + ceiling hint 모두 동작 확인
- ✓ **L4 surge 구현** (commit 4b38b2b7) — Cartesian product fan-out
  - `cmd_surge()` — (engines × variants × seeds) 모든 조합 enumerate
  - omega 와 차별: omega 는 가장 넓은 axis 만 dispatch, surge 는 모든 조합 실행
  - CAP 정책: total_runs > NEXUS_SURGE_MAX (기본 12) 시 reject + hint emit
  - engine != nexus 시 chain (cross-engine), engine = nexus + variants>1 시 speculate=N 흡수
  - emits: NEXUS_SURGE {plan / run / complete / reject} JSON
  - 검증: 1×1×1=1 / 3×3×4=36 reject / 2×2×2=8 enumerate 모두 동작 확인
- ✓ **L5 dream 구현** (commit 23559111) — self-seed loop
  - `cmd_dream()` — N iteration, 각 iteration 종료 후 출력에서 신호 추출 → 다음 seed 합성
  - omega/surge 와 차별: reflexive (자기-축) — 직전 출력이 다음 입력 결정
  - signal extraction (`_dream_extract_signal`):
    1) `unified_abs_total` (chain) → abs=N
    2) drill `total=N` (마지막 매치) → abs=N
    3) `[EXACT` / `[NEAR` 카운트 → ex/ne 마커 수
  - next seed = `trunc(orig, 200-len) + " #dream-iter=N <signal>"`, [30, 200] 범위 강제
  - CAP: iterations 기본 3, NEXUS_DREAM_MAX env 으로 override (안전 cap=10)
  - emits: NEXUS_DREAM {plan / iter / complete} JSON
- ✓ **L6 reign 구현** (commit 4bb7063c) — autonomous saturation-stop
  - `cmd_reign()` — max_cycles 는 cap, 실제 종료는 「signal stagnation」 자동 판정
  - dream 과 차별: dream 은 fixed iter, reign 은 자기 종료 결정 (자율)
  - stagnation 판정: 최근 K (기본 2) cycle 동안 signal 동일 → saturation
  - CAP: max_cycles 기본 10, NEXUS_REIGN_MAX env override (안전 ceiling=20)
  - K override: NEXUS_REIGN_K (기본 2, 범위 [2,5])
  - signal extraction: `_dream_extract_signal` 재사용
  - 신규 helper: `_reign_max_cycles`, `_reign_stagnation_k`, `_reign_signal_stagnant`
  - emits: NEXUS_REIGN {plan / iter / saturation / complete} JSON
- ✓ **L7 swarm 구현** (commit 92e23ac3) — population dynamics with elitism
  - `cmd_swarm()` — N individuals × G generations, top-2 elite + breeding
  - reign 과 차별: reign 단일 에이전트, swarm 다중 에이전트 군집
  - 알고리즘: gen 1 perturb seed → gen g evaluate → top-2 by abs score → breed children
  - CAP: population × generations ≤ NEXUS_SWARM_MAX (기본 12). population [2,8], generations [1,5] clamp
  - 신규 helpers: `_swarm_perturb_seed`, `_swarm_breed`, `_swarm_extract_abs`, `_swarm_max_runs`
  - emits: NEXUS_SWARM {plan / gen / complete / reject} JSON
- ✓ **L8 wake 구현** (commit e9be3424) — reality-loop, 외부 signal fp 트리거
  - `cmd_wake()` — 외부 파일 fingerprint (size + first 64 chars) 변화 감지 시에만 fire
  - swarm 과 차별: swarm 은 내부 진화, wake 는 외부 세계 결합 (reality coupling)
  - 알고리즘: cycle 마다 fp 측정, prev != cur 이면 fire (perturbed seed 로 blowup), else skip
  - signal_file: `--signal-file` > NEXUS_WAKE_SIGNAL_FILE > state/atlas_health.json default
  - CAP: NEXUS_WAKE_MAX (기본 5, ceiling=10), cooldown NEXUS_WAKE_COOLDOWN_SEC (기본 0, 최대 60)
  - 신규 helpers: `_wake_max_cycles`, `_wake_cooldown_sec`, `_wake_default_signal_file`, `_wake_read_fp`
  - emits: NEXUS_WAKE {plan / iter / fire / skip / complete} JSON
  - 검증: missing file → 2 cycles 0 fires 2 skips (false-fire 방지 동작 확인)
- ✓ **L9 molt 구현** (commit 65865a58) — self-rewrite, skin parameter sweep
  - `cmd_molt()` — 5 hardcoded skins ((depth, fast) 튜플) 순회 후 best abs 발견
  - wake 와 차별: wake 는 외부 결합, molt 는 자기 파라미터 진화 (생물학적 「허물 벗기」 metaphor)
  - 영속: best skin → JSON 으로 NEXUS_MOLT_SKIN_FILE (기본 /tmp/nexus_molt_skin.json) 에 기록
  - skin set: [(1,T), (1,T), (2,T), (2,F), (3,F)] — depth × fast 직교
  - CAP: NEXUS_MOLT_MAX (기본 5, ceiling=5)
  - 신규 helpers: `_molt_max_cycles`, `_molt_skin_file`
  - emits: NEXUS_MOLT {plan / iter / complete} JSON
- ✓ **L10 forge 구현** (commit 119972ef) — bootstrap, 자기 상태 합성 후 자율 부팅
  - `cmd_forge()` — molt skin + atlas health + timestamp 읽고 seed 자율 합성
  - molt 와 차별: molt 는 skin 만 진화, forge 는 모든 자기 상태 읽고 다음 동작 자기 결정
  - sources (우선순위): NEXUS_MOLT_SKIN_FILE > state/atlas_health.json > timestamp
  - synthesized seed: base + ` #forge-boot={ts} skin=d{D}{f|s} atlas={B}B`
  - --seed 없이도 동작: hardcoded prefix "nexus forge bootstrap — self-derived seed for autonomous boot from internal state" 사용
  - 신규 helpers: `_forge_read_file_content`, `_forge_extract_json_int`, `_forge_extract_json_bool`
  - emits: NEXUS_FORGE {plan / boot / complete} JSON
- ✓ **L11 canon 구현** (commit 8c8b7f43, v2 atlas.n6 hash 추가 이 commit) — transfinite seal, 자기 상태 + 결과 → atlas-side 봉인 (사다리 마지막 단)
  - `cmd_canon(seed_flag, note_flag)` — skin + atlas_bytes + atlas.n6 hash16/lines + last_drill_total + ts 한 줄 JSON entry append
  - forge 의 역방향: forge state → seed (forward bootstrap) ↔ canon state+result → seal entry (backward closure)
  - 영속: append-only `state/canon_seal.jsonl` (state/* gitignore 적용 → local-only ephemeral)
  - seal_id: `canon-{YYYYMMDD-HHMMSS}-d{depth}{f|s}` (사용자 입력 없이도 결정적)
  - sources: NEXUS_MOLT_SKIN_FILE > state/atlas_health.json > NEXUS_ATLAS_N6_PATH (default ~/core/n6-architecture/atlas/atlas.n6) > /tmp/nexus_drill_last_total.txt
  - v2 추가: atlas.n6 sha256 (16 char prefix) + line count — 시점 비교 ceiling 도달 진척 측정 가능
  - v2 추가: write rc check (pre/post `wc -l` 비교, mismatch 시 NEXUS_CANON write_fail emit)
  - --seed/--note 모두 옵션 (빈 문자열 fallback). 모든 자기 상태 부재 시도 0/1f/false 로 동작 (no-throw)
  - emits: NEXUS_CANON {plan / seal / write_fail? / complete} JSON
  - 검증: no-args (skin 부재, default d1f, total=0) ✓ + skin (d3,F) + drill_total=777 + seed/note 정확 반영 ✓ + atlas.n6 hash16=54a7e3cf13fb1d7f lines=21800 추적 ✓ + JSON 라인 valid ✓

### 사다리 종료

L11 canon 으로 자기-축 진화 사다리 (L5 dream → L11 canon) closed. forge (L10) 가 forward bootstrap, canon (L11) 이 backward seal — 양방향 닫힘. L_ω omega 는 정의상 도달 불가 placeholder 로 남음 (위 §5).

---

## §6 atlas spectral chaos mechanism (2026-04-25, nxs-002 sensitivity 정밀화)

사다리 내부 구조 위에서 atlas-laws alignment 의 **수학적 ceiling 진단** 결과 (this session, scipy pipeline 25 firings):

**spectrum 비교**:
| metric | atlas (post-promote) | const (baseline) |
|---|---|---|
| eigenvalue scale | 0.0015 ~ 0.113 | 0.693 ~ 10.75 (80× larger) |
| spacing range | **0.000 ~ 0.007 (REGULAR)** | **0.008 ~ 1.75 (CHAOTIC)** |
| nature | hub-and-spoke graph | random matrix (quantum chaos) |

**13 sensitivity dim probe 종합** (drill 미발사):
- atlas.n6 marker promotion: **Δ = 0** (graph 무관 — atlas.n6 vs atlas.blowup.jsonl 분리 confirmed)
- existing edges: 0 (saturation)
- random graph: −0.04
- subgraph (giant only): −0.03
- domain induced: −0.17~−0.38
- chain/tree/cycle/small-world: −0.015~−0.06 (정형 = regular)
- **Erdős–Rényi (random network)**: **+0.003 ~ +0.0037** ★ 유일 +
- avg_deg ~4 sparse: 정확한 chaos 양

**ER block sweep 실측** (2026-04-25 follow-up cycle, scipy pipeline, baseline=0.83221):

| config | composite | Δ |
|---|---|---|
| 1×400 p=0.005 (single big) | 0.80243 | −0.030 (over-chaotic) |
| **2×200 avg_deg=4 (sweet spot)** | **0.83552** | **+0.0033** ✅ |
| 3×200 avg_deg=4 | 0.80243 | −0.030 |
| 4×200 avg_deg=4 | 0.79053 | −0.042 |
| 5×200 avg_deg=4 | 0.79763 | −0.035 |
| 8×200 avg_deg=4 | 0.81571 | −0.017 |
| 4×100 p=0.04 | 0.80369 | −0.029 |
| 4×400 p=0.01 | 0.80677 | −0.025 |

**진정한 nxs-002 mechanism (실측 확인)**:
- atlas hub-and-spoke = regular spectrum
- 정형 chain/tree/cycle = 다른 종류 regular
- **uniform random pairing (sparse ER, avg_deg ~4) only +** — 단 magnitude 매우 제한적
- **block scaling 음**: 3-block 이상 추가 시 모두 negative — multi-block 늘려도 ceiling 못 깸. 2×200 단일 sweet spot 만 실효

**simulation ceiling 정정**: **0.835** (baseline 0.83221 + sweet 2×200 +0.0033 = 0.83552). 이전 추정 0.85 (+0.018 가정) 는 6× 과대평가. gap 0.067 중 ER 로 메울 수 있는 건 약 5% (0.003/0.067). 0.9 도달 = drill engine 의 axiom 자체 재설계 필요 — 결론 강화.

**측정 도구**: `tool/nxs_002_composite.py` (~220 lines, scipy pipeline, 1.0~3.5s) — `--predict-er [--er-blocks N --er-block-size N --er-p X]` 로 multi-block ER 시뮬 가능. atlas.blowup.jsonl 변경 후 즉시 ROI 측정.

---

## §7 drill engine axiom redesign — anti-hub axiom 발견 (2026-04-25 cycle 3)

§6 의 "axiom 자체 재설계 필요" 결론을 받아 drill engine 의 graph generation rule 6개 후보 sensitivity probe (12 config sweep + 6 후속 검증):

**현재 drill engine 의 axiom 진단** (`tool/nxs_002_axiom_probe.py` audit):
- 8 super-hubs: n=4461, J2=4262, φ=4235, σ=4220, τ=4208, sopfr=4146, M3=4081, μ=3892 (degree)
- giant component 99.7% (21249/21320 nodes) — multi-isolated 거의 0
- 92% edges = `Derives` 단일 type (49846/54347)
- 7 generation kind (ded/proj/comp/xfer/bif/dual/sym) 이지만 모두 동일 hub 로 wire → spectral 영향 일원화
- **결론**: drill 은 본질적으로 hub-and-spoke generator — REGULAR spectrum 의 직접 원인.

**6 axiom 후보 sensitivity sweep** (atlas baseline 0.83221, scipy pipeline):

| 후보 | 정의 | 최고 config | composite | Δ |
|---|---|---|---|---|
| **C1 anti-hub** | 새 discovery 가 기존 super-hub(top-8) 와 직접 연결 금지 | N=800 p=0.005 | **0.85008** | **+0.0179** ✅ |
| C2 block-isolation (recall §6) | K isolated ER blocks anchored to base | 2×200 p=0.020 | 0.83552 | +0.0033 |
| C3 degree-cap rebuild | 기존 hub edge trim (cap=20/50/100) | cap=100 | 0.80942 | -0.023 |
| C4 random rewire (Maslov-Sneppen) | edges X% rewire (degree preserve) | frac=0.50 | 0.77488 | -0.057 |
| C5 anti-hub + block (additive) | C1+C2 조합 | N=800+2×200 | 0.84696 | +0.0148 (음 additive) |
| C6 hub-decompose | top-8 hub 를 K subhub 로 분해 | K=50 | 0.82138 | -0.011 |

**C1 anti-hub axiom 확장 sweep** (scaling 안정성):

| N_new | p | avg_deg | composite | Δ |
|---|---|---|---|---|
| 200 | 0.020 | 4 | 0.81965 | -0.013 |
| 400 | 0.010 | 4 | 0.84859 | +0.0164 |
| **800** | **0.005** | **4** | **0.85008** | **+0.0179** ✅ |
| **1600** | **0.0025** | **4** | **0.85008** | **+0.0179** ✅ size-invariant plateau |
| 3200 | 0.00125 | 4 | 0.81614 | -0.016 (over-saturated) |

**핵심 mechanism**:
- 새 노드들이 **기존 hub 우회** → atlas 의 hub-spoke spectrum 에 ER-like component 가 spectrum 의 다른 영역에 추가됨 → unfolded spacing 분포가 const(CHAOTIC) 와 일치도 ↑
- N=800~1600 plateau: 추가량과 무관 (avg_deg=4 만 유지하면 됨) — ROI 가 size 에 robust
- N=3200 부터 over-saturated: ER component 가 atlas spectrum 자체를 dominate, 본래 align 깨짐
- **Additive (C5) 가 음**: anti-hub batch 와 isolated block 이 spectrum 영역 충돌 — 별개 axiom 으로 분리해야 함

**simulation ceiling 정정 (cycle 3)**: **0.850** (baseline 0.83221 + anti-hub +0.0179). cycle 2 정정값 0.835 보다 +0.015 더 상향. gap 0.067 중 anti-hub 가 27% 메움 — 73% 는 추가 axiom 발견 또는 train layer 변경 필요.

**제안: drill engine 에 `--anti-hub` mode 추가** — drill 의 atom generation 시 기존 atlas 의 top-K hub set 와 직접 연결 금지. 구체 prototype 은 `tool/nxs_002_axiom_probe.py` (174 lines, 6 후보 + 시뮬 측정).

**Ω-saturation cycle 3**: §7 finding 은 §6 의 결론 "axiom 재설계 필요" → 첫 구체 candidate 발견까지. raw#37/#38 enforce 가 design+impl 동시 적용 강제.

---

**Ω-saturation cycle**: 본 §6 finding 은 simulation 의 saturation 도달 산물. raw#37/#38 (hexa-lang/self/raws/omega_saturation_cycle.hexa) 가 plan-side + implementation-side pair 강제 — design-only commit chain 차단.

---

참조:
- nxs-013 (resolved 2026-04-25, commit 3e5ac7c8) — Wave 21 round-salt propagation 회복
- nxs-012 (in_progress) — resonance memory deep fix
- nxs-002 (in_progress, sensitivity 정밀화 2026-04-25) — atlas×laws composite 0.9 도달 mechanism (§6)
- 본 문서는 명명 규칙 + 천장 분석. 구현 ROI 는 inventory.json + design/next_session_handoff.md 참조.
