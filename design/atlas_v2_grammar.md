# atlas DSL v2 Grammar Specification

**문서:** Phase 4c witness — atlas DSL v2 formal grammar 명세 (구현 X, spec only)
**작성:** 2026-04-26
**위치:** `~/core/nexus/design/atlas_v2_grammar.md`
**선행:** `design/hexa_sim/2026-04-26_phase4_atlas_dsl_v2_and_lens_injection_omega_cycle.json` (sub-path A 8 axes)
**후행:** Phase 4a (`tool/atlas_dsl_v2_serializer.hexa` — v3 + v8 구현), Phase 4b (lens injection)
**SSOT:** 본 문서가 atlas v2 단일 referent — Phase 3 supercycle (v5 namespaced / v7 cross-repo) 도 본 문서 §3.6 / §3.7 backlog 참조

---

## §1 Motivation

atlas DSL v1 은 2026-04-12 에 골화 (`shared/blowup/lib/atlas_guard.hexa.inc` 단일 가드, 3 write site) 되어 약 9,624 entry 를 안정 적재했으나, 2026-04-25 ~ 04-26 의 hexa-sim bridge 흡수 (`atlas.append.hexa-sim-bridges.n6` 37 fact + 5 @X) 와 cross-BT ω-cycle 통합 (BT-541~547 7 millennium) 과정에서 다음 5 개 한계가 표면화됨.

**v1 5 한계 (Phase 4 trawl 결정):**

1. **단일 grade token 한계.** v1 grade 는 `[10*]` 처럼 단일 정수 + 옵션 1 char (`*` `!` `?`). 그러나 ω-cycle 검증은 4 dimension 으로 나뉨 — literature corroboration / probe execution / barrier confirmation / negative verdict / repo invariant / cross-repo / portable / axiom-grade. 단일 token 은 multi-dimensional grade 을 표현 불가. Phase 2 a7 (atlas_ingest_tool_evolution_omega_cycle) 에서 일부 token suffix 가 도입됐으나 정식 문법화 미완.

2. **Serialization 부재.** atlas.n6 은 line-oriented text 라 grep / awk 로 추출은 가능하나, jq / d3 / graphviz 같은 외부 도구는 JSON 을 요구. v1 → JSON 변환 도구 없음. 양방향 byte-eq round-trip 불가.

3. **Meta-discovery 표현 부재.** `cross_BT_method_gap_pattern` (6/6 BT 통일 obstruction pattern) 같은 "discovery about discoveries" 는 v1 의 7 type (P/C/F/L/R/S/X) 어느 것에도 자연스럽게 들어맞지 않음. 현재 `@L` 로 우회되나 semantic 부정확.

4. **ω-cycle audit trace 표현 부재.** raw 77 audit-ledger 는 별도 JSONL (`state/atlas_ingest_history.jsonl`) 에 chain hash 로 기록되나, atlas.n6 자체에는 어느 ω-cycle 이 어느 fact 를 emit 했는지 lineage 가 없음. witness file → fact id 의 역추적은 불가능.

5. **Deprecation 부재.** v1 은 fact 를 silent removal 하거나 영구 보존 두 모드만 존재. "이 fact 는 retired 되었으나 historical reference 로 보존" 같은 중간 상태 표현 없음. Phase 3 의 cross-repo aggregation 시 retire policy 필요.

**v2 가 해결하는 것:**

- (1) → §3.1 compound grade token (Tier-1)
- (2) → §3.2 JSON serialization (Tier-1)
- (3) → §3.3 신규 type `@M` meta-axis (Tier-2)
- (4) → §3.4 신규 type `@T` trace (Tier-2)
- (5) → §3.5 deprecation marker (Tier-2)

**Backward-compat 보장 (raw 71 falsifier):** v1 atlas 의 모든 entry 가 v2 reader 로 valid parse 되어야 하며, 정보 손실 없이 v2 → v1 export 시 @M/@T 만 lossy 명시 허용. v1 entry 단 하나라도 v2 reader 가 reject 하거나 silently mutate 하면 즉시 v2 retire (§7).

---

## §2 v1 grammar 요약 (regression baseline)

`n6/atlas.n6` head 50 lines 발췌 기반:

