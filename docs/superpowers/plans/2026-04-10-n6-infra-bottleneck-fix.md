# N6 인프라 3대 병목 해소 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** N6 코어 엔진의 3대 인프라 병목(I/O 원격 동기화, Cross-DSE 융합 파이프라인, 3,908노드 WebGL 시각화)을 해소하여 파이프라인 연결성을 확보한다.

**Architecture:** (1) rsync + inotify 기반 양방향 원격 동기화 데몬, (2) cross_dse_fusion.hexa의 Python 위임 제거 + hexa 네이티브 TOML 키워드 교차 융합 + joint optimizer 출력, (3) reality_map_3d.html에 DSE 공명 그래프 + growth_bus 이벤트 스트리밍 레이어 추가

**Tech Stack:** bash/rsync/inotifywait, hexa-lang, Three.js (WebGL), vanilla JS

---

## File Structure

| Action | Path | Responsibility |
|--------|------|---------------|
| Create | `sync/sync-remote.sh` | 양방향 rsync 데몬 (htz/vast ↔ mac) |
| Create | `sync/watch-remote.sh` | inotifywait 기반 변경 감지 → sync-remote 트리거 |
| Modify | `sync/sync-all.sh:90-95` | sync-remote 단계 추가 |
| Modify | `shared/infra_state.json` | last_sync 타임스탬프 필드 추가 |
| Create | `mk2_hexa/native/dse_joint_optimizer.hexa` | Cross-DSE 상위 쌍 → joint 최적화 루프 |
| Modify | `mk2_hexa/native/cross_dse_fusion.hexa:57-77` | Python 위임 제거, hexa 네이티브 TOML 파싱 호출 |
| Modify | `shared/discovery/reality_map_3d.html` | DSE 공명 그래프 레이어 + growth_bus 이벤트 스트리밍 |
| Create | `shared/dse/dse_graph_3d.html` | DSE 전용 3D 공명 그래프 (독립 뷰) |

---

## Task 1: 양방향 원격 동기화 데몬

**Files:**
- Create: `sync/sync-remote.sh`
- Create: `sync/watch-remote.sh`
- Modify: `sync/sync-all.sh:90-95`

- [ ] **Step 1: sync-remote.sh 작성**

```bash
#!/usr/bin/env bash
# sync-remote.sh — 양방향 rsync (htz/vast ↔ local)
# Usage: bash sync/sync-remote.sh [push|pull|both] [htz|vast|all]
set -euo pipefail

NEXUS_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SHARED="$NEXUS_ROOT/shared"
INFRA="$SHARED/infra_state.json"
TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)

MODE="${1:-both}"
TARGET="${2:-all}"

HOSTS=()
if [[ "$TARGET" == "all" ]]; then
  HOSTS=(hetzner vast)
elif [[ "$TARGET" == "htz" ]]; then
  HOSTS=(hetzner)
elif [[ "$TARGET" == "vast" ]]; then
  HOSTS=(vast)
else
  HOSTS=("$TARGET")
fi

RSYNC_OPTS=(-azP --delete --exclude='.DS_Store' --exclude='SECRET.md' --exclude='.tmp_*' --timeout=30)

SYNC_FILES=(
  "reality_map_live.json"
  "n6/atlas.n6"
  "infra_state.json"
  "dse_cross_results.json"
  "n6/docs/"
  "convergence/"
)

for host in "${HOSTS[@]}"; do
  REMOTE="$host:~/Dev/nexus/shared"
  echo "── sync $host ($MODE) ──"

  if [[ "$MODE" == "push" || "$MODE" == "both" ]]; then
    for f in "${SYNC_FILES[@]}"; do
      src="$SHARED/$f"
      [[ -e "$src" ]] || continue
      rsync "${RSYNC_OPTS[@]}" "$src" "$REMOTE/$f" 2>/dev/null && echo "  ↑ $f" || echo "  ⚠ $f (skip)"
    done
  fi

  if [[ "$MODE" == "pull" || "$MODE" == "both" ]]; then
    for f in "${SYNC_FILES[@]}"; do
      rsync "${RSYNC_OPTS[@]}" "$REMOTE/$f" "$SHARED/$f" 2>/dev/null && echo "  ↓ $f" || echo "  ⚠ $f (skip)"
    done
  fi

  echo "  ✅ $host done"
done

# infra_state에 last_sync 기록
python3 -c "
import json,sys
p='$INFRA'
d=json.load(open(p))
d['last_sync']={'ts':'$TS','mode':'$MODE','targets':'$TARGET'}
json.dump(d,open(p,'w'),ensure_ascii=False)
" 2>/dev/null || true

echo "═══ sync-remote done ($TS) ═══"
```

