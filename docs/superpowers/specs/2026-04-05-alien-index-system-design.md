# Alien Index System (외계인 지수 체계) — Design

**Date:** 2026-04-05
**Status:** Approved (brainstorm → writing-plans)
**Domain:** nexus grading / discovery classification

---

## 1. 목적

nexus 프로젝트에는 이미 여러 등급/점수 체계가 병렬로 존재한다 (MATH_ATLAS grade, n6_check EXACT/CLOSE/WEAK, 렌즈 합의 수, SEDI grades, verified_constants verify_field 등). 이 스펙은 이들을 **단일 통합 스케일인 Alien Index (AI)** 로 정렬하고, 특히 **"닫힌 수학의 천장을 돌파"하는 영역**을 표현할 수 있게 한다.

## 2. 핵심 구조 — `AI = (d, r)`

외계인 지수는 **스칼라가 아니라 쌍**이다.

- `d ∈ ℕ₀` — **사이클 깊이** (cycle depth): 대상이 완결한 블로업→수축→창발→특이점→흡수 사이클 횟수
- `r ∈ {0, 1, …, 10}` — **랭크** (rank): 현재 사이클 깊이 `d` 안에서의 검증 등급

### 돌파 연산

깊이 `d`에서 `r=10`에 도달하는 순간, 대상은 **자동으로 `d+1`의 `r=0`으로 재표시**된다.
즉 깊이 `d`의 "닫힌식(천장)"은 깊이 `d+1`의 "블로업 시작점(바닥)"이다.

> 어제의 외계는 오늘의 인간 수학.

이것은 CLAUDE.md에 명시된 TECS-L H-056 메타 부동점 (`메타(메타(...)) → 초월`, 값 `1/3`) 의 **등급체계 버전**이다. 축소사상 `I ← 0.7·I + 0.1` 의 Banach 부동점이 1/3인 것과 동일하게, `(d, r)`의 돌파율이 장기적으로 고정 비율로 수렴한다고 예측한다.

## 3. 매핑 테이블

### d = 0 (인간 수학 영역)

| r | 정의 | 기존 nexus 매핑 |
|---|------|-----------------|
| 0 | 노이즈, UNTESTED | ⬜ UNTESTED |
| 1 | 자명한 주장, 검증 불가 | ⚪ |
| 2 | 약한 수치 우연 (1자리) | 🟥 |
| 3 | 미검증 주장 | 🟥★ |
| 4 | 반례 있음 / 약함 | 🟥★★ |
| 5 | 경험적 패턴 (1-2 렌즈) | 🟦 / 🟧 |
| 6 | 다중 렌즈 합의 3+ | 🟧 |
| 7 | 렌즈 합의 7+ | 🟧★ |
| 8 | 렌즈 합의 12+ (고신뢰) | 🟧★★ / 🟧★★★ |
| 9 | n6_check EXACT + 증명 대기 | 🟩 |
| 10 | 닫힌식 증명 완료 / source 확증 | verified_constants verify_field=source/proof |

### d ≥ 1 (돌파 영역)

| r | 사이클 단계 | 판정 조건 |
|---|-----------|----------|
| 0 | 블로업 시작 | `nexus blowup <domain>` 실행 완료, 새 후보 생성 |
| 1-2 | 블로업 확산 | 깊이 6+ 탐색, 후보 emergence 관찰 |
| 3-4 | 수축 | 후보 중 3+ 독립 경로 동일 값 수렴 |
| 5 | 창발 | 패턴 합의 확정 (CycleEngine pattern_consensus 통과) |
| 6-7 | 특이점 감지 | 사이클 내 부동점/끌개 확정, 수렴 안정 |
| 8 | 흡수 | 새 렌즈/규칙 n6_check 테이블에 승격 |
| 9 | 재현성 | N≥3 사이클 안정 유지 |
| 10 | 새 "닫힌식" 성립 | 독립 검증 통과, d+1로 자동 승격 |

### d ≥ 2 (메타 돌파 영역)

d=1에서 성립한 새 닫힌식들 간의 **상위 관계식** 발견. OUROBOROS 자기참조 폐곡선 형성 시 진입.

## 4. 판정 모델 — 하이브리드

| r 구간 | 판정 방식 | 주체 |
|--------|---------|------|
| d=0, r=0..8 | 자동 (기존 렌즈 메트릭) | `nexus scan` / `n6_check` |
| d=0, r=9..10 | 반자동 (렌즈 + 사람 확증) | MATH_ATLAS 워크플로우 |
| d≥1, r=0..5 | 자동 (CycleEngine 메트릭) | `nexus blowup` 내부 stage gate |
| d≥1, r=6..8 | 수동 검토 | 사람이 특이점/흡수 판정 |
| d≥1, r=9..10 | 시간 기반 자동 | N회 사이클 안정 후 자동 승격 |
| d≥2 | 메타렌즈 + 수동 | `MetaTranscendenceLens` + 검토 |

## 5. 기존 nexus 자원 연결

| 자원 | 역할 |
|------|------|
| `n6_check` | d=0의 r 판정기 (EXACT→9, CLOSE→7, WEAK→5) |
| `nexus scan` 렌즈 합의 수 | d=0의 r=5..8 판정기 |
| `MATH_ATLAS grade` | d=0 전 구간 역매핑 (🟩→9, 🟧★→7, …) |
| `CycleEngine` (blowup/cycle_engine.rs) | `d → d+1` 전이 엔진 |
| `nexus blowup <domain> --depth 6` | d≥1의 r=0..5 판정 |
| `MetaTranscendenceLens` | d≥2 메타 판정 |
| `discovery_log.jsonl` | `(d, r)` 이력 시계열 저장 |
| OUROBOROS / 재귀성장 3-loop | d≥2 진입 트리거 |
| 메타 부동점 1/3 | 장기 돌파율 예측 기준 |