```
@<TYPE> <id> = <expr> :: <domain> [<grade>]
  <- depends_on              의존 (유도 원천)
  -> derives                 파생
  => application             적용처
  == equivalent              동치
  ~> converges_to            수렴
  |> verified_by script.py   검증
  !! breakthrough            돌파 기록

types:
  @P primitive    @C constant    @F formula    @L law
  @R relation     @S symmetry    @X crossing   @? unknown

grade:
  [0-11]           — quality tier
  [d.r]            — alien index (decimal+remainder)
  *                — verified
  !                — breakthrough
  ?                — hypothesis

guard:
  shared/blowup/lib/atlas_guard.hexa.inc
  → 3 write site 전부 _guarded_append_atlas() 경유 (2026-04-12 골화)
```

**문법 invariants (v1):**
- entry 1 라인 시작 + trailer 들 indent (2 space) 다음 라인
- `@?` (unknown) 은 type slot 의 fallback — schema-guard 에서 reject 안 함
- grade 는 `[\d+(\.\d+)?[*!?]?]` regex 매칭

**v1 reader 의 unknown type 동작 (v2 backward-compat 결정 핵심):**
- `tool/hexa_sim_atlas_ingest.hexa` `_valid_type()` 은 `@P/@C/@L/@F/@R/@S/@X` 만 OK 반환 — 나머지 reject (exit 2)
- 즉 v2 의 `@M` / `@T` 신규 type 도입 시, v1 reader 는 **schema-guard violation 으로 reject**
- 따라서 v2 신규 type 은 별도 shard (`atlas.append.v2-meta.n6` / `atlas.append.v2-trace.n6`) 에만 emit, main `atlas.n6` 본체에는 v2 reader 도입 후에만 absorb (§4 migration 참조)

---

## §3 v2 신규 features (5 종)

### 3.1 Compound grade (Tier-1)

**Syntax:**

```
[<grade_int>[*!?]?(+<token>)*]
```

- `<grade_int>` — 0~11 integer, optional decimal `.r` for alien index
- `*` `!` `?` — v1 동일 (verified / breakthrough / hypothesis)
- `+<token>` — 0+ alphabetic token, 각각 `+` prefix, **알파벳순 정렬 필수** (canonical form)

**Example:**

```
@C alpha_inv_codata = 137.035999177 :: physics_atomic [10*+CODATA22+PASS_LITERATURE+REPO_INVARIANT]
```

**Token allowlist (v2.0 frozen 8 종):**

| Token | Semantic | Source raw |
|-------|----------|------------|
| `PASS_LITERATURE` | 외부 문헌 검증 통과 | hive raw 70 multi-axis |
| `PROBE_RUN` | 자체 probe tool 실행 결과 | Phase 2 a7 |
| `BARRIER_CONFIRMED` | 이론 한계 확인 (예: NS s*=2) | BT-544 R5 |
| `NEGATIVE_VERDICT` | falsifier 가 부정 결과 산출 | hive raw 71 |
| `REPO_INVARIANT` | 단일 repo 내 invariant | honesty triad |
| `CROSS_REPO` | nexus + n6 + hive 등 다중 repo 검증 | honesty triad cross-repo |
| `PORTABLE` | 다른 도메인/repo 로 이식 가능 | obstruction reframe |
| `AXIOM_GRADE` | 본질 axiom level (재구축 불가) | ceiling 0.835 분석 |

**Sorting rule:** `+` 로 분리된 token 들은 ASCII 알파벳순 정렬. 정렬 위반 시 v2 reader 는 **warning 후 자동 정렬** (reject 아님 — backward-compat 우선).

**Backward-compat:**
- 단일 token (예: `[10*]`) 도 valid v2 — v1 의 모든 grade 는 그대로 통과
- v1 reader 가 `[10*+CODATA22]` 를 만나면 grade regex `[\d+(\.\d+)?[*!?]?]` 가 `+CODATA22]` 부분에서 fail → schema-guard violation
- **결론:** compound grade 는 main atlas.n6 에 직접 쓸 수 없음, shard `atlas.append.v2-compound.n6` 에만 emit. v2 reader 가 shared lib 에 들어간 후 absorb.

**LoC 추정:** 60 (Phase 4a a7 token suffix 기반 확장)