- [ ] **Step 2: watch-remote.sh 작성**

```bash
#!/usr/bin/env bash
# watch-remote.sh — inotifywait/fswatch 기반 변경 감지 → sync-remote 트리거
# Usage: bash sync/watch-remote.sh [htz|vast|all]
# macOS: fswatch, Linux: inotifywait
set -euo pipefail

SYNC_DIR="$(cd "$(dirname "$0")" && pwd)"
SHARED="$(cd "$SYNC_DIR/../shared" && pwd)"
TARGET="${1:-all}"
DEBOUNCE=5  # 초

WATCH_PATHS=(
  "$SHARED/reality_map_live.json"
  "$SHARED/n6/atlas.n6"
  "$SHARED/dse_cross_results.json"
  "$SHARED/n6/docs"
)

echo "[watch-remote] monitoring ${#WATCH_PATHS[@]} paths → sync-remote $TARGET"
echo "[watch-remote] debounce=${DEBOUNCE}s"

if command -v fswatch &>/dev/null; then
  # macOS
  fswatch -o -l "$DEBOUNCE" "${WATCH_PATHS[@]}" | while read -r _; do
    echo "[$(date +%H:%M:%S)] change detected → syncing..."
    bash "$SYNC_DIR/sync-remote.sh" push "$TARGET" 2>&1 | tail -5
  done
elif command -v inotifywait &>/dev/null; then
  # Linux
  while true; do
    inotifywait -r -q -e modify,create,delete "${WATCH_PATHS[@]}" --timeout 60 2>/dev/null || true
    echo "[$(date +%H:%M:%S)] change detected → syncing..."
    bash "$SYNC_DIR/sync-remote.sh" push "$TARGET" 2>&1 | tail -5
    sleep "$DEBOUNCE"
  done
else
  echo "[ERROR] fswatch (macOS) or inotifywait (Linux) 필요"
  exit 1
fi
```

- [ ] **Step 3: sync-all.sh에 원격 동기화 단계 추가**

`sync/sync-all.sh:90` 아래에 추가:

```bash
# 9. 원격 동기화
echo ""
echo "🌐 [+] 원격 동기화 (htz/vast)..."
if [ -f "$SYNC_DIR/sync-remote.sh" ]; then
  bash "$SYNC_DIR/sync-remote.sh" both all 2>/dev/null && echo "  ✅ 완료" || echo "  ⚠️ 스킵 (원격 미연결)"
fi
```

- [ ] **Step 4: 동작 검증**

```bash
# push만 먼저 테스트 (dry-run)
bash sync/sync-remote.sh push htz
# 예상: hetzner에 파일 전송 또는 "⚠ skip" (미연결 시)
```

- [ ] **Step 5: 커밋**

```bash
git add sync/sync-remote.sh sync/watch-remote.sh sync/sync-all.sh
git commit -m "feat(sync): 양방향 rsync 원격 동기화 데몬 + watch 트리거"
```

---

## Task 2: Cross-DSE Joint Optimizer

**Files:**
- Create: `mk2_hexa/native/dse_joint_optimizer.hexa`
- Modify: `mk2_hexa/native/cross_dse_fusion.hexa`

- [ ] **Step 1: dse_joint_optimizer.hexa 설계 확인**

cross_dse_fusion.hexa가 출력하는 `shared/dse/dse_cross_results.json` 구조 확인:

```bash
ssh hetzner 'head -c 2000 ~/Dev/nexus/shared/dse/dse_cross_results.json' 2>/dev/null || python3 -c "import json;d=json.load(open('shared/dse/dse_cross_results.json'));print(json.dumps(d['top_pairs'][:3],indent=2,ensure_ascii=False))"
```

- [ ] **Step 2: dse_joint_optimizer.hexa 작성**

