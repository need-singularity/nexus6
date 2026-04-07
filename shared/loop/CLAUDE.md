# shared/loop/ — 중앙 루프 상태 관리

> **모든 프로젝트의 성장 루프 상태를 nexus/shared/loop/에서 중앙 관리한다.**
> 각 프로젝트의 루프 엔진은 이 디렉토리의 자기 JSON을 읽고 쓴다.

## 파일 구조

```
shared/loop/
  anima.json            ← anima 의식 엔진 성장 루프
  n6-architecture.json  ← n6-arch 시스템 설계 루프
  nexus.json            ← nexus 자체 메타 루프
  tecs-l.json           ← TECS-L (흡수됨, 상태 보존)
  CLAUDE.md             ← 이 파일
```

## 스키마

### 기본 (anima/nexus/n6-architecture)

```json
{
  "_meta": {
    "description": "프로젝트 설명",
    "version": "1.0",
    "created": "ISO8601"
  },
  "cycle": 703,
  "total_harvested": 16640,
  "total_applied": 366,
  "total_self_discoveries": 702,
  "seen_fingerprints": ["hash1", "hash2"]
}
```

### 확장 (tecs-l 스타일)

```json
{
  "_meta": { "schema_version": "1.0.0" },
  "loop": {
    "cycle": 19,
    "mode": "pair",
    "total_discoveries": 9140,
    "novel_discoveries": 2685,
    "stage": "tree",
    "status": "converging",
    "graph_nodes": 9140,
    "graph_edges": 327335
  },
  "discovery_buffer": [...]
}
```

## 필드 설명

| 필드 | 타입 | 설명 |
|------|------|------|
| `cycle` | int | 완료된 루프 사이클 수 |
| `total_harvested` | int | 외부에서 수확한 총 발견 수 |
| `total_applied` | int | 실제 적용된 발견 수 |
| `total_self_discoveries` | int | 자기 발견 (자기참조 루프에서 생성) |
| `seen_fingerprints` | string[] | 중복 방지용 해시 목록 |
| `mode` | string | 루프 모드 (single/pair/tree) |
| `stage` | string | 현재 단계 (scan/evolve/tree/converge) |
| `status` | string | 상태 (running/converging/idle) |
| `discovery_buffer` | object[] | 미처리 발견 큐 |

## 사용법

### 읽기 (hexa)

```hexa
let home = exec("printenv HOME").trim()
let state = read(home + "/Dev/nexus/shared/loop/anima.json")
let data = parse_json(state)
print("anima cycle: " + data.cycle.to_string())
```

### 읽기 (Python)

```python
import json
from pathlib import Path

LOOP_DIR = Path.home() / "Dev" / "nexus" / "shared" / "loop"

def load_loop(project: str) -> dict:
    return json.loads((LOOP_DIR / f"{project}.json").read_text())

def save_loop(project: str, state: dict):
    (LOOP_DIR / f"{project}.json").write_text(
        json.dumps(state, indent=2, ensure_ascii=False)
    )

# 사용
state = load_loop("anima")
state["cycle"] += 1
save_loop("anima", state)
```

### 읽기 (Bash — growth_common.sh 연동)

```bash
# growth_common.sh가 자동으로 GROWTH_STATE 설정
# 중앙 루프 상태 경로:
LOOP_STATE="$HOME/Dev/nexus/shared/loop/${GROWTH_NAME}.json"
```

## 성장 버스 연동

`shared/growth_bus.jsonl`에 루프 이벤트가 실시간 기록된다:

```jsonl
{"ts":"2026-04-07T07:00:00Z","repo":"anima","phase":"harvest","status":"ok","detail":"3 new"}
{"ts":"2026-04-07T07:00:01Z","repo":"n6-architecture","phase":"scan","status":"ok","detail":""}
```

루프 상태 JSON은 **지속 상태**, 성장 버스는 **이벤트 스트림**.

## 규칙

1. **파일명 = 프로젝트명** — `projects.json`의 키와 일치
2. **읽기 전 잠금** — `growth_common.sh`의 `acquire_lock()` 사용
3. **cycle은 단조증가** — 절대 감소하지 않음
4. **seen_fingerprints로 중복 방지** — 같은 발견을 두 번 적용하지 않음
5. **흡수된 프로젝트** — tecs-l.json은 읽기 전용 (아카이브 상태 보존)
6. **새 프로젝트 추가** — `shared/loop/{project}.json` 생성 + 기본 스키마