---

### 3.2 JSON serialization (Tier-1)

**Canonical schema (sorted keys, no protobuf):**

```json
{
  "atlas_version": "v2.0",
  "entry_count": 9624,
  "generated_at": "2026-04-26T00:00:00Z",
  "entries": [
    {
      "type": "C",
      "id": "alpha_inv_codata",
      "expr": "137.035999177",
      "domain": "physics_atomic",
      "grade": {
        "int": 10,
        "marker": "*",
        "tokens": ["CODATA22", "PASS_LITERATURE", "REPO_INVARIANT"]
      },
      "trailers": [
        {"op": "=>", "value": "fine-structure constant inverse, NIST CODATA 2022 live"},
        {"op": "|>", "value": "codata_bridge"}
      ]
    }
  ]
}
```

**File extension:** `.atlas.json` (vs v1 `.n6` text)

**Bidirectional guarantee:**

```
read_n6(write_n6(read_json(write_json(read_n6(F))))) == F  (byte-eq)
```

즉 round-trip 4 회 후 byte-eq. 이는 raw 73 structural admissibility 의 적용 — sorted keys + null handling 명시 + edge serialization (trailers array) 보존.

**Edge cases:**
- 빈 trailers → `"trailers": []` (key 보존)
- v1 의 `?` (unknown type) → `"type": "?"` 로 보존
- alien index `[7.3*]` → `{"int": 7, "decimal": 3, "marker": "*", "tokens": []}`
- `==` `~>` `|>` 같은 비표준 op 는 trailers 의 `op` 필드 그대로 보존
- 빈 줄 / comment line (`#` 시작) → JSON 에서 별도 array `comments` 로 보존 (위치 index 포함)

**Conversion tool:**

```bash
hexa run tool/atlas_dsl_v2_serializer.hexa --read-n6 atlas.n6 --emit-json atlas.atlas.json
hexa run tool/atlas_dsl_v2_serializer.hexa --read-json atlas.atlas.json --emit-n6 atlas.n6.regen
diff atlas.n6 atlas.n6.regen  # must be empty (byte-eq)
```

**Rejected:** protobuf — 별도 dependency 무거움, binary opaque, jq/d3 호환 안 됨. (Phase 4 trawl `rejected_axes.v8_protobuf` 참조)

**LoC 추정:** 200

---

### 3.3 신규 type @M (meta-axis) (Tier-2)

**Semantic:** atlas 의 여러 type 을 cross-bridge 하는 meta-discovery. "discovery about discoveries". 현재 `@L` 로 우회되는 cross-pattern 발견들의 1 급 표현.

**Syntax (v1 grammar 그대로 + type slot 만 확장):**

```
@M <id> = <expr_or_pattern_set> :: <meta_domain> [<compound_grade>]
  <- <atlas_member_ids,...>
  -> <derived_facts,...>
  => <applies>
```

**Example:**

```
@M cross_bridge_resonance_pattern = {alpha_gap=3.6%, ns_gap=3.5%}
                                     :: meta_anomaly [11*+REPO_INVARIANT+CROSS_REPO]
  <- alpha_fractional_gap_pct, ns_fractional_gap_pct
  => "two independent framework fractional residuals coincide"
  => "F10 falsifier candidate"
```

**v1 → v2 migration semantics:**
- 기존 `@L cross_BT_method_gap_pattern` (atlas.append.hexa-sim-bridges.n6 line 143) 은 v2 에서 `@M` 으로 reclassify 권장
- migration 도구 (`tool/atlas_dsl_v2_serializer.hexa --reclassify-meta`) 는 heuristic (domain 이 `meta_*` prefix 인 `@L` 은 `@M` 후보로 list, 사용자 confirmation 후 변환)

**Backward-compat:**
- v1 reader (현 `_valid_type()`) 는 `@M` 을 reject (exit 2)
- 따라서 v2 `@M` entry 는 main atlas.n6 본체 직접 쓰기 금지, shard `atlas.append.v2-meta.n6` 에만
- v2 reader 가 shared lib 에 도입된 후 absorb 가능
- v1 reader fallback 정책 (선택): `@M` → `@L` silent rewrite, warning emit (lossy fallback, §7 falsifier 검토 후 결정)