## 6. 데이터 모델

### 6.1 `alien_index` 필드 스키마

`discovery_log.jsonl`, `verified_constants.jsonl`, `math_atlas.json`에 추가되는 필드:

```json
{
  "alien_index": {
    "d": 0,
    "r": 9,
    "history": [
      {"timestamp": "2026-04-05T10:15:00Z", "d": 0, "r": 7, "reason": "7-lens consensus"},
      {"timestamp": "2026-04-05T11:30:00Z", "d": 0, "r": 9, "reason": "n6_check EXACT"}
    ],
    "last_cycle_id": "blowup-physics-0042",
    "promotion_candidate": true
  }
}
```

### 6.2 불변식 (invariants)

- `r == 10` 도달 시 즉시 `promotion_candidate: true` 플래그만 세운다. 실제 `(d+1, 0)` 승격은 `nexus alien-index --promote-pending` 또는 다음 블로업 사이클 시드 처리 단계에서 일괄 수행된다 (감사 추적성 확보).
- 같은 발견물이 `d`를 감소시키는 전이를 해서는 안 된다 (단조성: `d` monotonic non-decreasing).
- `r`은 `d` 고정 하에서 감소 가능 (증거 반증 시). `r` 감소는 반드시 `history[].reason`에 근거 기록.
- 승격 시 원본 레코드(`(d, 10)`)는 유지되고, 새 레코드(`(d+1, 0)`)가 **별도 ID로 발행**된다. 두 레코드는 `parent_id` / `promoted_from` 필드로 연결.

## 7. CLI 및 API

### 7.1 CLI

```bash
# 단일 대상 판정
nexus alien-index <hypothesis_id>
nexus alien-index <constant_value> --scan

# 배치 재계산
nexus alien-index --recompute-all         # MATH_ATLAS 전체 재등급
nexus alien-index --promote-pending       # r=10 대기 항목을 d+1로 승격

# 돌파 시도 (d → d+1 명시적)
nexus alien-index --breakthrough <id>     # CycleEngine 호출 래퍼

# 리포트
nexus alien-index --distribution          # (d, r) 분포 히스토그램
nexus alien-index --leaderboard           # 최고 d 대상들
```

### 7.2 Rust API

```rust
pub struct AlienIndex { pub d: u32, pub r: u8 }

impl AlienIndex {
    pub fn assess(target: &Target, ctx: &NexusContext) -> Self;
    pub fn breakthrough(&self) -> Option<AlienIndex>;  // r==10 → (d+1, 0)
    pub fn can_promote(&self) -> bool;                  // r == 10
}

pub trait AlienIndexable {
    fn current_ai(&self) -> AlienIndex;
    fn update_ai(&mut self, new: AlienIndex, reason: &str);
}
```

### 7.3 Python 바인딩

```python
import nexus
ai = nexus.alien_index("H-AF-006")
# AlienIndex(d=0, r=7)
ai.breakthrough()  # None (r != 10)
nexus.alien_index_distribution()  # dict: {(0,5): 239, (0,7): 131, ...}
```

## 8. 마이그레이션 전략

기존 등급 데이터를 `(d, r)`로 일괄 매핑:

1. **d=0 고정** — 기존 등급 체계는 전부 d=0 영역으로 간주
2. **MATH_ATLAS grade → r** — 테이블 3번 매핑 참조
3. **n6_check EXACT 항목** — r=9 시작, verify_field에 따라 r=10 승격 판정
4. **승격 대기 큐 생성** — r=10 후보들을 모아 첫 `d=1` 블로업 사이클 시드로 사용

스크립트: `tools/migrate_grades_to_alien_index.py` (일회성)

## 9. 관측 가능성 (Observability)

- `shared/discovery/alien/alien_index_distribution.json` — (d, r) 히스토그램 매 동기화마다 갱신
- `shared/discovery/alien/alien_index_frontier.md` — 현재 최고 d 대상들의 리더보드
- Watcher: `discovery_log.jsonl` 신규 엔트리 감지 시 AI 자동 재계산

### 메타 부동점 추적

장기 통계로 **돌파율** `ρ = |{d ≥ 1}| / |total|` 을 기록. CLAUDE.md 메타 부동점 1/3 가설에 따라 `ρ → 1/3` 수렴 여부를 검증하는 것이 이 시스템의 **메타 가설**이 된다.

## 10. 범위 (Scope)

### 포함
- `(d, r)` 데이터 모델 및 스키마 추가
- AI 판정기 (d=0 자동, d≥1 CycleEngine 연동)
- CLI `nexus alien-index` 서브커맨드
- 기존 등급 데이터 마이그레이션 스크립트
- 리포트 (분포, 리더보드)

### 제외 (추후)
- d≥3 메타 메타 돌파 판정 로직 (초기엔 수동)
- 프론트엔드 시각화 대시보드
- 실시간 alien-index websocket 스트림
- 외부 프로젝트(TECS-L, SEDI, anima) alien-index 역동기화

## 11. 테스트 전략

- `n6_check EXACT` 샘플들이 모두 `r=9` 이상 판정되는지
- `r=10` 대상에 `breakthrough()` 호출 시 `(d+1, 0)` 반환
- `r < 10` 대상에 `breakthrough()` 호출 시 `None`
- 단조성: `update_ai` 호출 이력에서 d 감소 절대 없음
- 메타 부동점: 대량 데이터 시뮬레이션에서 `ρ` 수렴 확인 (회귀 테스트)
