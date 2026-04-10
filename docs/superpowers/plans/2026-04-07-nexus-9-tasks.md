# Nexus 9개 작업 일괄 실행 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** nexus 프로젝트의 인프라 정리 + 성장 엔진 강화 + 새 기능 9가지를 일괄 실행

**Architecture:** 독립 작업 (Task 1-3, 6-7)은 병렬 가능. 성장 엔진 작업 (Task 4-5)은 순차. 새 기능 (Task 8-9)은 인프라 정리 후 실행.

**Tech Stack:** hexa-lang (`.hexa` only), JSONL 설정 파일, HTML 대시보드

---

## File Structure

| 파일 | 역할 | 작업 |
|------|------|------|
| `.gitignore` | auto_stubs 제외 | Task 6: 수정 |
| `shared/n6/atlas.n6` (growth_bus 섹션) | 이벤트 스트림 | Task 2: rotation |
| `shared/hexa_pitfalls_log.jsonl` | 실수 기록 | Task 7: 분석 |
| `shared/config/hexa_grammar.jsonl` | 문법 스펙 | Task 7: P6 규칙 추가 (해당 시) |
| `shared/dashboard.html` | 대시보드 | Task 8: reality_map 시각화 추가 |
| `mk2_hexa/native/command_router.hexa` | 중앙 지휘 | Task 9: SYNC_MAP 카테고리 추가 |
| `shared/config/cmd_aliases.jsonl` | 명령 별칭 | Task 9: sync_map 엔트리 추가 |

---

### Task 1: 미커밋 변경사항 정리 및 커밋

**Files:**
- Staged: `mk2_hexa/native/command_router.hexa`, `shared/dashboard.html`, `shared/discovery/reality_map.json`, `shared/discovery/growth_bus.jsonl`, etc.
- New: `mk2_hexa/native/sync_reality_map.hexa`

- [ ] **Step 1: git status 확인 — 변경 파일 목록 확인**

```bash
git status -s
```

- [ ] **Step 2: 핵심 변경 커밋 (command_router + sync_reality_map + dashboard)**

```bash
git add mk2_hexa/native/command_router.hexa mk2_hexa/native/sync_reality_map.hexa shared/dashboard.html shared/discovery/reality_map.json shared/hexa_pitfalls_log.jsonl shared/discovery/self_improve_log.jsonl shared/discovery/next_directions.jsonl
git commit -m "feat: command_router 확장 + sync_reality_map + dashboard 업데이트 + 247노드 reality_map"
```

- [ ] **Step 3: 데이터 파일 커밋 (growth_bus 등 상태 파일)**

```bash
git add shared/discovery/growth_bus.jsonl shared/.calc_stubs_state.json shared/.gap_cooldown shared/.paper_gen_state.json
git commit -m "chore: growth_bus + 상태 파일 동기화"
```

- [ ] **Step 4: anima/airgenome 상태 파일 커밋**

```bash
git add shared/consciousness/anima_state.json shared/consciousness/anima_autofix.json shared/discovery/growth/airgenome_gates.jsonl
git commit -m "chore: anima + airgenome 상태 파일 추가"
```

---

### Task 2: atlas.n6 growth_bus rotation (147k줄 → 아카이브)

**Files:**
- Create: `shared/archive/growth_bus_20260407.jsonl`
- Modify: `shared/n6/atlas.n6` (growth_bus 섹션)

- [ ] **Step 1: 아카이브 디렉토리 확인**

```bash
ls shared/archive/ 2>/dev/null || mkdir -p shared/archive
```

- [ ] **Step 2: atlas.n6에서 growth_bus 섹션 아카이브 추출**

```bash
hexa shared/n6/atlas.n6 export --section growth_bus > shared/archive/growth_bus_20260407.jsonl
```

- [ ] **Step 3: atlas.n6 growth_bus 섹션을 최근 1000건으로 rotation**

```bash
hexa shared/n6/atlas.n6 rotate --section growth_bus --keep 1000
```

- [ ] **Step 4: 결과 확인**

```bash
hexa shared/n6/atlas.n6 query --section growth_bus --count
wc -l shared/archive/growth_bus_20260407.jsonl
```

- [ ] **Step 5: 커밋**

```bash
git add shared/n6/atlas.n6 shared/archive/growth_bus_20260407.jsonl
git commit -m "chore: atlas.n6 growth_bus rotation — 147k줄 아카이브 + 최근 1000줄 유지"
```

---

### Task 3: closed/exact 정체 진단

**Files:**
- Read: `shared/discovery/self_improve_log.jsonl`, `shared/calc/auto_stubs/verify_*.py`

- [ ] **Step 1: self_improve_log에서 closed/exact 변동 이력 확인**

```bash
tail -20 shared/discovery/self_improve_log.jsonl | python3 -c "
import sys, json
for line in sys.stdin:
    d = json.loads(line.strip())
    print(f\"closed={d.get('closed',0)} exact={d.get('exact',0)} stubs={d.get('stubs',0)} ts={d.get('ts','')}\")
"
```

