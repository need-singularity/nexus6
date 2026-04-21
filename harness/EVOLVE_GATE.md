# evolve_gate — 로드맵 자율 진화 엔진

> roadmap 의 `vN → v(N+1)` 자율 승격. deferred=0 + planned=0 + R14 CLEAN + 정직성 invariant 충족 시 자동 승격 + 다음 버전 meta/phase 블록 auto-generate. millennium v2.3 → v3 수동 전환 pattern 을 모든 nexus 프로젝트 (nexus/anima/n6-architecture/hexa-lang/millennium) 로 일반화.

## 사용

```bash
# 모든 프로젝트 dry-run
python3 shared/harness/evolve_gate.py --dry-run

# 단일 프로젝트
python3 shared/harness/evolve_gate.py --project anima

# 실제 승격 (통과 시 roadmap.json 수정 + evolve_history.jsonl 기록)
python3 shared/harness/evolve_gate.py

# 강제 승격 (MANDATORY check 우회, 위험)
python3 shared/harness/evolve_gate.py --project X --force
```

## 진화 조건 (MANDATORY)

모든 아래 통과해야 auto-promote:
1. **saturation**: `deferred == 0 && planned == 0`
2. **OUROBOROS R14**: MILL-*/BT-* CRITICAL cycle = 0 (optional, report 없으면 skip)
3. **honesty invariant**: `_meta.description` 에 정직성 키워드 ("정직", "honest", "0/6" 등) 존재

하나라도 실패 시 HOLD (승격 보류).

## 승격 동작

1. `schema_version` 현재값 → `{major+1}.0`
2. 새 `_v{N+1}_meta` block 추가:
   - `auto_promoted: true`
   - `promoted_at: ISO timestamp`
   - `parent_version: 현재`
   - `parent_completion: 통계 snapshot`
   - `honesty_charter: [4 원칙]`
   - `tracks: [프로젝트 config 의 track_pattern]`
3. 새 `_v{N+1}_phases` block 추가 — 각 track 별 seed task
4. `evolve_history.jsonl` 에 이벤트 append

## 프로젝트 config (PROJECT_CONFIGS)

각 프로젝트별 진화 규칙:
- `file`: roadmap JSON 경로
- `track_pattern`: 다음 버전 track 이름 목록
- `honesty_invariant`: 정직성 불변식 (프로젝트별)
- `version_key`: schema version dot-path

현재 등록:
- millennium (E/T/M)
- nexus (INFRA/GROWTH/META)
- anima (PHI/DUAL_TRACK/CONSCIOUSNESS)
- n6-architecture (TRACK_SCAN/TRACK_DSE/TRACK_META)
- hexa-lang (LANG/COMPILER/ECOSYSTEM)

## 주기 자동 실행 (cron 또는 launchd)

### macOS launchd (`~/Library/LaunchAgents/com.nexus.evolve-gate.plist`)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.nexus.evolve-gate</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/python3</string>
    <string>/Users/ghost/Dev/nexus/shared/harness/evolve_gate.py</string>
  </array>
  <key>StartInterval</key>
  <integer>21600</integer>  <!-- 6시간마다 -->
  <key>StandardOutPath</key>
  <string>/Users/ghost/Dev/nexus/shared/harness/evolve_gate.stdout</string>
  <key>StandardErrorPath</key>
  <string>/Users/ghost/Dev/nexus/shared/harness/evolve_gate.stderr</string>
</dict>
</plist>
```

설치: `launchctl load ~/Library/LaunchAgents/com.nexus.evolve-gate.plist`

### Linux cron (`crontab -e`)

```cron
0 */6 * * * /usr/bin/python3 /Users/ghost/Dev/nexus/shared/harness/evolve_gate.py >> /tmp/evolve_gate.log 2>&1
```

## evolve_history.jsonl 포맷

각 line = 1 event:
```json
{
  "timestamp": "2026-04-15T15:45:00Z",
  "project": "millennium",
  "current_version": "3.0",
  "statistics": {"total": 173, "done": 150, "partial": 5, "deferred": 0, "planned": 18},
  "checks": {
    "saturation": {"pass": false, "reason": "18 planned 미시작"},
    "ouroboros_r14": {"pass": true, "reason": "R14 CLEAN ..."},
    "honesty": {"pass": true, "reason": "정직성 invariant present..."}
  },
  "decision": "HOLD",
  "status": "SATURATION_NOT_REACHED"
}
```

## 정직성 헌장 (진화 과정에서 불변)

모든 자동 승격은 아래 4 원칙을 새 `_v{N+1}_meta.honesty_charter` 에 복제 유지:
1. BT 해결 주장 금지
2. 외부 의존 명시
3. MISS 조건 사전
4. OUROBOROS 주기 감사

프로젝트별 invariant 추가 (e.g. millennium "BT 해결 0/6 유지").

## Safety

- `--dry-run`: 실제 수정 없음 (preview JSON)
- `--force`: MANDATORY 우회 (사용자 의도 명시 필요)
- `evolve_history.jsonl`: 모든 이벤트 append-only audit log
- `OUROBOROS 2.0 CLI` 주기 실행 권장 (auto-promotion 후 R14 재검증)

## 향후 확장

- OUROBOROS 결과 자동 통합 (report 갱신 + 반영)
- seed task 를 LLM 으로 generate (프로젝트 컨텍스트 기반)
- 승격 직후 Slack/email notification
- inter-project 의존 (millennium v5 시작 조건 = nexus v4 도달)