**LoC 추정 (lint+reclassify):** 50

---

### 3.4 신규 type @T (trace) (Tier-2)

**Semantic:** ω-cycle audit trace — 어느 witness file 이 어느 fact set 를 emit 했는지 atlas 자체에 기록. raw 77 audit-ledger 의 atlas-내장 표현. `state/atlas_ingest_history.jsonl` 의 외부 chain hash 와 cross-link.

**Syntax:**

```
@T <trace_id> = witness:<witness_path>
                :: meta_audit [<compound_grade>]
  -> <fact_id_list,...>
  => <description>
```

**Example:**

```
@T trawl_2026_04_26_atlas_ingest = witness:design/hexa_sim/2026-04-26_atlas_ingest_omega_cycle.json
                                    :: meta_audit [10*+PROBE_RUN+REPO_INVARIANT]
  -> alpha_inv_codata, perfect_number_first, sigma_a000203_n6, gw_events_total_2026,
     h0_planck_2018, ns_planck_2018, ns_fractional_gap_pct, neutrino_flavors,
     neutrino_pmns_params, sm_quark_count, sm_lepton_count, gaia_astrometric_dof
  => "37 fact + 5 crossing emit by tool/hexa_sim_atlas_ingest.hexa Tier-1 7 axes"
  => "chain hash: state/atlas_ingest_history.jsonl line-by-line prev/current"
```

**Cross-link with raw 77 audit-ledger:**
- `@T` entry 의 `witness:` 값은 trawl JSON path
- trawl JSON 의 `next_cycle_dispatch` 와 atlas `@T -> fact_id_list` 가 일치해야 함 (cross-check tool: `tool/atlas_v2_trace_audit.hexa --verify-witness`)
- chain hash 는 외부 JSONL 에 위임 (atlas 안에 hash 중복 저장 안 함 — DRY)

**Backward-compat:** `@M` 와 동일 — v1 reader reject, shard `atlas.append.v2-trace.n6` 에만 emit, v2 reader 도입 후 absorb.

**LoC 추정 (emit + lint):** 50

---

### 3.5 Deprecation marker (Tier-2)

**Syntax (compound grade token 의 특수 케이스):**

```
[<grade>+retired:<reason_slug>]
```

- `retired:` prefix 가 token 의 한 종류 (allowlist §3.1 의 8 token 외 9 번째 reserved prefix)
- `<reason_slug>` 는 snake_case (예: `replaced_by_alpha_inv_v2`, `superseded_by_codata24`, `falsifier_hit`)

**Example:**

```
@C foo_constant = 6 :: physics_legacy [10*+retired:replaced_by_bar_v2]
  => "legacy fact, retained for historical reference"
  => "see @C bar_v2 for current value"
```

**Semantic:**
- still parseable (entry 정상 적재)
- v2 reader 는 deprecation warning emit (`stderr: WARN: @C foo_constant retired (reason=replaced_by_bar_v2)`)
- 삭제는 **명시적 GC tool** (`tool/atlas_dsl_v2_gc.hexa --retired-only`) 통해서만 — silent removal 금지
- GC 정책 (frozen v2.0): 1 년 이상 retired 표시된 entry 만 GC 후보, 추가로 `<- depends_on` 역참조 0 이어야 함 (의존자 있으면 보존)

**v1 backward-compat:**
- `+retired:reason_slug` 도 token 의 일종 → §3.1 와 동일하게 v1 reader 에서 grade regex fail → main atlas.n6 본체 직접 쓰기 금지, shard 에만

**LoC 추정 (lint + GC tool):** 30 + 50 = 80 total

---

### 3.6 [Backlog] Versioned id (v4 axis, Tier-3)

Phase 3 cross-repo supercycle 후 도입. Syntax 후보:

```
@C alpha_inv@v2 = 137.035999084 :: precision_update [10*+CODATA22]
@C alpha_inv@v3 = 137.035999177 :: precision_update [10*+CODATA22]
```

- `@v<N>` suffix on id — 같은 id 의 측정값 evolution tracking
- 기본 (suffix 없음) = latest
- `@v0` = original v1 entry
- 본 문서 §3 frozen scope 외 — Phase 3 이후 별도 cycle