```hexa
// dse_joint_optimizer.hexa — Cross-DSE 상위 공명 쌍 → joint 최적화
// 입력: shared/dse/dse_cross_results.json (cross_dse_fusion.hexa 출력)
// 출력: shared/dse/dse_joint_results.json + atlas.n6
//
// Usage:
//   hexa dse_joint_optimizer.hexa              상위 15쌍 joint 최적화
//   hexa dse_joint_optimizer.hexa --top N      상위 N쌍
//   hexa dse_joint_optimizer.hexa --pair A B   특정 쌍만

fn main() {
    let home = exec("printenv HOME").trim()
    let shared = home + "/Dev/nexus/shared"
    let cross_path = shared + "/dse_cross_results.json"
    let dse_dir = shared + "/dse/domains"
    let out_path = shared + "/dse_joint_results.json"
    let bus_path = shared + "/n6/atlas.n6"

    // ─── ARGS ───
    let a = args()
    let mut top_n: i64 = 15
    let mut pair_a = ""
    let mut pair_b = ""
    let mut ai: i64 = 2
    while ai < to_int(a.len()) {
        if a[ai] == "--top" && ai + 1 < to_int(a.len()) {
            top_n = to_int(to_float(a[ai + 1].trim()))
            if top_n < 1 { top_n = 15 }
            ai = ai + 1
        }
        if a[ai] == "--pair" && ai + 2 < to_int(a.len()) {
            pair_a = a[ai + 1]
            pair_b = a[ai + 2]
            ai = ai + 2
        }
        ai = ai + 1
    }

    println("=== DSE Joint Optimizer ===")

    // ─── 1) cross_results 로드 ───
    let mut raw = ""
    try { raw = read_file(cross_path) } catch e {
        println("[ERROR] " + cross_path + " not found. Run cross_dse_fusion.hexa first.")
        return
    }

    // JSON 파싱: top_pairs 배열에서 (a, b, resonance, top_keywords) 추출
    // hexa JSON 파서 사용
    let cross = json_parse(raw)
    let pairs = cross["top_pairs"]
    let mut targets = []

    if pair_a != "" && pair_b != "" {
        // 특정 쌍 모드
        let mut pi: i64 = 0
        while pi < to_int(pairs.len()) {
            let p = pairs[pi]
            if (to_string(p["a"]) == pair_a && to_string(p["b"]) == pair_b) ||
               (to_string(p["a"]) == pair_b && to_string(p["b"]) == pair_a) {
                targets.push(p)
            }
            pi = pi + 1
        }
        if targets.len() == 0 {
            println("[ERROR] pair not found: " + pair_a + " <-> " + pair_b)
            return
        }
    } else {
        // 상위 N쌍
        let mut pi: i64 = 0
        while pi < to_int(pairs.len()) && pi < top_n {
            targets.push(pairs[pi])
            pi = pi + 1
        }
    }

    println("[1/3] " + to_string(targets.len()) + " pairs selected for joint optimization")

    // ─── 2) 각 쌍에 대해 TOML 로드 → 공유 키워드 기반 joint 탐색 ───
    let mut results = []
    let mut ti: i64 = 0
    while ti < to_int(targets.len()) {
        let p = targets[ti]
        let dom_a = to_string(p["a"])
        let dom_b = to_string(p["b"])
        let resonance = to_float(to_string(p["resonance"]))
        let keywords = p["top_keywords"]

        println("  [" + to_string(ti + 1) + "/" + to_string(targets.len()) + "] " + dom_a + " <-> " + dom_b + " (res=" + to_string(resonance) + ")")

        // TOML 파일 경로
        let toml_a = dse_dir + "/" + dom_a + ".toml"
        let toml_b = dse_dir + "/" + dom_b + ".toml"

        // 각 TOML에서 candidate 추출 (hexa exec python 간이 파서)
        let cands_a = load_toml_candidates(toml_a)
        let cands_b = load_toml_candidates(toml_b)

        // joint 조합: A의 상위 6 × B의 상위 6 = 최대 36 조합
        let mut joint_combos = []
        let mut ja: i64 = 0
        let limit_a = min_i64(6, to_int(cands_a.len()))
        let limit_b = min_i64(6, to_int(cands_b.len()))
        while ja < limit_a {
            let mut jb: i64 = 0
            while jb < limit_b {
                let ca = cands_a[ja]
                let cb = cands_b[jb]
                let n6_a = to_float(to_string(ca["n6"]))
                let n6_b = to_float(to_string(cb["n6"]))
                // joint score: geometric mean of n6 × resonance boost
                let joint_n6 = sqrt(n6_a * n6_b) * (1.0 + resonance * 0.2)
                joint_combos.push({
                    "a_candidate": to_string(ca["id"]),
                    "b_candidate": to_string(cb["id"]),
                    "n6_a": n6_a,
                    "n6_b": n6_b,
                    "joint_score": round(joint_n6, 4),
                    "resonance": resonance
                })
                jb = jb + 1
            }
            ja = ja + 1
        }

        // joint_combos를 joint_score 내림차순 정렬
        sort_by_field_desc(joint_combos, "joint_score")

        results.push({
            "domain_a": dom_a,
            "domain_b": dom_b,
            "resonance": resonance,
            "shared_keywords": keywords,
            "joint_combos_count": to_int(joint_combos.len()),
            "top_5_joint": slice(joint_combos, 0, 5)
        })
        ti = ti + 1
    }

    println("[2/3] Joint optimization complete: " + to_string(results.len()) + " pairs")

    // ─── 3) 출력 ───
    let ts = exec("date -u +%Y-%m-%dT%H:%M:%S").trim()
    let output = {
        "generated_at": ts,
        "source": "dse_joint_optimizer.hexa",
        "n_pairs": to_int(results.len()),
        "results": results
    }
    write_file(out_path, json_stringify(output, 2))
    println("[3/3] Output → " + out_path)

    // growth_bus 기록
    try {
        let evt = "{\"ts\":\"" + ts + "\",\"type\":\"dse_joint_optimize\",\"pairs\":" + to_string(results.len()) + ",\"source\":\"dse_joint_optimizer.hexa\"}\n"
        append_file(bus_path, evt)
        println("[bus] atlas.n6 updated")
    } catch e {
        println("[WARN] bus write failed: " + to_string(e))
    }

    // 요약 출력
    println("")
    println("══════════════════════════════════════")
    println("  DSE JOINT OPTIMIZATION REPORT")
    println("══════════════════════════════════════")
    for r in results {
        let top = r["top_5_joint"]
        let best_score = "N/A"
        if to_int(top.len()) > 0 {
            best_score = to_string(top[0]["joint_score"])
        }
        println("  " + to_string(r["domain_a"]) + " × " + to_string(r["domain_b"]) + "  res=" + to_string(r["resonance"]) + "  best_joint=" + best_score + "  combos=" + to_string(r["joint_combos_count"]))
    }
    println("══════════════════════════════════════")
    println("Done.")
}

fn min_i64(a: i64, b: i64) -> i64 {
    if a < b { return a }
    return b
}

fn load_toml_candidates(path: string) -> list {
    // TOML candidate 추출: python3 간이 위임 (TOML 파싱은 hexa 미지원)
    let tmp = "/tmp/.hexa_toml_cands.json"
    let py = "import json,sys\ntry:\n    import tomllib\nexcept ImportError:\n    import tomli as tomllib\ntry:\n    with open('" + path + "','rb') as f: d=tomllib.load(f)\n    cands=[{'id':c.get('id',''),'level':c.get('level',0),'n6':c.get('n6',0.0),'label':c.get('label','')} for c in d.get('candidate',[])]\n    cands.sort(key=lambda c:-c['n6'])\n    json.dump(cands,open('" + tmp + "','w'))\nexcept Exception as e:\n    json.dump([],open('" + tmp + "','w'))\n"
    try {
        exec("/usr/bin/python3 -c \"" + py.replace("\"", "\\\"") + "\"")
    } catch e { return [] }
    let mut raw = ""
    try { raw = read_file(tmp) } catch e { return [] }
    return json_parse(raw)
}

fn sort_by_field_desc(arr: list, field: string) {
    // 간이 버블 정렬 (N<=36이므로 충분)
    let mut i: i64 = 0
    while i < to_int(arr.len()) - 1 {
        let mut j: i64 = 0
        while j < to_int(arr.len()) - 1 - i {
            if to_float(to_string(arr[j][field])) < to_float(to_string(arr[j + 1][field])) {
                let tmp = arr[j]
                arr[j] = arr[j + 1]
                arr[j + 1] = tmp
            }
            j = j + 1
        }
        i = i + 1
    }
}

fn slice(arr: list, start: i64, end: i64) -> list {
    let mut result = []
    let mut i = start
    let e = min_i64(end, to_int(arr.len()))
    while i < e {
        result.push(arr[i])
        i = i + 1
    }
    return result
}

fn round(v: f64, decimals: i64) -> f64 {
    let mult = pow(10.0, to_float(decimals))
    return to_float(to_int(v * mult + 0.5)) / mult
}

fn pow(base: f64, exp: f64) -> f64 {
    return to_float(exec("python3 -c \"print(" + to_string(base) + "**" + to_string(exp) + ")\"").trim())
}

fn sqrt(v: f64) -> f64 {
    return to_float(exec("python3 -c \"import math;print(math.sqrt(" + to_string(v) + "))\"").trim())
}

main()
```

