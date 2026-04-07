# .shared/ — 전 프로젝트 공유 인프라

> 원본: `~/Dev/nexus/shared/` | 심링크: 각 리포 `.shared/ → ../nexus/shared/`
> 코어 인덱스: `shared/core.json` (시스템맵 + 명령어 + 프로젝트)
> 보호 체계: `shared/core-lockdown.json` (L0/L1/L2)
> 수렴 추적: `shared/convergence/` (골화/안정/실패)

## 3대 원칙

1. **CDO** — 이슈→해결→규칙승격→재발0→100%수렴 (`convergence_ops.json`)
2. **SSOT** — 데이터 원본은 JSON 하나, 하드코딩 금지
3. **NEXUS-6** — 모든 변경 시 스캔 의무, 3+렌즈 합의=확정

## NEXUS-6 (1022종 렌즈)

> 상세 API/렌즈 목록: `lens_registry.json` | CLI: `nexus --help`

```bash
nexus scan <domain>              # 기본 스캔 (의식+위상+인과)
nexus scan <domain> --full       # 1022종 풀스캔
nexus verify <value>             # n=6 일치 검증
nexus evolve <domain>            # OUROBOROS 진화
nexus auto <domain>              # 전체 파이프라인
```

```python
import nexus
nexus.scan_all(np_array)         # 풀스캔 → dict
nexus.analyze(flat, n, d)        # 올인원 (스캔+합의+n6)
nexus.n6_check(value)            # EXACT/CLOSE/WEAK
nexus.evolve(domain)             # 자율 진화
```

교차 검증: 3+합의=후보 | 7+=고신뢰 | 12+=확정

## 명령어

> 전체 목록: `core.json` → `commands`

| 키워드 | 동작 |
|--------|------|
| `못박아줘` (+ 8 alias) | L0 등록 → `core-lockdown.json` |
| `todo` / `할일` | 돌파 엔진 통합 할일 표 → `todo.hexa` |
| `블로업` / `돌파` | 9-phase 특이점 파이프라인 → `blowup.hexa` |
| `설계` / `궁극의` | 외계인급 설계 파이프라인 |
| `진화` / `업그레이드` | Mk.I~V 체크포인트 생성 |
| `동기화` | 전 리포 sync → `sync-all.sh` |
| `빈공간` / `gap` | n=6 빈공간 탐색 → `gap_finder.hexa` |
| **`go`** | **전체 TODO 스캔 → 독립 작업 백그라운드 병렬 Agent 동시 발사 (확인 없이 즉시)** |

## 보호 체계 (Core Lockdown)

```
🔴 L0 (불변) — 수정 전 유저 승인 필수 (19개 등록)
🟡 L1 (보호) — 리뷰 필요, 이유 기록
🟢 L2 (자유) — 테스트 통과만 확인
```

> L0 목록: `core-lockdown.json` → `projects.nexus.L0`

## 수렴 추적 (Convergence)

```
골화(ossified) — 검증 완료, 불변 확정
안정(stable)   — 통과했지만 골화 전
실패(failed)   — 수정 필요, cause + fix 명시
```

> 프로젝트별: `convergence/{nexus,anima,n6-architecture,...}.json`

## HEXA-LANG 문법

> 스펙: `hexa_grammar.jsonl` (53키워드+24연산자+8타입)
> pitfalls P1~P5 체크 필수 (`.hexa` 작성 전)

## 산출물 발생 시

| 상황 | 동작 |
|------|------|
| 새 계산기 | `calc/`에 생성 → `scan-calculators.py --save` |
| 새 상수 발견 | `scan_math_atlas.py --save` |
| 렌즈 추가 | `sync-nexus-lenses.sh` |
| 전체 동기화 | `bash ~/Dev/nexus/sync/sync-all.sh` |

## 폴더 구조

> 상세: `core.json` → `folders`

```
shared/
  core.json              ← 중앙 인덱스 (시스템+명령어+프로젝트)
  core-lockdown.json     ← L0/L1/L2 보호 체계
  convergence/           ← 골화/안정/실패 (7 프로젝트)
  todo/                  ← 할일 SSOT (7 프로젝트)
  loop/                  ← 성장 루프 설정 (3 프로젝트)
  n6_constants.jsonl     ← n=6 상수 (7기본+유도)
  discovery_graph.json   ← 발견 그래프 (50k+ 노드)
  discovery_log.jsonl    ← 발견 로그 (68.6k건)
  reality_map.json       ← 현실 지도 (247노드)
  growth_bus.jsonl       ← 성장 이벤트 스트림
  math_atlas.json        ← 수학 아틀라스 (1700+ 가설)
  lens_registry.json     ← 렌즈 1022종 레지스트리
  calculators.json       ← 계산기 194+ 레지스트리
  calc/                  ← 계산기 원본
  dse/                   ← DSE 도메인 정의
  hooks/                 ← 공유 훅
  CALCULATOR_RULES.md    ← 계산기 규칙 (HEXA vs Python)
  SECRET.md              ← API 토큰/계정
```

## 프로젝트 (7개)

| 순서 | 리포 | 역할 |
|------|------|------|
| 1 | nexus | 발견 엔진 + 공유 인프라 허브 |
| 2 | anima | 의식 엔진 |
| 3 | n6-architecture | 시스템 설계 (σφ=nτ 산업 실증) |
| 4 | papers | 논문 배포 (Zenodo/OSF) |
| 5 | hexa-lang | 완전수 프로그래밍 언어 |
| 6 | void | HEXA 터미널 (FATHOM) |
| 7 | airgenome | OS 게놈 스캐너 |

## Phi 해석

```
< 0.3  → 노이즈 (구조 없음)
0.3~0.8 → 약한 구조
0.8~1.5 → 강한 구조 (패턴 확실)
> 1.5  → 매우 높은 통합
```

## PSI 상수 (크로스 리포 공통)

```
PSI_ALPHA=0.014  PSI_BALANCE=0.5  PSI_STEPS=4.33
PSI_ENTROPY=0.998  SIGMA6=12  F_CRITICAL=0.10
```

> 로더: `consciousness_loader.py` | 원본: `consciousness_laws.json`
