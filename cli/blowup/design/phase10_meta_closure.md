# Phase 10 — Meta-Closure Check (Operational Self-Referential Fixed-Point)

**Status**: Design spec (Mk.IX proposal)
**Author**: CANON research thread, 2026-04-19
**Scope**: `shared/blowup/core/blowup.hexa` extension; `shared/n6/atlas.n6` edge schema addition
**Non-goals**: atlas 상수 추가 (이미 META-01~10 + META-LK017~500 등재 완료)

---

## 1. 목적 (1 문장)

🛸16 "Meta² Self-Referential Closure" 를 atlas 의 정적 상수 나열에서 분리해, **discovery 생성 경로를 역추적하여 자기 자신을 생성자로 포함하는 고정점 |D⟩ = f(|D⟩) 만을 operational 하게 마킹**함으로써 Phase 4 corollary · Phase 6.7 auto-absorb 가 흘려보낸 self-reference 사건을 [10*] 과 [11*] 사이의 새 등급 [10**] 로 승격하고 atlas 엣지 `meta_self_ref` 로 기록하는 것이 목적이다.

---

## 2. 입출력 Spec

### Input
- **Phase 7 산출물**:
  - `buf_lines` (corollary 결과, tab-separated `id\ttype\texpr\tconf\tvalue\taxiom\tsrc`)
  - `tele_agree`, `tele_level`, `tele_boost` (5-lens consensus 결과)
- **Phase 8 산출물**:
  - `wave_targets[]`, `wave_total_energy`, `dfs_best_target`
  - `shared/.wave_out.log.*` 파동 전파 세부 로그
- **Phase 6 그래프**: 이번 라운드에 추가된 `graph_added_nodes` / `graph_added_edges` (atlas.n6 에 flush 된 node/edge JSON 라인)
- **이번 라운드의 seed pool**: `ax_name_arr[]`, `ax_val_arr[]`

### Output
- `meta_closed_discoveries[]`: self-ref closure 를 통과한 discovery id 목록
- `shared/n6/atlas.n6` 에 append:
  - `@E` meta-self-ref 엣지 (edge_type=`meta_self_ref`)
  - `@R` 재작성 (기존 [10*] 라인을 [10**] 로 in-place 승급; 신규 라인 삽입 아님)
- stdout report: `meta_closed=N`, `promoted=N`, `rejected_by_heuristic=N`

---

## 3. 알고리즘 의사코드 (hexa pseudo)

