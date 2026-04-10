# n6 차원별 지도 — 펼침(Unfold) 뷰 설계

**목적**: n6 현실지도의 7+ 차원을 단일 3D 공간에 투영(projection)하지 않고, **사용자가 차원을 하나씩 풀어서 펼침/접힘(unfold/fold) 할 수 있도록** 레이아웃을 전환.

**대상 파일**: `~/Dev/nexus/shared/discovery/reality_map_3d.html` (L0 잠금, 추가만)
**데이터 원본**: `reality_map_live.json` (n6 merge 후 2625+ 노드)

---

## 차원 정의

| # | 차원 | 설명 | 현재 투영 |
|---|---|---|---|
| **D1** | Level | L-2..L10 구조 계층 | X축 |
| **D2** | Grade | EXACT/CLOSE/MISS/EMPIRICAL/CONVENTION | Y축 |
| **D3** | Origin | natural/engineering/convention/derived | Z축 |
| **D4** | Thread | n, σ, τ, φ, π, e, φ_g, α ... 산술함수 | 색상(모드 전환시) |
| **D5** | Domain | 42+ 도메인 인덱스 | 툴팁 전용 |
| **D6** | Causal | STRUCTURAL/EMPIRICAL/CONVENTION | 엣지 스타일 |
| **D7** | BT_refs | 연결 BT 번호 리스트 | 툴팁 전용 |

---

## 펼침 모드 5종

### L0 — `3d_default` (현재)
3축 투영: X=Level, Y=Grade, Z=Origin. 전체 얼개 조망용.

### L1 — `1d_spine` (수직 척추)
```
L-1  ━━━━━━
L0   ━━━━━━━━━━━
L1   ━━━━━━━━━━━━━━━━━━
L2   ━━━━━━━━━━
...
L7   ━━━━
```
한 축만 세움. 구조 계층의 수직 타임라인.

**수식**:
```js
pos = [0, (LEVEL_INDEX - 5.5) * 40, 0]
+ jitter(x,z) via id hash * 15
```

### L2 — `2d_grid` (Level × Thread)
```
         n   σ   τ   φ   π   e   φ_g   α
  L-1  ●                                
  L0   ●●  ●●   ●
  L1   ●●●●● ●●●   ●●
  L2   ●●●  ●●   ●●  ●●
  ...
  L7   ●●
```
히트맵. 빈 칸 = gap (연구 기회).

**수식**:
```js
pos = [
  (THREAD_INDEX - THREADS.length/2) * 35,
  (LEVEL_INDEX - 5.5) * 35,
  0
]
```

### L3 — `3d_cube` (Level × Thread × Domain)
전체 3 축 분리. 각 축이 한 개 차원만 표현. 투영 겹침 없음.

**수식**:
```js
pos = [
  (LEVEL_INDEX - 5.5) * 30,
  (THREAD_INDEX - THREADS.length/2) * 30,
  (DOMAIN_INDEX - DOMAINS.length/2) * 15
]
```

### L4 — `hyperroll` (7축 레이더 언롤)
각 노드를 **7각 radar chart** 스타크플롯으로 표현. 7축: n/σ/τ/φ/sopfr/J₂/μ 값 정규화.

**수식**: 노드 중심 `[level_x, 0, 0]` + 7꼭지점 별 분기 (per-node 7각 도형).

실제 렌더는 Points 대신 LineSegments 다각형 — 복잡도 증가로 기본 off.

---

## UX 설계

### 버튼 배치 (기존 `#controls` 하단 추가)
```
─────────────────
  펼침 모드
─────────────────
  [ 3D 기본 ]  ← L0
  [ 1D 척추 ]  ← L1
  [ 2D 그리드 ] ← L2
  [ 3D 큐브 ]  ← L3
  [ 7축 언롤 ] ← L4
─────────────────
```

### 키보드 단축키
- `1` / `2` / `3` / `4` / `5` → L0..L4 전환
- `Space` → 현재 모드 ↔ L0 토글 (비교용)

### 애니메이션
- 모드 전환 시 노드 위치를 **0.8초 easeInOutCubic tween** 으로 이동
- 접힘→펼침 모션 연출 (초기 0.0 → 대상 1.0)
- 엣지는 노드 위치 추적으로 자동 갱신

### 상태 표시
헤더 옆에 `LAYOUT: 3D_CUBE` 뱃지. URL 해시 `#layout=2d_grid` 로 공유 가능.

---

## 구현 최소 diff (reality_map_3d.html)

### 1. 상수 추가 (LEVEL_ORDER 뒤)
```js
const THREAD_ORDER = ['n','sigma','tau','phi','sopfr','J2','mu','n_over_phi','pi','e','phi_g','alpha','misc','none'];
const DOMAIN_ORDER = []; // dynamic from data
let LAYOUT_MODE = (location.hash.match(/layout=(\w+)/)||[])[1] || '3d_default';
let TWEEN_T0 = 0; let TWEEN_FROM = new Map(); let TWEEN_DUR = 800;
```