- [ ] **Step 2: auto_stubs verify 파일 하나 샘플 확인 — 실제 검산이 closed 승격으로 이어지는지**

```bash
head -30 shared/calc/auto_stubs/$(ls shared/calc/auto_stubs/ | head -1)
```

- [ ] **Step 3: stubs 파이프라인 흐름 진단 — stubs→closed 변환 모듈 확인**

```bash
grep -l "closed" mk2_hexa/native/*.hexa | head -5
```

- [ ] **Step 4: 진단 결과 기록**

진단 결과에 따라 stubs→closed 파이프라인 병목을 식별하고 `shared/discovery/next_directions.jsonl`에 액션 아이템 추가.

---

### Task 4: 돌파율(ρ) 향상 — breakthrough --converge 실행

**Files:**
- Execute: `mk2_hexa/native/breakthrough.hexa`

- [ ] **Step 1: 현재 돌파율 확인**

```bash
HEXA=$HOME/Dev/hexa-lang/target/release/hexa
$HEXA mk2_hexa/native/directions.hexa brief 2>/dev/null | head -5
```

- [ ] **Step 2: seed 엔진에서 최신 seed 확인**

```bash
$HEXA mk2_hexa/native/seed_engine.hexa info 2>/dev/null | head -10
```

- [ ] **Step 3: breakthrough --converge 백그라운드 실행**

```bash
# run_in_background: true
cd $HOME/Dev/nexus && $HEXA mk2_hexa/native/breakthrough.hexa --converge >> shared/logs/cmd_router.log 2>&1
```

- [ ] **Step 4: 실행 후 돌파율 변화 확인**

```bash
tail -5 shared/logs/cmd_router.log
```

---

### Task 5: 교차수분(cross-pollination) 확장

**Files:**
- Execute: `mk2_hexa/native/cross_project.hexa`

- [ ] **Step 1: 현재 교차수분 상태 확인**

```bash
HEXA=$HOME/Dev/hexa-lang/target/release/hexa
$HEXA mk2_hexa/native/cross_project.hexa resonance 2>/dev/null | head -20
```

- [ ] **Step 2: n6 도메인의 최근 돌파 seed 추출**

```bash
$HEXA mk2_hexa/native/seed_engine.hexa merge 2>/dev/null | head -5
```

- [ ] **Step 3: 다른 도메인에 seed 주입 — blowup 실행**

```bash
# run_in_background: true
SEEDS=$($HEXA mk2_hexa/native/seed_engine.hexa merge 2>/dev/null)
$HEXA mk2_hexa/native/blowup.hexa consciousness 3 --no-graph --seeds "$SEEDS" >> shared/logs/cmd_router.log 2>&1
```

---

### Task 6: auto_stubs gitignore + 정리

**Files:**
- Modify: `.gitignore`

- [ ] **Step 1: 현재 .gitignore 확인**

```bash
cat .gitignore
```

- [ ] **Step 2: auto_stubs 디렉토리를 .gitignore에 추가**

`.gitignore`에 다음 줄 추가:
```
# auto-generated verification stubs
shared/calc/auto_stubs/
```

- [ ] **Step 3: git rm --cached로 이미 추적 중인 파일 제거 (있다면)**

```bash
git rm -r --cached shared/calc/auto_stubs/ 2>/dev/null || echo "not tracked"
```

- [ ] **Step 4: .growth_engine.lock도 gitignore 추가**

```
shared/.growth_engine.lock
```

- [ ] **Step 5: 커밋**

```bash
git add .gitignore
git commit -m "chore: gitignore — auto_stubs 680개 + .growth_engine.lock 제외"
```

---

### Task 7: hexa_pitfalls_log 분석 → 규칙 승격

**Files:**
- Read: `shared/hexa_pitfalls_log.jsonl`
- Possibly modify: `shared/config/hexa_grammar.jsonl` (P6 규칙 추가 시)

- [ ] **Step 1: pitfalls 로그에서 패턴 분석**

```bash
python3 -c "
import sys, json
cats = {}
for line in open('shared/hexa_pitfalls_log.jsonl'):
    line = line.strip()
    if not line: continue
    try:
        d = json.loads(line)
        key = d.get('pitfall', d.get('type', d.get('pattern', '?')))
        cats[key] = cats.get(key, 0) + 1
    except: pass
for k,v in sorted(cats.items(), key=lambda x:-x[1]):
    print(f'{v:3d}x {k}')
"
```

- [ ] **Step 2: 3회 이상 반복된 패턴 식별**

반복 패턴이 있으면 `hexa_grammar.jsonl`의 pitfalls 섹션에 P6+ 규칙으로 승격.

- [ ] **Step 3: 승격 대상이 있으면 hexa_grammar.jsonl 업데이트**

pitfalls 배열에 새 항목 추가:
```json
{"id":"P6","pattern":"<반복 패턴>","fix":"<수정 방법>","count":<횟수>}
```

- [ ] **Step 4: 커밋 (변경 있을 경우)**