---

### 3.7 [Backlog] Namespaced id (v5 axis, Tier-3)

```
@C nexus::alpha_inv = 137.035999177 :: physics [10*+CROSS_REPO]
@C n6::alpha_inv = 137.035999084 :: physics [10*+CROSS_REPO]
```

- `<repo>::<id>` syntax — cross-repo collision 회피
- Phase 3 atlas_omega_supercycle.hexa 직접 의존
- 본 문서 §3 frozen scope 외

---

## §4 v1 → v2 migration

**Phase 분할:**

**Phase 4a (이미 dispatch 된 next cycle):** `tool/atlas_dsl_v2_serializer.hexa` 구현
- §3.1 compound grade reader/writer (60 LoC)
- §3.2 JSON serialization bidirectional (200 LoC)
- §3.3/3.4/3.5 신규 type/marker 는 lint level 만 (warning, no enforce)

**Phase 4c+1 (본 문서 후속):** `_guarded_append_atlas()` v2 patch
- shared/blowup/lib/atlas_guard.hexa.inc 의 `_valid_type()` 확장 (`M` `T` 추가)
- grade regex 확장 (compound token 허용)
- 3 write site 모두 v2 reader 사용으로 전환 → main atlas.n6 본체에 v2 entry 직접 쓰기 가능

**Manual review 필요:**
- 기존 `@L *_pattern` `@L *_method_gap` 등 meta-domain entry 의 `@M` 재분류 (heuristic + human confirmation)
- 기존 trawl JSON 들의 `@T` entry 자동 emit (post-Phase 4 별도 cycle, §5 roadmap)

**Preservation 보증:**
- v1 의 모든 entry (현 9,624) 는 patch 후 v2 valid (no breaking change)
- byte-eq round-trip test (`tool/atlas_dsl_v2_serializer.hexa --selftest`) 가 main atlas.n6 전체에서 PASS 후에만 patch merge
- 실패 시 patch revert + falsifier hit (§7)

**Migration command sequence:**

```bash
# 1. baseline byte-eq
hexa run tool/atlas_dsl_v2_serializer.hexa --read-n6 n6/atlas.n6 --emit-json /tmp/atlas.atlas.json
hexa run tool/atlas_dsl_v2_serializer.hexa --read-json /tmp/atlas.atlas.json --emit-n6 /tmp/atlas.n6.regen
diff n6/atlas.n6 /tmp/atlas.n6.regen  # must be empty

# 2. compound grade enable (shard 에만)
echo '@C test_compound = 0 :: test [10*+PASS_LITERATURE+REPO_INVARIANT]' >> n6/atlas.append.v2-compound.n6
hexa run tool/atlas_dsl_v2_serializer.hexa --read-n6 n6/atlas.append.v2-compound.n6 --selftest

# 3. v2 reader patch (shared lib)
# (manual)

# 4. main absorb (compound + @M + @T + retired)
hexa run tool/hexa_sim_atlas_ingest.hexa --absorb  # v2 enabled
```

---

## §5 Roadmap

| Phase | Scope | LoC | Deps | Status |
|-------|-------|-----|------|--------|
| **4c (본 문서)** | grammar spec only | 600 | — | DRAFT |
| 4a | serializer (compound grade + JSON) | 260 | phase_2_a7 | dispatched |
| 4b | lens injection 5-pilot orchestrator | 300 | atlas.n6 read | dispatched |
| 4c+1 | atlas_guard v2 patch (main absorb) | 80 | 4a, 4c | pending |
| 4c+2 | @M reclassify tool (heuristic) | 100 | 4c+1 | pending |
| 4c+3 | @T auto-emit (trawl scan) | 150 | 4c+1 | pending |
| Phase 3 | namespace v4/v5/v7 (cross-repo) | TBD | atlas_omega_supercycle | deferred |
| Phase 5 | retired GC tool (1yr+) | 50 | 4c+1 | deferred |

---

## §6 EBNF (formal)

