# .shared/ — 전 프로젝트 공유 인프라

> 원본: `~/Dev/nexus/shared/` | 심링크: 각 리포 `.shared/ → ../nexus/shared/`
> 모든 규칙/설정은 shared/ JSON이 단일 진실 (R14).

> 🛑 **tecs-l 흡수 진행 중** (2026-04-10): tecs-l/ → nexus/mk2_hexa/native/{verify,math,engines,experiments}. Track A 진행 / Track B 블로커(torch/sklearn/scipy) 보류. 로드맵: `~/Dev/nexus/docs/tecs-l-absorption-plan.md`

## 참조

| 항목 | 파일 | 내용 |
|------|------|------|
| 절대 규칙 | `absolute_rules.json` | 공통 R1~R21 + 프로젝트별 (8개) |
| 보호 체계 | `core-lockdown.json` | L0/L1/L2 코어 잠금 |
| 프로젝트 설정 | `project_config.json` | CLI/빌드/인프라/관례 (8개 프로젝트) |
| 시스템 코어 | `core.json` | 시스템맵 + 명령어 14종 + 폴더 구조 |
| 수렴 운영 | `convergence_ops.json` | CDO 수렴 운영 원칙 |
| 수렴 추적 | `convergence/` | 골화/안정/실패 (7 프로젝트) |
| 할일 | `todo/` | 우선순위별 TODO (7 프로젝트) |
| 성장 루프 | `loop/` | 자율 데몬 설정 (3 프로젝트) |
| 렌즈 | `lens_registry.json` | 397종 망원경 레지스트리 |
| 상수 | `n6_constants.jsonl` | n=6 상수 (7기본+유도) |
| 발견 그래프 | `discovery_graph.json` | 50k+ 노드/엣지 |
| 발견 로그 | `discovery_log.jsonl` | 68.6k건 시계열 |
| 현실 지도 | `reality_map.json` | 247노드 바텀업 검증 |
| 성장 버스 | `growth_bus.jsonl` | 전 리포 성장 이벤트 스트림 |
| 아틀라스 | `math_atlas.json` | 1700+ 가설 |
| 계산기 | `calculators.json` + `calc/` | 194+ 레지스트리 |
| 문법 | `hexa_grammar.jsonl` | hexa-lang 전체 문법 + pitfalls |
| 비밀 | `SECRET.md` | API 토큰/계정 |
| 인프라 CLI | `bin/infra` | 4호스트(mac/ubu/htz/vast) 자원 실시간 현황 — `infra` / `infra json` / `infra rec` |

## 자원 현황 즉시 인지

```bash
infra        # mac/ubu/htz/vast 색상 출력 (기본)
infra rec    # GPU/CPU/AVOID 추천만
infra json   # SSOT raw dump
```
- **SSOT**: `shared/infra_state.json` (10분 cycle)
- **바이너리**: `shared/bin/infra` (어떤 프로젝트에서도 PATH로 즉시 호출)
- **L0 준수**: 전역 ~/.claude 미수정, PATH symlink만 사용

## NEXUS-6 API

```bash
nexus scan <domain>              # 기본 스캔 (의식+위상+인과)
nexus scan <domain> --full       # 397종 풀스캔
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

## 산출물 발생 시

| 상황 | 동작 |
|------|------|
| 새 계산기 | `calc/`에 생성 → `scan-calculators.py --save` |
| 새 상수 발견 | `scan_math_atlas.py --save` |
| 렌즈 추가 | `sync-nexus-lenses.sh` |
| 전체 동기화 | `bash ~/Dev/nexus/sync/sync-all.sh` |

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