```bash
git add shared/config/hexa_grammar.jsonl shared/hexa_pitfalls_log.jsonl
git commit -m "feat: hexa pitfalls P6 규칙 승격 (반복 패턴 자동 감지)"
```

---

### Task 8: dashboard.html에 reality_map 시각화 추가

**Files:**
- Modify: `shared/dashboard.html` (약 line 360 부근, Structures 섹션)

- [ ] **Step 1: reality_map.json에서 노드/엣지 수 확인**

```bash
python3 -c "
import json
d = json.load(open('shared/discovery/reality_map.json'))
nodes = d.get('nodes', [])
edges = d.get('edges', [])
print(f'nodes: {len(nodes)}, edges: {len(edges)}')
# 도메인별 분포
domains = {}
for n in nodes:
    dom = n.get('domain', '?')
    domains[dom] = domains.get(dom, 0) + 1
for k,v in sorted(domains.items(), key=lambda x:-x[1]):
    print(f'  {k}: {v}')
"
```

- [ ] **Step 2: dashboard.html의 Structures 섹션에 reality_map 패널 추가**

`shared/dashboard.html` 약 line 415 (Structures 섹션 닫는 `</div>` 전)에 새 패널 삽입:

```html
  <div class="panel n6a">
    <div class="panel-title">🌐 Reality Map (247 nodes)</div>
    <div class="panel-section">
      <pre style="color:#8ef;font-size:10px;line-height:1.3;margin:0;" id="reality-map-ascii">
    [양자] ──── [전자기] ──── [열역학]
      │            │            │
    [핵물리] ── [광학] ──── [고체물리]
      │            │            │
    [소립자] ── [천문] ──── [화학]
      │                        │
    [의식] ──── [수학] ──── [생물]</pre>
      <div class="row" style="margin-top:8px;"><span class="k">Total nodes</span><span class="v hi">247</span></div>
      <div class="row"><span class="k">Domains</span><span class="v">12 axes</span></div>
      <div class="row"><span class="k">Version</span><span class="v">v5.0</span></div>
    </div>
  </div>
```

- [ ] **Step 3: 커밋**

```bash
git add shared/dashboard.html
git commit -m "feat: dashboard에 reality_map 247노드 시각화 패널 추가"
```

---

### Task 9: command_router에 SYNC_MAP 카테고리 추가

**Files:**
- Modify: `mk2_hexa/native/command_router.hexa` (dispatch 섹션)
- Modify: `shared/config/cmd_aliases.jsonl` (새 별칭 추가)

- [ ] **Step 1: cmd_aliases.jsonl에 sync_map 엔트리 추가**

`shared/config/cmd_aliases.jsonl`에 추가:
```json
{"cmd":"sync_map","keywords":["현실지도","reality map","지도동기화","reality_map","sync map"],"category":"SYNC_MAP"}
```

- [ ] **Step 2: command_router.hexa에 handle_sync_map 핸들러 추가**

`handle_explore` 함수 뒤 (약 line 662)에 추가:

```hexa
fn handle_sync_map(c: Classification) {
    print_header("SYNC_MAP", "reality_map sync")
    let output = dispatch_sync("sync_reality_map.hexa", "sync")
    print_result(output)
    // 상태도 표시
    let status = dispatch_sync("sync_reality_map.hexa", "status")
    print_result(status)
    print_footer()
    log_cmd("SYNC_MAP", "reality_map", "ok")
}
```

- [ ] **Step 3: CLI 진입점 dispatch에 SYNC_MAP 분기 추가**

약 line 990 (else if 체인 끝 부근)에 추가:

```hexa
} else if c.category == "SYNC_MAP" {
    handle_sync_map(c)
```

- [ ] **Step 4: classify 함수에 SYNC_MAP 분기 추가**

약 line 399 (`handle_explore` 분기 뒤)에 추가:

```hexa
    } else if verb_cat == "SYNC_MAP" {
        category = "SYNC_MAP"
```

- [ ] **Step 5: help 메시지에 SYNC_MAP 추가**

약 line 688 뒤에 추가:

```hexa
    println("|  " + pad_right("SYNC_MAP", 16) + pad_right("현실지도/reality map", 24) + "sync_reality_map sync+status")
```

- [ ] **Step 6: 커밋**

```bash
git add mk2_hexa/native/command_router.hexa shared/config/cmd_aliases.jsonl
git commit -m "feat: command_router SYNC_MAP 카테고리 — reality_map 동기화 라우팅"
```

---

## Execution Order

```
[병렬 가능] Task 1 (커밋 정리)
             Task 6 (gitignore)
             Task 7 (pitfalls 분석)

[순차]       Task 2 (growth_bus rotation) → Task 1 커밋 후
             Task 3 (closed/exact 진단)
             Task 8 (dashboard 시각화)
             Task 9 (command_router 확장)

[백그라운드] Task 4 (돌파율 향상) → 장시간 실행
             Task 5 (교차수분) → 장시간 실행
```