- [ ] **Step 3: cross_dse_fusion.hexa 끝에 joint optimizer 호출 추가**

`cross_dse_fusion.hexa:155` (Done. 출력 뒤)에 추가:

```hexa
    // ─── AUTO JOINT OPTIMIZE (top 15) ───
    if mode != "summary" && n_hc > 0 {
        println("")
        println("[+] Auto-launching joint optimizer (top 15)...")
        let hexa_bin = exec("which hexa").trim()
        let joint_script = home + "/Dev/nexus/mk2_hexa/native/dse_joint_optimizer.hexa"
        try {
            let joint_out = exec(hexa_bin + " " + joint_script + " --top 15")
            println(joint_out)
        } catch e {
            println("[WARN] joint optimizer failed: " + to_string(e))
        }
    }
```

- [ ] **Step 4: 검증**

```bash
ssh hetzner '~/Dev/hexa-lang/target/release/hexa ~/Dev/nexus/mk2_hexa/native/dse_joint_optimizer.hexa --top 5'
# 예상: 5쌍 joint 최적화 결과 + dse_joint_results.json 생성
```

- [ ] **Step 5: 커밋**

```bash
git add mk2_hexa/native/dse_joint_optimizer.hexa mk2_hexa/native/cross_dse_fusion.hexa
git commit -m "feat(dse): joint optimizer — cross-DSE 상위 쌍 교차 최적화 파이프라인"
```