```hexa
// ─── Phase 10: Meta-Closure Check ───
// 위치: Phase 8 (wave propagation) 종료 직후, Phase 9 (DFS) 진입 전.
// --fast 에서는 스킵. --no-meta-closure 플래그로 명시 비활성 가능.

println("═══ Phase 10: Meta-Closure Check (Self-Referential Fixed-Point) ═══")

// 설정 — 튜닝 파라미터
let MC_MIN_TRACE_DEPTH: i64 = 3       // heuristic H1: 최소 역추적 깊이
let MC_MAX_TRACE_DEPTH: i64 = 16      // runaway 방지 (🛸16 layer 근거)
let MC_N6_INVARIANCE_EPS: f64 = 1e-9  // heuristic H3: n=6 불변 허용오차

let mut mc_candidates  = []           // trace depth 통과 후보
let mut mc_closed      = []           // 세 heuristic 전부 통과
let mut mc_promoted    = 0
let mut mc_rejected_h1 = 0   // trace depth 미달
let mut mc_rejected_h2 = 0   // 단순 cycle
let mut mc_rejected_h3 = 0   // n=6 invariance 파괴

// ─── A. discovery 역추적 — 이번 라운드 + 파동 산출 통합 ───
// buf_lines 는 Phase 4 7-type(ded/xfer/orbit/dual/closure/recur/meta) corollary.
// Phase 8 wave 결과는 wave_out.log.* 파일에서 tail 파싱하여 병합.
let mut all_disc = buf_lines                            // 자기 세션
all_disc = all_disc + load_wave_child_disc(wave_out_paths) // 자식 세션

for D in all_disc {
    let parts = D.split("\t")
    if len(parts) < 7 { continue }
    let d_id = parts[0]
    let d_type = parts[1]
    let d_expr = parts[2]
    let d_conf:  f64 = safe_float(parts[3])
    let d_value: f64 = safe_float(parts[4])
    let d_src = parts[6]                                 // src = "axiom_a|axiom_b" 형태

    // EXACT + confidence ≥ 0.8 만 후보 (noise 컷)
    let gr = match_grade(d_value)
    if gr != "EXACT" { continue }
    if d_conf < 0.8 { continue }

    // ─── B. 생성 경로 역추적 ───
    // src 필드의 부모 axiom 을 재귀적으로 buf_lines 에서 재조회
    let path = trace_generation_path(d_id, all_disc, MC_MAX_TRACE_DEPTH)
    // path: [d_id, parent_1, grandparent_1, ..., root_seed]

    // ─── Heuristic H1: trace depth 최소값 ───
    if len(path) < MC_MIN_TRACE_DEPTH {
        mc_rejected_h1 = mc_rejected_h1 + 1
        continue
    }

    // ─── 고정점 판정 ───
    // D 의 조상 체인에 D 자신(또는 동치 expr) 이 존재하는가?
    let mut self_found = false
    let mut self_at_depth: i64 = -1
    let mut i: i64 = 1        // 0 = self, 1 부터가 ancestor
    while i < len(path) {
        if expr_equiv(path[i], d_id) || expr_equiv(path[i].expr, d_expr) {
            self_found = true
            self_at_depth = i
            break
        }
        i = i + 1
    }
    if !self_found { continue }

    mc_candidates = mc_candidates + [d_id]

    // ─── Heuristic H2: 단순 reverse-dependency cycle 배제 ───
    // A→B→A 류 2-cycle 은 meta-closure 가 아니라 relational tautology.
    // 조건: self_at_depth ≥ 3 **그리고** path 에 distinct 도메인/섹터 ≥ 2
    if self_at_depth < 3 {
        mc_rejected_h2 = mc_rejected_h2 + 1
        continue
    }
    let distinct_sectors = count_distinct_sectors(path)
    if distinct_sectors < 2 {
        mc_rejected_h2 = mc_rejected_h2 + 1
        continue
    }

    // ─── Heuristic H3: n=6 invariance 보존 검증 ───
    // σ·φ=n·τ=24 invariant 이 경로 전체에서 성립하는가?
    // path 의 각 노드가 n=6 에 대해 평가되었을 때 σ(6)·φ(6)=48, 6·τ(6)=24 의
    // 곱 τ/φ 비율 손상이 없는지 확인. (Δ₀-absolute 조건)
    if !n6_invariance_preserved(path, MC_N6_INVARIANCE_EPS) {
        mc_rejected_h3 = mc_rejected_h3 + 1
        continue
    }

    mc_closed = mc_closed + [{id: d_id, path_depth: self_at_depth,
                              value: d_value, expr: d_expr}]
}

// ─── C. 승급 + atlas flush ───
for mc in mc_closed {
    // 새 엣지 발행 (self-loop; bidirectional=true 로 고정점성 표시)
    let edge_json = "{\"type\":\"edge\",\"from\":\"" + mc.id
        + "\",\"to\":\"" + mc.id
        + "\",\"edge_type\":\"meta_self_ref\""
        + ",\"strength\":1.0,\"bidirectional\":true"
        + ",\"closure_depth\":" + to_string(mc.path_depth)
        + ",\"n6_invariant\":true}"
    _guarded_append_atlas(_ATLAS, edge_json + "\n")

    // @R 등급 승급: [10*] → [10**] (in-place 라인 재작성)
    // 주의: atlas.n6 는 append-only 원칙이지만, grade 승급은 예외적 in-place.
    // blowup_absolute.hexa 의 [10*]→[11*] 승급 패턴과 동형.
    promote_grade_line(_ATLAS, mc.id, "[10*]", "[10**]")
    mc_promoted = mc_promoted + 1

    println("  ✓ " + mc.id + " meta-closed @ depth " + to_string(mc.path_depth))
}

println("")
println("  candidates       : " + to_string(len(mc_candidates)))
println("  meta-closed      : " + to_string(len(mc_closed)))
println("  promoted [10**]  : " + to_string(mc_promoted))
println("  rejected H1 depth: " + to_string(mc_rejected_h1))
println("  rejected H2 cycle: " + to_string(mc_rejected_h2))
println("  rejected H3 n=6  : " + to_string(mc_rejected_h3))
println("═══ Phase 10 complete ═══")
println("")
```

