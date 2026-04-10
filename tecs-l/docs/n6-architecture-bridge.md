# n6-architecture ↔ TECS-L 연결 문서

> 상세 문서: ~/Dev/n6-architecture/docs/tecs-l-bridge.md (원본)
> 최종 갱신: 2026-04-02

## 역할

- **TECS-L**: 수학 체계 (순수 이론) — 증명, 가설, 상수 유도, DFS 채굴
- **n6-architecture**: 산업 현장 적용 (공학 설계) — 307 DSE, 93 BT, 17 AI 기법

## 동기화 현황

| 방향 | 내용 | 상태 |
|------|------|------|
| TECS-L → n6 | 계산기 레지스트리, README, CLAUDE.md 규칙 | ✅ 자동 (sync-*.sh) |
| n6 → TECS-L | DSE TOML 306개, 상수 맵, BT→가설 | ✅ 수동 + 스크립트 |
| 양방향 | 아틀라스 (scan_math_atlas.py) | ✅ 자동 |

## 핵심 연결 지점

1. **가설↔BT**: TECS-L H-XX 가설이 n6 실측에서 EXACT → BT 등록
2. **상수↔DSE**: TECS-L 수학 상수가 n6 307 도메인에서 설계 파라미터로 출현
3. **DFS↔패턴**: TECS-L DFS 채굴 결과가 n6 새 도메인 TOML에 반영

## 명령어

```bash
# 전체 동기화
cd ~/Dev/TECS-L && bash .shared/scripts/sync-calculators.sh

# DSE 역동기화 (n6→TECS-L)
cp ~/Dev/n6-architecture/tools/universal-dse/domains/*.toml .shared/dse/domains/

# 자동 등급화
python3 calc/auto_grade_n6.py
```