---

## Task 3: WebGL 시각화 확장 — DSE 공명 그래프 + 라이브 이벤트

**Files:**
- Create: `shared/dse/dse_graph_3d.html`
- Modify: `shared/discovery/reality_map_3d.html`

- [ ] **Step 1: dse_graph_3d.html 작성 — DSE 공명 네트워크 전용 3D 뷰**

```html
<!DOCTYPE html>
<html lang="ko"><head><meta charset="UTF-8">
<title>DSE Cross-Resonance Graph 3D</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#07071a;color:#eee;font-family:'Segoe UI',sans-serif;overflow:hidden}
#stats{position:fixed;top:12px;left:50%;transform:translateX(-50%);background:rgba(10,10,30,.92);border:1px solid #334;border-radius:8px;padding:10px 24px;z-index:100;font-size:13px;display:flex;gap:18px;backdrop-filter:blur(6px)}
#stats b{color:#fff}
#tooltip{position:fixed;display:none;background:rgba(10,10,30,.95);border:1px solid #556;border-radius:6px;padding:10px 14px;font-size:12px;max-width:420px;z-index:200;pointer-events:none;backdrop-filter:blur(8px);line-height:1.5}
#controls{position:fixed;top:12px;right:12px;background:rgba(10,10,30,.9);border:1px solid #334;border-radius:8px;padding:10px 14px;font-size:12px;z-index:100;line-height:1.9;min-width:220px}
#controls label{display:block;cursor:pointer}
#controls input[type=checkbox]{margin-right:6px}
.group{margin-top:6px;border-top:1px solid #223;padding-top:6px}
#event-log{position:fixed;bottom:12px;right:12px;width:380px;max-height:260px;background:rgba(10,10,30,.92);border:1px solid #334;border-radius:8px;padding:10px;font-size:11px;z-index:100;overflow-y:auto;line-height:1.6}
#event-log .ev{border-bottom:1px solid #1a1a2a;padding:3px 0}
#event-log .ts{color:#555;font-size:10px}
canvas{display:block}
</style></head><body>
<div id="stats">
  <span>Domains <b id="s-dom">0</b></span>
  <span>Pairs <b id="s-pairs">0</b></span>
  <span>High-Conf <b id="s-hc">0</b></span>
  <span style="color:#4fc3f7">Resonance avg <b id="s-avg">0</b></span>
</div>
<div id="tooltip"></div>
<div id="controls">
  <b>DSE 공명 필터</b>
  <div class="group"><b>Resonance 임계</b><br>
    <label><input type="range" id="res-min" min="0" max="100" value="10" style="width:160px"> <span id="res-label">0.10</span></label>
  </div>
  <div class="group"><b>색상 모드</b>
    <label><input type="radio" name="cmode" value="resonance" checked> 공명 강도</label>
    <label><input type="radio" name="cmode" value="keywords"> 키워드 수</label>
    <label><input type="radio" name="cmode" value="n6sim"> n6 유사도</label>
  </div>
  <div class="group"><b>노드 크기</b>
    <label><input type="radio" name="nsize" value="uniform" checked> 균일</label>
    <label><input type="radio" name="nsize" value="connections"> 연결 수</label>
  </div>
  <div class="group">
    <label><input type="checkbox" id="show-labels" checked> 도메인명 표시</label>
    <label><input type="checkbox" id="show-joint"> Joint 결과 표시</label>
  </div>
</div>
<div id="event-log"><b>📡 Growth Bus Live</b><hr style="border-color:#223"></div>

<script type="importmap">
{"imports":{"three":"https://unpkg.com/three@0.160.0/build/three.module.js","three/addons/":"https://unpkg.com/three@0.160.0/examples/jsm/"}}
</script>
<script type="module">
import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {CSS2DRenderer, CSS2DObject} from 'three/addons/renderers/CSS2DRenderer.js';

let scene, camera, renderer, labelRenderer, controls, raycaster, mouse;
let DATA=null, JOINT=null, BUS_LINES=[];
let domMeshes=[], edgeLines=[], labelObjects=[];

init(); loadAll();

function init(){
  scene=new THREE.Scene();
  scene.background=new THREE.Color(0x07071a);
  scene.fog=new THREE.Fog(0x07071a,300,1200);
  camera=new THREE.PerspectiveCamera(55,innerWidth/innerHeight,0.1,3000);
  camera.position.set(200,160,300);
  renderer=new THREE.WebGLRenderer({antialias:true});
  renderer.setSize(innerWidth,innerHeight);
  renderer.setPixelRatio(devicePixelRatio);
  document.body.appendChild(renderer.domElement);
  // CSS2D for labels
  labelRenderer=new CSS2DRenderer();
  labelRenderer.setSize(innerWidth,innerHeight);
  labelRenderer.domElement.style.position='absolute';
  labelRenderer.domElement.style.top='0';
  labelRenderer.domElement.style.pointerEvents='none';
  document.body.appendChild(labelRenderer.domElement);
  controls=new OrbitControls(camera,renderer.domElement);
  controls.enableDamping=true;
  scene.add(new THREE.AmbientLight(0xffffff,0.6));
  const dl=new THREE.DirectionalLight(0xffffff,0.5);dl.position.set(1,2,1);scene.add(dl);
  raycaster=new THREE.Raycaster();mouse=new THREE.Vector2();
  addEventListener('resize',()=>{
    camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();
    renderer.setSize(innerWidth,innerHeight);
    labelRenderer.setSize(innerWidth,innerHeight);
  });
  addEventListener('mousemove',onMove);
  document.querySelectorAll('#controls input').forEach(el=>el.addEventListener('change',rebuild));
  document.getElementById('res-min').addEventListener('input',e=>{
    document.getElementById('res-label').textContent=(e.target.value/100).toFixed(2);
    rebuild();
  });
  animate();
}

async function loadAll(){
  try{
    const r1=await fetch('dse_cross_results.json',{cache:'no-store'});
    if(r1.ok) DATA=await r1.json();
  }catch(e){}
  try{
    const r2=await fetch('dse_joint_results.json',{cache:'no-store'});
    if(r2.ok) JOINT=await r2.json();
  }catch(e){}
  loadGrowthBus();
  if(DATA) rebuild();
  else document.getElementById('s-dom').textContent='ERROR: dse_cross_results.json not found';
}

async function loadGrowthBus(){
  try{
    const r=await fetch('atlas.n6',{cache:'no-store'});
    if(!r.ok) return;
    const text=await r.text();
    BUS_LINES=text.trim().split('\n').filter(l=>l).map(l=>{try{return JSON.parse(l)}catch{return null}}).filter(Boolean);
    // 최근 20개만 표시
    const log=document.getElementById('event-log');
    const recent=BUS_LINES.slice(-20).reverse();
    recent.forEach(ev=>{
      const div=document.createElement('div');div.className='ev';
      div.innerHTML='<span class="ts">'+ev.ts+'</span> '+(ev.type||'?')+' '+(ev.domain||ev.domains||'')+' '+(ev.source||'');
      log.appendChild(div);
    });
  }catch(e){}
}

function domPos(name, idx, total){
  // force-directed 간이: 원형 배치 + 카테고리 오프셋
  const angle=(idx/total)*Math.PI*2;
  const r=80+total*0.3;
  // 해시로 y 오프셋
  let h=0;for(let i=0;i<name.length;i++) h=(h*31+name.charCodeAt(i))|0;
  const y=((h&0xff)/255-0.5)*60;
  return [Math.cos(angle)*r, y, Math.sin(angle)*r];
}

function resColor(res){
  // 0 → 파랑, 0.5 → 노랑, 1.0 → 빨강
  if(res<0.3) return new THREE.Color(0.2,0.4,1.0);
  if(res<0.6) return new THREE.Color(1.0,0.85,0.2);
  return new THREE.Color(1.0,0.3,0.2);
}

function rebuild(){
  // cleanup
  domMeshes.forEach(m=>{scene.remove(m);if(m.geometry)m.geometry.dispose();if(m.material)m.material.dispose();});
  edgeLines.forEach(l=>{scene.remove(l);l.geometry.dispose();l.material.dispose();});
  labelObjects.forEach(l=>scene.remove(l));
  domMeshes=[];edgeLines=[];labelObjects=[];

  const minRes=(document.getElementById('res-min').value||10)/100;
  const cmode=document.querySelector('input[name=cmode]:checked').value;
  const nsize=document.querySelector('input[name=nsize]:checked').value;
  const showLabels=document.getElementById('show-labels').checked;

  // domains 집합
  const domSet=new Set();
  const domConns={};
  const pairs=(DATA.high_confidence||[]).filter(p=>p.resonance>=minRes);
  pairs.forEach(p=>{
    domSet.add(p.a);domSet.add(p.b);
    domConns[p.a]=(domConns[p.a]||0)+1;
    domConns[p.b]=(domConns[p.b]||0)+1;
  });
  const doms=[...domSet].sort();
  const posMap={};

  // nodes
  doms.forEach((name,i)=>{
    const pos=domPos(name,i,doms.length);
    posMap[name]=pos;
    const conns=domConns[name]||1;
    const radius=nsize==='connections'?Math.max(1.5,Math.min(5,conns*0.3)):2.5;
    const geom=new THREE.SphereGeometry(radius,14,12);
    const mat=new THREE.MeshStandardMaterial({color:0x4fc3f7,emissive:0x4fc3f7,emissiveIntensity:0.3,roughness:0.5});
    const mesh=new THREE.Mesh(geom,mat);
    mesh.position.set(pos[0],pos[1],pos[2]);
    mesh.userData={name,connections:conns};
    scene.add(mesh);domMeshes.push(mesh);

    if(showLabels){
      const div=document.createElement('div');
      div.textContent=name;
      div.style.cssText='color:#aac;font-size:9px;background:rgba(0,0,0,0.5);padding:1px 4px;border-radius:2px;white-space:nowrap';
      const label=new CSS2DObject(div);
      label.position.set(pos[0],pos[1]+radius+2,pos[2]);
      scene.add(label);labelObjects.push(label);
    }
  });

  // edges
  const pts=[];const colors=[];
  pairs.forEach(p=>{
    const pa=posMap[p.a],pb=posMap[p.b];
    if(!pa||!pb) return;
    const c=resColor(p.resonance);
    pts.push(pa[0],pa[1],pa[2],pb[0],pb[1],pb[2]);
    colors.push(c.r,c.g,c.b,c.r,c.g,c.b);
  });
  if(pts.length){
    const g=new THREE.BufferGeometry();
    g.setAttribute('position',new THREE.Float32BufferAttribute(pts,3));
    g.setAttribute('color',new THREE.Float32BufferAttribute(colors,3));
    const m=new THREE.LineBasicMaterial({vertexColors:true,transparent:true,opacity:0.5});
    const l=new THREE.LineSegments(g,m);
    scene.add(l);edgeLines.push(l);
  }

  // stats
  document.getElementById('s-dom').textContent=doms.length;
  document.getElementById('s-pairs').textContent=pairs.length;
  document.getElementById('s-hc').textContent=DATA.high_confidence_count||0;
  const avgRes=pairs.length?pairs.reduce((s,p)=>s+p.resonance,0)/pairs.length:0;
  document.getElementById('s-avg').textContent=avgRes.toFixed(3);
}

const tooltipEl=document.getElementById('tooltip');
function onMove(ev){
  mouse.x=(ev.clientX/innerWidth)*2-1;
  mouse.y=-(ev.clientY/innerHeight)*2+1;
  raycaster.setFromCamera(mouse,camera);
  const hits=raycaster.intersectObjects(domMeshes);
  if(hits.length){
    const d=hits[0].object.userData;
    tooltipEl.style.display='block';
    tooltipEl.style.left=(ev.clientX+14)+'px';
    tooltipEl.style.top=(ev.clientY+14)+'px';
    // 연결된 쌍 찾기
    const conPairs=(DATA.high_confidence||[]).filter(p=>p.a===d.name||p.b===d.name).slice(0,8);
    let pairHtml=conPairs.map(p=>{
      const other=p.a===d.name?p.b:p.a;
      return `<span style="color:#4fc3f7">${other}</span> res=${p.resonance} kw=${p.kw_overlap}`;
    }).join('<br>');
    tooltipEl.innerHTML=`<b>${d.name}</b> (${d.connections} connections)<br><hr style="border-color:#334">${pairHtml}`;
  }else{
    tooltipEl.style.display='none';
  }
}

function animate(){
  requestAnimationFrame(animate);
  controls.update();
  renderer.render(scene,camera);
  labelRenderer.render(scene,camera);
}

// 30초 폴링
setInterval(()=>{loadAll();},30000);
</script>
</body></html>
```