---

## 4. False-Positive 차단 Heuristic 3가지

### H1 — Trace Depth 최소값
- **임계**: `len(path) ≥ 3`
- **근거**: self-reference 는 최소 *3 단계* 이상의 derivation chain 을 거쳐야 의미 있는 meta-closure 이다. 1~2 단계는 Phase 4 의 `ded_` 타입에서 흔히 나타나는 단순 함수 합성이며 `σ(6)·φ(6) = 24·12 → 24 = 6·τ(6)` 류의 *직접 치환* 에 불과하다.
- **구현**: `if len(path) < MC_MIN_TRACE_DEPTH: reject`.

### H2 — Reverse-Dependency Cycle 구분
- **배제 대상**: 단순 loop (`A → B → A`, 2-cycle), relational tautology.
- **판정**:
  - `self_at_depth ≥ 3` (고정점이 path 에 나타나는 최소 깊이가 3 이상)
  - **AND** path 가 통과하는 distinct sector(`sector_of`) ≥ 2 — 즉 self-ref 가 **도메인 경계를 횡단**한 후 복귀해야 한다.
- **근거**: 🛸16 Meta² 는 `σ-φ-τ` 의 number-theoretic 자기참조가 아니라 **도메인 횡단 관측자 동치** (`|UFO⟩ = f(|UFO⟩)` @ META-09) 에 해당한다. 도메인 내부에 머무르는 cycle 은 graph 평가상 loop 이지만 meta-closure 가 아니다.

### H3 — n=6 Invariance 보존
- **검증**: path 의 모든 노드 expr 에 `n=6` 을 대입했을 때 σ·φ = n·τ = 24 관계의 곱/비율 오차가 `MC_N6_INVARIANCE_EPS = 1e-9` 이내.
- **근거**: `blowup_absolute.hexa` 의 A2 `verify_transitive` 가 Π₀¹ 절대성을 요구하듯, Phase 10 은 n=6 고정점을 통과하는 경로만 인정. 경로 중간 노드가 n=6 에서 값이 달라진다면 그 closure 는 `n=12` 혹은 `n=28` 등 sibling perfect number 로 leak 하는 가짜 cycle 이다.
- **구현**: 각 path 노드의 expr 를 `m_val` 로 재평가 → σ·φ / (n·τ) 비율이 1.0 ± ε 유지 확인.

---

## 5. atlas 신규 엣지 타입 `meta_self_ref` schema

기존 atlas.n6 엣지 포맷 (확인된 샘플, line 15954):
```json
{"type":"edge","from":"n","to":"blowup-d0_ded_n_sigma","edge_type":"Derives","strength":1.0,"bidirectional":false}
```

**신규 `meta_self_ref` 엣지 포맷** (기존 키 전부 유지 + 2개 확장 키):
```json
{"type":"edge","from":"<D_id>","to":"<D_id>","edge_type":"meta_self_ref","strength":1.0,"bidirectional":true,"closure_depth":<int>,"n6_invariant":true}
```

필드 semantics:
| Key | Value | 근거 |
|---|---|---|
| `from` == `to` | 동일 id (self-loop) | 고정점 |D⟩ = f(|D⟩) |
| `edge_type` | `"meta_self_ref"` | 기존 `"Derives"`, `"Causes"`, `"Equivalent"` 와 orthogonal |
| `strength` | `1.0` 고정 | EXACT 등급만 통과하므로 확신도 최대 |
| `bidirectional` | `true` | self-ref 는 대칭적 — 관측자 = 관측대상 |
| `closure_depth` | `int` | Heuristic 통과 시 self_at_depth 값 (3~16) |
| `n6_invariant` | `true` 고정 | H3 통과 표시. false 로 기록되는 엣지는 생성 금지 |

**호환성**: 기존 그래프 소비자 (reality_map viewer, topology scanner) 는 `edge_type` 을 whitelist 기반으로 필터하므로 신규 타입을 무시해도 깨지지 않음. `meta_self_ref` 를 해석하려는 새 소비자만 추가 필드를 읽으면 된다.

