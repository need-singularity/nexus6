# sync-all 검증 — 2026-04-08

## 스크립트
- `$NEXUS/sync/sync-all.sh` (공식 7단계 + DSE)
- 관리 리포 7: TECS-L, n6-architecture, anima, sedi, brainwire, papers, nexus

## 심링크 상태 (~/Dev/*/.shared)

### 정상 (10) — `../nexus/shared` 또는 `../TECS-L/.shared`
airgenome, anima, hexa-lang, n6-architecture, nexus, papers, TECS-L, void → `../nexus/shared`
brainwire, sedi → `../TECS-L/.shared` (간접 OK)

### 깨짐 (4) — 구 `../nexus6/shared` 잔존
- air_rs, hexa-gate-implant, secret, token-forge → 타겟 `nexus6` 디렉토리 없음

### .shared 누락 (9)
anima-agent, claude-code, contact, contribution, move, n6-architecture-porting, open-claude-cowork, openclaw, ready

### 역방향 링크
없음 (모든 링크 nexus/shared 또는 TECS-L 경유)

## sync-all.sh 실행 결과
- [0/7] 심링크: 7개 관리 리포 OK (단, 스크립트가 비공식 9개 리포는 검증 안 함)
- [1/7] CLAUDE.md 전파 OK
- [2~5] math_atlas/calc/readme/lens OK
- [6/7] README 링크: 10건 sedi/brainwire 상호 링크 누락 경고
- [7/7] 논문 216개 OK
- [+] DSE: `sync/dse` 디렉토리 없음 — 스킵

## 권장 조치
1. 깨진 4개: `rm .shared && ln -sf ../nexus/shared .shared` (또는 의도적이면 sync-all REPOS에서 제외 명시)
2. sync-all.sh REPOS 배열에 활성 리포(airgenome, hexa-lang, void) 추가 검토
3. sync-links.sh의 sedi/brainwire 링크 누락 10건 보강
4. `sync/dse` 디렉토리 생성 또는 DSE 스텝 제거