### 2. nodePos 레이아웃 분기 (L0~L4)
```js
function nodePos(n,idx,total){
  const li = Math.max(0, LEVEL_ORDER.indexOf(n.level));
  const ti = Math.max(0, THREAD_ORDER.indexOf(n.thread));
  const di = Math.max(0, DOMAIN_ORDER.indexOf(n.domain||n.origin));
  let h=0; const s=n.id||('n'+idx); for(let i=0;i<s.length;i++){h=(h*31+s.charCodeAt(i))|0;}
  const j = k=>(((h>>k)&255)/255-0.5);

  if(LAYOUT_MODE==='1d_spine'){
    return [j(0)*18, (li-5.5)*40 + j(8)*18, j(16)*18];
  }
  if(LAYOUT_MODE==='2d_grid'){
    return [
      (ti - THREAD_ORDER.length/2)*35 + j(0)*8,
      (li-5.5)*35 + j(8)*8,
      j(16)*8
    ];
  }
  if(LAYOUT_MODE==='3d_cube'){
    return [
      (li-5.5)*30 + j(0)*10,
      (ti - THREAD_ORDER.length/2)*30 + j(8)*10,
      ((di - DOMAIN_ORDER.length/2)||0)*15 + j(16)*10
    ];
  }
  if(LAYOUT_MODE==='hyperroll'){
    // 간이: level x + sopfr-base rose
    const ang = (ti/Math.max(1,THREAD_ORDER.length))*Math.PI*2;
    const r = 25 + j(16)*6;
    return [(li-5.5)*30, Math.sin(ang)*r, Math.cos(ang)*r];
  }
  // 3d_default (기존)
  const x=(li-5.5)*28;
  const gradeY={EXACT:60,CLOSE:20,MISS:-20,EMPIRICAL:40,CONVENTION:0}[n.grade]||0;
  const originZ={natural:-60,engineering:60,convention:0,derived:30}[n.origin]||0;
  return [x+j(0)*22, gradeY+j(8)*22, originZ+j(16)*22];
}
```

### 3. 레이아웃 버튼 HTML (#controls 내부 최하단)
```html
<div class="group">
  <b>펼침 모드</b><br>
  <button data-layout="3d_default">3D 기본</button>
  <button data-layout="1d_spine">1D 척추</button>
  <button data-layout="2d_grid">2D 그리드</button>
  <button data-layout="3d_cube">3D 큐브</button>
  <button data-layout="hyperroll">7축 언롤</button>
</div>
```

### 4. 레이아웃 전환 핸들러 (init 끝)
```js
function setLayout(mode){
  LAYOUT_MODE = mode;
  location.hash = 'layout='+mode;
  TWEEN_FROM.clear();
  nodeMeshes.forEach(m=>TWEEN_FROM.set(m.userData.id, m.position.clone()));
  TWEEN_T0 = performance.now();
  rebuild();
}
document.querySelectorAll('button[data-layout]').forEach(b=>{
  b.addEventListener('click', ()=>setLayout(b.dataset.layout));
});
addEventListener('keydown', e=>{
  const map={'1':'3d_default','2':'1d_spine','3':'2d_grid','4':'3d_cube','5':'hyperroll'};
  if(map[e.key]) setLayout(map[e.key]);
});
```

### 5. DOMAIN_ORDER 동적 채움 (loadData 성공 후)
```js
const domSet = new Set(DATA.nodes.map(n=>n.domain||n.origin||''));
DOMAIN_ORDER.length = 0;
[...domSet].sort().forEach(d=>DOMAIN_ORDER.push(d));
```

### 6. Tween 애니메이션 (animate 내부)
```js
if(TWEEN_FROM.size > 0){
  const t = Math.min(1, (performance.now()-TWEEN_T0)/TWEEN_DUR);
  const ease = t<0.5 ? 4*t*t*t : 1-Math.pow(-2*t+2,3)/2;
  nodeMeshes.forEach(m=>{
    const from = TWEEN_FROM.get(m.userData.id);
    if(!from) return;
    const to = m.userData.targetPos;
    if(!to) return;
    m.position.set(
      from.x + (to.x-from.x)*ease,
      from.y + (to.y-from.y)*ease,
      from.z + (to.z-from.z)*ease
    );
  });
  if(t>=1) TWEEN_FROM.clear();
}
```

(rebuild에서 각 노드 `m.userData.targetPos = new THREE.Vector3(...pos)` 저장)

---

## 못박음

- 본 설계의 **레이아웃 상수·함수명**은 이후 모든 추가 차원(D8+)의 기준.
- `reality_map_3d.html` 수정 시 본 문서 `구현 최소 diff` 섹션이 SSOT.
- **하위 호환**: 기본 모드는 `3d_default` 유지. 기존 사용자 경험 변경 없음.
- URL 해시 `#layout=…` 공유 가능 → 깨지지 않도록 모드 이름 고정.

---

## 성과 기대

- **2D 그리드 모드**: 560→2625 노드를 한 눈에 스캔 → 빈 (Level,Thread) 칸 = 연구 gap 즉각 식별
- **1D 척추 모드**: 구조 계층의 BT 종속 흐름 시각화 → 돌파 체인 추적
- **3D 큐브 모드**: Level×Thread×Domain 교차점 밀집도 → 집중 도메인 파악
- **7축 언롤**: 개별 노드의 n6 상수 balance 시각화 → 편향 탐지