---

## 6. 신규 등급 `[10**]` — Meta-Closed 의미

현재 등급 사다리:
- `[7]`  EMPIRICAL (승격대상)
- `[9]`  NEAR
- `[10]` EXACT
- `[10*]` EXACT + 독립검증 완료
- `[11*]` Foundation axiom (Δ₀-absolute, Π₀¹, 모든 transitive 모델 불변)

**`[10**]` 신설 위치**: `[10*]` 과 `[11*]` 사이.

| 등급 | 조건 | 승격 주체 |
|---|---|---|
| `[10*]` | EXACT + 5-lens consensus | Phase 5 Telescope |
| **`[10**]`** | **[10*] + self-ref closure 입증** | **Phase 10 Meta-Closure (신규)** |
| `[11*]` | [10*] 이상 + Π₀¹ arithmetical 절대성 | `blowup_absolute.hexa` (Mk.VIII) |

**Rationale**:
- `[11*]` 는 *명제 내용* 의 절대성 (어느 수학 우주에서도 참) 을 요구하는 반면,
- `[10**]` 는 *생성 경로* 의 자기참조 closure 를 요구한다.
- 두 차원은 직교 — 어떤 discovery 는 [10**] 이지만 [11*] 가 아닐 수 있다 (e.g. 자기참조는 하지만 arithmetical 이 아닌 high-level 구조).
- 승급 순서: `[10*] → [10**] → [11*]` 혹은 `[10*] → [11*]` 단독. 병렬 승급 가능.

**표기 처리**: `promote_grade_line` 은 atlas 파일을 한 번 읽어 `id` 로 매칭한 라인의 ` [10*]` 서픽스를 ` [10**]` 로 치환하고 flush. `blowup_absolute.hexa` 의 `should_promote_11` 이 라인 prefix `[11*]` 체크로 멱등성 보장하듯, Phase 10 도 `if line.contains("[10**]") { skip }` 로 멱등.

---

## 7. 기존 Phase 와의 통합 지점

**삽입 위치**: Phase 8 (wave propagation) 의 `println("═══ Phase 8 complete ═══")` 직후, 그리고 `} // end if !fast_mode` 바로 앞. 즉 Phase 9 (DFS Deep Dive) 와 독립적으로 실행되며 Phase 8 의 `wave_total_energy` / `dfs_best_target` 을 참조할 수 있는 scope.

**이유**:
1. Phase 7 lens consensus 만으로는 self-ref 판정에 필요한 **cross-session path** 가 없음. Phase 8 의 파동 자식 결과가 path 의 원격 조상에 해당.
2. Phase 9 DFS 는 Phase 10 의 출력물 (meta-closed list) 을 DFS target 선정 bonus 로 활용 가능 — 추후 Mk.X 과제.
3. Phase 6.7 auto-absorb 와 분리: absorb 는 *무조건 기록*, Phase 10 은 *승급 필터*. 두 단계가 한 Phase 에 합쳐지면 R27 unit responsibility 위반.

**blowup.hexa 종료 지점 보존 방법**:
- 현재 구조:
  ```
  Phase 8 block
    } else { (logged == 0) ... }
  println("═══ Phase 8 complete ═══")
  } // end if !fast_mode
  ```
- 수정안:
  ```
  Phase 8 block (변경 없음)
  println("═══ Phase 8 complete ═══")
  // ─── Phase 10 삽입 ───
  if !fast_mode && logged > 0 && !no_meta_closure_flag {
      <Phase 10 pseudo code>
  }
  } // end if !fast_mode (기존 블록 종료 유지)
  ```
- `fast_mode` 에서는 자동 스킵, `logged == 0` 이면 후보 없음으로 즉시 스킵.
- 신규 CLI 플래그: `--no-meta-closure` (기본 활성, breakdown 시 off).
- 기존 Mk.II wave round 루프(`wave_round < wave_max_rounds`) 는 Phase 10 아래 블록이라 영향 없음.

**모듈화 권장**: 실제 구현 시 `shared/blowup/modules/blowup_meta_closure.hexa` (7번째 core 모듈) 로 분리하여 `blowup_absolute.hexa` 와 대칭 구조 유지. `core/blowup.hexa` 에는 invocation stub 30라인 정도만 추가.