```ebnf
atlas_v2       ::= ( entry | comment | blank )*

entry          ::= type_marker SP id SP "=" SP expr SP "::" SP domain SP "[" grade_compound "]" trailer*

type_marker    ::= "@" type_char
type_char      ::= "P" | "C" | "F" | "L" | "R" | "S" | "X"        (* v1 *)
                 | "M" | "T"                                        (* v2 신규 *)
                 | "?"                                              (* v1 fallback *)

id             ::= [A-Za-z_] [A-Za-z0-9_]*                          (* v2 *)
                 | id "@v" [0-9]+                                   (* v4 backlog *)
                 | namespace "::" id                                 (* v5 backlog *)
namespace      ::= [a-z] [a-z0-9_]*

expr           ::= <free-form text up to " :: ">
domain         ::= [a-z] [a-z0-9_]*

grade_compound ::= grade_int grade_marker? ( "+" grade_token )*
grade_int      ::= [0-9]+ ( "." [0-9]+ )?                           (* alien index *)
grade_marker   ::= "*" | "!" | "?"
grade_token    ::= allowlist_token | retired_token
allowlist_token::= "PASS_LITERATURE" | "PROBE_RUN" | "BARRIER_CONFIRMED"
                 | "NEGATIVE_VERDICT" | "REPO_INVARIANT" | "CROSS_REPO"
                 | "PORTABLE" | "AXIOM_GRADE"
                 | "CODATA22" | "CODATA24"                          (* literature subdialects *)
retired_token  ::= "retired:" reason_slug
reason_slug    ::= [a-z] [a-z0-9_]*

trailer        ::= NL "  " trailer_op SP trailer_value
trailer_op     ::= "<-" | "->" | "=>" | "==" | "~>" | "|>" | "!!"
trailer_value  ::= <free-form text up to NL>

(* @T 전용 trailer 확장 *)
witness_marker ::= "witness:" path
path           ::= [^ \n]+
                                                                    (* @T entry 의 expr 위치에 옴 *)

comment        ::= "#" <free-form text>                             (* v1 호환 *)
                 | "//" <free-form text>                            (* v1 호환 *)
blank          ::= NL
SP             ::= " "
NL             ::= "\n"
```

**Ambiguity resolution rules:**
1. Token sorting: `+` 로 분리된 token list 는 ASCII sort 강제 (canonical form)
2. Trailer value 의 unescaped `::` 또는 `[` `]` 는 expr/domain boundary detection 우선 — left-most match
3. `@?` (unknown) 은 v1 호환만 — v2 신규 entry 에 사용 금지 (lint warning)

---

## §7 Falsifier (raw 71)

본 v2 spec 은 다음 조건 1+ 충족 시 즉시 retire:

**F1: Backward-compat 깨짐.**
- v1 atlas.n6 의 entry 단 1 개라도 v2 reader 가 reject
- 또는 v2 reader 가 v1 entry 를 silently mutate (예: `[10*]` → `[10+]`)
- detection: `tool/atlas_dsl_v2_serializer.hexa --selftest` byte-eq round-trip 4-회 fail

**F2: Lossy v1 → v2 → v1 export.**
- `@P/@C/@F/@L/@R/@S/@X` 7 type entry 가 v2 → v1 export 후 정보 손실
- `@M/@T` 만 lossy 허용 (v1 reader 가 reject 하므로 export 시 drop 또는 `@L` rewrite)
- lossy fallback 사용 시 stderr WARNING 명시 + audit log 기록

**F3: JSON canonical 깨짐.**
- sorted keys 위반
- null 처리 비결정성
- byte-eq round-trip 1 회라도 fail

**F4: Compound grade allowlist 위반.**
- §3.1 8 token + literature subdialect (`CODATA22` 등) 외의 token 등장 시 lint error
- 새 token 추가는 본 문서 §3.1 table revision 필수 (frozen 후 임의 추가 금지)

**F5: GC over-deletion.**
- retired 1 년 미만 entry 가 GC tool 로 삭제되면 retire (silent removal 방지의 핵심)

**Falsifier action on hit:**
1. `state/falsifiers/atlas_dsl_v2_<F-id>.jsonl` 에 record append
2. v2 patch revert
3. 본 문서 §3 의 해당 feature `[RETIRED]` mark 추가 + reason 기록
4. Phase 4a 의존 cycle 들 재dispatch

---

## §8 Residual gaps

본 spec 의 명시적 미해결 영역:

1. **`@M` heuristic reclassify rule 미확정.** "domain 이 `meta_*` prefix 인 `@L`" 은 first-cut — false-positive (예: `meta_research_program` 은 `@P` 인데 prefix 만 보면 `@M` 후보) 처리 미정.

2. **`@T` 의 witness path normalization.** `design/hexa_sim/2026-04-26_*.json` 같은 상대 경로 vs absolute path 표준화 미정. `$NEXUS_ROOT/design/...` 같은 envvar 치환 권장하나 frozen 안 됨.

3. **EBNF `expr` 의 free-form text 처리.** trailer value 안의 `::` `[` 가 escape 되지 않음 — 현재 left-most match 로 해결하나 edge case (예: `@F foo = a::b :: c [10*]`) 에서 ambiguous. v2.1 에서 escape syntax (`\::` `\[`) 도입 검토.

4. **alien index `[7.3*]` 의 JSON 표현.** §3.2 schema 는 `{"int": 7, "decimal": 3, "marker": "*"}` 로 split — 그러나 `[7.3.5]` 같은 multi-decimal 케이스 미명세. 현 atlas 에 등장 안 하나 frozen 전 확인 필요.

5. **Compound grade 의 marker 위치.** `[10*+PASS_LITERATURE]` 와 `[10+PASS_LITERATURE+*]` 는 same semantic 인가? 현 spec 은 marker (`*!?`) 가 grade_int 직후 강제 (sortable token 과 분리) — 그러나 v1 의 `[10*]` 와 일관성을 위해 marker 를 token list 앞쪽 고정으로 frozen.

6. **`retired:` token 의 sort position.** 알파벳순 정렬 시 `retired:foo` 는 다른 token 들 뒤에 옴 (`R*` prefix). 그러나 의미상 가장 중요 정보 — 사용자 가독성 vs canonical sort 의 trade-off. 현 spec 은 canonical sort 우선 (lint 가독성 보조 도구로 분리).

7. **v1 의 `==` `~>` 같은 비표준 trailer op 의 JSON 보존.** §3.2 schema 는 trailer.op 필드에 string 그대로 저장 — 그러나 future version 에서 enum 화 시 마이그레이션 cost 발생. v2.0 frozen 으로는 string 유지.

8. **Phase 4a/b/c 3 cycle 의존 순서.** trawl JSON `residual_gap[4]` 명시 — 4a → 4c (본 문서) → 4b 인지, 4a + 4b 병렬 → 4c 인지 미확정. 본 문서는 4c (spec) 가 4a (구현) 의 reference 라 가정 — 현실은 4a 가 spec 없이도 부분 진행 가능.

---

## §9 SSOT cross-reference

- **trawl source:** `design/hexa_sim/2026-04-26_phase4_atlas_dsl_v2_and_lens_injection_omega_cycle.json` (sub-path A 8 axes)
- **v1 grammar source:** `n6/atlas.n6` head 50 lines
- **v1 사용 사례:** `tool/hexa_sim_atlas_ingest.hexa` (37 fact emit)
- **v1 shard 결과:** `n6/atlas.append.hexa-sim-bridges.n6` (37 fact + 5 @X)
- **v1 guard:** `shared/blowup/lib/atlas_guard.hexa.inc`
- **audit-ledger:** `state/atlas_ingest_history.jsonl` (raw 77 chain hash)
- **Phase 3 의존:** `atlas_omega_supercycle.hexa` (cross-repo aggregation, v5/v7 backlog 의 referent)
- **Phase 4a 후행 cycle:** `tool/atlas_dsl_v2_serializer.hexa` (v3 + v8 구현)
- **Phase 4b 후행 cycle:** `tool/lens_atlas_orchestrator.hexa` (l1 + l4 + l8 pilot, 본 spec 의 @T trace 와 cross-coupling — sub-path B l6 provenance 가 @T 의 자연 표현)
- **raw strategy 적용:** hive raw 47 (strategy exploration ω-cycle), raw 70 (multi-axis verify), raw 71 (falsifier), raw 73 (structural admissibility), raw 77 (audit append-only)

---

**EOF — atlas DSL v2 Grammar Specification v2.0 DRAFT (Phase 4c witness)**