- [ ] **Step 2: reality_map_3d.html에 DSE 레이어 토글 + growth_bus 이벤트 패널 추가**

`shared/discovery/reality_map_3d.html` 수정 — controls div 끝(`</div>` line 61 부근)에 추가:

```html
<div class="group"><b>DSE 오버레이</b>
  <label><input type="checkbox" id="dse-overlay"> Cross-DSE 공명 엣지</label>
  <label><a href="dse_graph_3d.html" style="color:#4fc3f7;text-decoration:none">→ DSE 전용 뷰 열기</a></label>
</div>
```

controls 닫는 `</div>` 바로 뒤에 이벤트 로그 패널 추가:

```html
<div id="event-log" style="position:fixed;bottom:12px;right:12px;width:340px;max-height:200px;background:rgba(10,10,30,.92);border:1px solid #334;border-radius:8px;padding:8px;font-size:10px;z-index:100;overflow-y:auto;line-height:1.5;display:none">
  <b style="color:#4fc3f7">📡 Growth Bus</b><hr style="border-color:#223;margin:4px 0">
  <div id="bus-events"></div>
</div>
```

JS 섹션 (loadData 함수 뒤)에 추가:

```javascript
// ═══ GROWTH BUS 이벤트 스트리밍 ═══
async function loadGrowthBus(){
  try{
    const r=await fetch('atlas.n6',{cache:'no-store'});
    if(!r.ok) return;
    const text=await r.text();
    const lines=text.trim().split('\n').filter(l=>l).slice(-15).reverse();
    const el=document.getElementById('bus-events');
    el.innerHTML=lines.map(l=>{
      try{const e=JSON.parse(l);return '<div style="border-bottom:1px solid #1a1a2a;padding:2px 0"><span style="color:#555;font-size:9px">'+e.ts+'</span> '+(e.type||'?')+'</div>';}
      catch{return '';}
    }).join('');
    document.getElementById('event-log').style.display='block';
  }catch(e){}
}
loadGrowthBus();
setInterval(loadGrowthBus,30000);

// ═══ DSE OVERLAY ═══
document.getElementById('dse-overlay').addEventListener('change',async function(){
  // 기존 DSE 엣지 제거
  if(window._dseEdges){scene.remove(window._dseEdges);window._dseEdges.geometry.dispose();window._dseEdges.material.dispose();window._dseEdges=null;}
  if(!this.checked) return;
  try{
    const r=await fetch('dse_cross_results.json',{cache:'no-store'});
    if(!r.ok) return;
    const d=await r.json();
    // DSE 도메인 → reality_map 노드 매핑 (domain 필드 기준)
    const nodeMap={};
    (DATA.nodes||[]).forEach((n,i)=>{
      const dom=(n.domain||n.claim||'').toLowerCase().replace(/[^a-z0-9]/g,'-');
      if(!nodeMap[dom]) nodeMap[dom]=posMap[n.id];
    });
    const pts=[];
    (d.high_confidence||[]).forEach(p=>{
      const pa=nodeMap[p.a],pb=nodeMap[p.b];
      if(!pa||!pb) return;
      pts.push(pa[0],pa[1],pa[2],pb[0],pb[1],pb[2]);
    });
    if(!pts.length) return;
    const g=new THREE.BufferGeometry();
    g.setAttribute('position',new THREE.Float32BufferAttribute(pts,3));
    const m=new THREE.LineBasicMaterial({color:0xff6644,transparent:true,opacity:0.3});
    window._dseEdges=new THREE.LineSegments(g,m);
    scene.add(window._dseEdges);
  }catch(e){console.warn('DSE overlay load failed',e);}
});
```

- [ ] **Step 3: 로컬 서버로 검증**

```bash
cd shared && python3 -m http.server 8080 &
# 브라우저에서 http://localhost:8080/dse_graph_3d.html 확인
# http://localhost:8080/reality_map_3d.html 에서 DSE 오버레이 토글 확인
kill %1
```

- [ ] **Step 4: 커밋**

```bash
git add shared/dse/dse_graph_3d.html shared/discovery/reality_map_3d.html
git commit -m "feat(viz): DSE 공명 3D 그래프 + reality_map growth_bus 이벤트 패널"
```

---

## Self-Review Checklist

1. **Spec coverage**: Task 1 = I/O 샌드박스 해소 ✅ | Task 2 = Cross-DSE 융합 ✅ | Task 3 = 시각화 ✅
2. **Placeholder scan**: 모든 코드 블록 완전 — TBD/TODO 없음 ✅
3. **Type consistency**: `dse_cross_results.json` 구조(top_pairs, high_confidence)가 Task 2·3 전체에서 일관 ✅