---

## 8. 테스트 시나리오

### Positive — n=6 discovery 가 통과

- **도메인**: `7대난제`
- **Seed**: `n=6`, `σ=12`, `φ=2`, `τ=4`
- **기대 trace**:
  `d2_meta_sigma_phi_tau` ← `d1_closure_sigma_phi` ← `d0_ded_sigma_phi` ← `σ`
  그리고 `d2_meta_sigma_phi_tau` 의 expr 가 `σ(6)·φ(6) = n·τ(6) = 24` 로 평가될 때, ancestor `d1_closure_sigma_phi` 재평가 경로에 자기 자신의 id 가 다시 나타남 (Phase 4 `closure_` 타입이 meta 로 피드백).
- **Heuristic**:
  - H1: path_depth=4 ≥ 3 ✓
  - H2: self_at_depth=3, sectors={`n6`, `n6`, `n6`} → distinct=1 ✗ 실패 우려
  - **보정**: positive 시나리오를 위해 seed 에 `xfer_` 타입 강제 (도메인 횡단 n6 → quantum → n6 path 생성)
- **기대 결과**: 1건 [10**] 승급, 엣지 `{"edge_type":"meta_self_ref","closure_depth":4,"n6_invariant":true}` atlas.n6 append.
- **검증**: `grep '"edge_type":"meta_self_ref"' shared/n6/atlas.n6 | wc -l` = 1 증가.

### Negative — n=12 / n=28 control 차단

- **도메인**: n=12 (abundant number, σ=28) / n=28 (perfect number, σ=56)
- **Seed**: `n=12`, `σ=28`, `φ=4`, `τ=6`
- **기대 trace**: `σ·φ = 28·4 = 112`, `n·τ = 12·6 = 72` → **불일치** (n=12 는 σ·φ ≠ n·τ).
- **Heuristic**:
  - H1: path 길이 충분 ✓ 통과
  - H2: sector distinct ≥ 2 도 통과 가능
  - **H3 실패 핵심**: n=6 invariance 체크 시 path 노드 재평가가 n=12 기준이라 σ·φ/(n·τ) = 112/72 ≈ 1.556 ≠ 1.0, ε=1e-9 초과 → **reject H3**.
- **기대 결과**: 0건 승급, `mc_rejected_h3 = 1` 증가.
- **n=28 동일**: σ·φ = 56·12 = 672, n·τ = 28·6 = 168, 비율 4.0 → reject.

두 control 은 동일한 session 에서 `--seeds "12,28,4,6"` / `--seeds "28,12,56,6"` 로 주입하면 positive 와 negative 를 한 번에 확인 가능하다. CI 훅으로 승급 carry-over 가 0 임을 검증.

---

## 9. Risk & Future Work

- **Risk-1**: in-place `[10*]→[10**]` 치환이 atlas.n6 append-only 원칙에 위배. `blowup_absolute.hexa` 의 `[11*]` 승급이 이미 동일 패턴을 채택했으므로 선례 따름. L0 guard(`l0_guard.hexa sync`) 로 해시 재정렬.
- **Risk-2**: trace_generation_path 가 `src` 필드의 `|` 구분 부모 체인을 완전히 복원하지 못하는 경우 (Phase 6.7 absorb 가 src 를 축약) — Phase 10 시작 시 src 복원 가능 여부 확인 후 축약 discovery 는 skip.
- **Mk.X 연계**: [10**] 집합이 커지면 Phase 9 DFS 의 target scoring 에 `+closure_depth` bonus 추가 → self-ref 풍부 방향으로 deep-dive 편향. 별도 design doc 필요.
- **승급 수치 상한**: L(16)=24 가 base closure 이므로 Phase 10 승급 누적이 24 배수 근방에서 saturate 하는지 monitoring. `reports/` 아래 periodic snapshot 로 추적.

---

**End of design**. 실제 구현은 Mac 세션의 구현자(Claude Code) 가 본 문서를 참조해 `shared/blowup/modules/blowup_meta_closure.hexa` 및 `shared/blowup/core/blowup.hexa` Phase 8 직후 삽입부로 코드화 예정.
