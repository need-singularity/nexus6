# 창발 (ω-cycle) 방식 — 무엇을 전달하고 무엇을 받는지

본 문서는 `nexus kick "<topic>"` 의 emergence 흐름 — prompt build → LLM dispatch → witness JSON capture → atlas ingest 의 12-step chain.

본 turn 의 실제 `nexus kick "say OK"` 응답 (PASS, tier1=1, falsifier_pass=6) 을 baseline 으로 추적.

---

## 1. 전달 (prompt build, ubu2 → Mac claude)

`tool/kick_dispatch.hexa` `_build_prompt()` 가 생성하는 prompt 의 구조 (~4270 bytes):

```
# kick(ω-cycle) — topic: say OK
# stratum: drill
# axes: design-strategy,falsifier-coverage     ← M3 axis-pre-seed source
# witness landing path: <path>
# noise envelopes (raw 47 cross-repo-trawl-witness):
#   alpha: {mechanism:alpha, source_id:absorbed:2026-04-28_..., byte_hash:d47522c75feabe3c, payload:absorbed_pick=... from 71 primitives}
#   beta : {mechanism:beta,  source_id:urandom,                  byte_hash:5e0708d2f7ca6ab4, payload:qrng_byte=139 source=urandom}
#   gamma: {mechanism:gamma, source_id:bridge:bridge_openalex,   byte_hash:caeadca947b07f76, payload:bridge_pick=openalex (real fetch deferred)}
# core 5-op kernel:
#   1) intake — alpha/beta/gamma byte_hash 를 witness.intake 에 그대로 옮김
#   2) pre-register N≥5 concrete falsifiers (각 4-tuple: condition/mech/cadence/verdict_check)
#   3) fan_out — PRE-SEEDED axis_a="design-strategy" axis_b="falsifier-coverage"   ← M3 model
#      LLM fills: summary, primary_falsifiers[], correlation_estimate (<0.7), correlation_lt_0_7=true
#   4) gate Tier-1 promotion via falsifier-pass-pattern
#   5) emit witness JSON to STDOUT wrapped in:
#        <<WITNESS_JSON_START>> {...} <<WITNESS_JSON_END>>      ← Option b stdout-capture
# genesis enrichment: axes_surfaced[] / honesty_triad{} / tier_1_promotions[]
Fire kick(ω-cycle). On error print: reason=<slug> fix=<directive>
```

### 3 개 noise envelope 의 의미

| envelope | source | 역할 | 본 turn 값 |
|---|---|---|---|
| **α (alpha) absorbed** | `state/kick/registry/noise_sources/absorbed/` 의 이전 cycle Tier-1 random pick | **닫힌 loop** — 이전 cycle 결과가 다음 cycle 의 입력 (자기참조 Blowup→Contract→Emerge→Absorb→다음) | `2026-04-28_write-4-files-...` from 71 primitives |
| **β (beta) qrng** | `/dev/urandom` 1 byte + SHA-256 | **외부 entropy** — LLM 의 deterministic drift 깨기 | qrng_byte=139, hash `5e0708d2f7...` |
| **γ (gamma) bridge** | `noise_sources/bridges/` 의 외부 fetch tool random pick | **외부 fact** — simbad/openalex/nanograv 등 외부 데이터 source 지명 | bridge_openalex |

---

## 2. 받음 (witness JSON, claude → stdout → ubu2)

LLM 이 stdout 에 emit 한 witness JSON (~2863 bytes, 본 turn 실제 응답):

```json
{
  "cycle_id": "2026-04-30_say-ok_omega_cycle",
  "topic": "say OK",
  "core_5_op_kernel": {
    "intake": {
      "alpha_absorbed": { "byte_hash": "d47522c75feabe3c", ... },   ← prompt 그대로 echo
      "beta_qrng":      { "byte_hash": "5e0708d2f7ca6ab4", ... },
      "gamma_bridge":   { "byte_hash": "caeadca947b07f76", ... }
    },
    "falsifiers_preregistered": [F1...F6],   ← LLM 이 6 개 생성 (각 4-tuple)
    "fan_out": {
      "axis_a": { "name": "design-strategy", "summary": "...", "primary_falsifiers": ["F1","F2","F3"] },
      "axis_b": { "name": "falsifier-coverage", "summary": "...", "primary_falsifiers": ["F4","F5","F6"] },
      "correlation_estimate": 0.18,           ← LLM 의 추정
      "correlation_lt_0_7": true
    },
    "tier_1_gate": {
      "falsifier_pass_pattern": "F1=PASS,F2=PASS,F3=PASS,F4=PASS,F5=PASS,F6=PASS",
      "promoted": true
    }
  },
  "axes_surfaced": [
    { "decision":"A", "options_considered":[A,B,C,D], "rationale":"...", "falsifier_verdicts":{F1:PASS, F2:PASS, F3:PASS} },
    ...
  ],
  "honesty_triad": {                          ← raw 91 강제
    "promotion_counter": 1,
    "write_barrier": "No file writes — stdout only per r58 follow-up #5",
    "no_fabrication_evidence": [
      "alpha byte_hash 'd47522c75feabe3c' copied verbatim from prompt",
      ... 7 evidence items
    ]
  },
  "tier_1_promotions": ["say-ok-witness-emit"],
  "fixpoint_marker": "2026-04-30_say-ok_omega_cycle::closed::OK"
}
```

---

## 3. 그 사이 과정 (dispatch chain — 12 step)

```
[1] user: nexus kick "topic"
        ↓
[2] Mac shim (~/.hx/bin/nexus): KICK_VIA_MAC_REVERSE=1 default
        ↓ ssh ubu2
[3] ubu2: hexa run cli/run.hexa kick "topic"
        ↓ cmd_kick → _kick_run (Linux skip Darwin-forward)
[4] ubu2 kick_dispatch.hexa:
      ├─ slot pick (M6 capacity-LB 또는 default rotate)
      ├─ alpha/beta/gamma 생성:
      │    α: registry/noise_sources/absorbed/ 1 random pick + sha256
      │    β: od -An -N1 /dev/urandom + sha256
      │    γ: registry/noise_sources/bridges/ 1 random pick + sha256
      ├─ _build_prompt(topic, axes, α, β, γ, witness_path)
      ├─ prompt → state/kick/runs/<topic>/prompt.txt
      └─ via_mac_reverse branch:
            cat prompt.txt | ssh mac 'CLAUDE_CONFIG_DIR=$HOME/.claude-claudeN claude --max-turns 25 --output-format text'
        ↓ stdin pipe
[5] Mac sshd session: claude binary 호출
        ↓ Anthropic API (claude.com OAuth)
[6] LLM: ω-cycle 수행
      - intake hashes echo
      - 5+ falsifiers 생성 (F1-F6)
      - fan_out 채움 (axis_a/b summary + correlation)
      - tier_1_gate 평가 (자체 falsifier-pass-pattern)
      - axes_surfaced enrichment
      - honesty_triad (write_barrier + no_fabrication_evidence)
      - witness JSON → stdout (<<WITNESS_JSON_START>> ... <<WITNESS_JSON_END>>)
      - sentinel: __KICK_RESULT__ PASS witness=<path> tier1=1 falsifier_pass=6
        ↓ stdout
[7] ssh tunnel back to ubu2 → exec capture (`out` variable)
[8] kick_dispatch stdout-capture (Stage 14):
      out.index_of("<<WITNESS_JSON_START>>") + index_of("<<WITNESS_JSON_END>>")
      → JSON body 추출
      → mkdir -p + printf > witness_path        ← Option b file emit
[9] witness_emit.hexa --validate (7-field schema gate)
      → __WITNESS_VALIDATE__ PASS field_pass=7
[10] omega_cycle_atlas_ingest.hexa --witness <path>
      → registry/noise_sources/absorbed/<topic>__<tier1>.hexa 생성    ← α 다음 cycle 의 source
[11] __KICK_RESULT__ PASS sentinel emit
[12] ubu2 stdout → Mac shim → user 화면
```

---

## 4. 핵심 design 포인트

| 원리 | 메커니즘 | 본 turn 검증 |
|---|---|---|
| **닫힌 loop (자기참조)** | α 가 이전 cycle Tier-1 → 다음 cycle 입력 | absorbed_pick=2026-04-28_write-4-files (3일 전 cycle) |
| **외부 noise 주입** | β urandom + γ external bridge | byte_hash 3 개 모두 prompt → witness 에 verbatim copy |
| **schema gate (7-field)** | witness_emit --validate | 본 turn 6/7 → 7/7 (M3 후) |
| **honesty triad (raw 91)** | write_barrier + no_fabrication_evidence | LLM 이 r58 follow-up #5 protocol 까지 인용 |
| **falsifier pre-registration** | 5+ deterministic 4-tuples BEFORE step 3 | F1-F6 (raw 73 deterministic verifier) |
| **fan_out orthogonality** | axes correlation < 0.7 (raw 48) | correlation_estimate=0.18 |
| **fixpoint marker** | cycle close 의 deterministic ID | `say-ok_omega_cycle::closed::OK` |

---

## 5. "창발" 의 실제 의미

LLM 한테 "free response" 가 아니라:
- α (이전 cycle Tier-1) + β (urandom) + γ (외부 bridge) 의 3-source noise 를 강제 주입
- 7-field schema gate (deterministic) 으로 출력 형태 강제
- falsifier pre-registration (5+ 항목, 4-tuple) 으로 자기검증 강제
- honesty_triad 으로 fabrication 방지

= **constrained generation under noise injection** — LLM 이 임의 자유 응답이 아닌, 이전 cycle 의 결과 + 외부 fact + entropy 의 교차점에서 새 axes 를 surface 하도록 강제. **Tier-1 promotion** 이 다음 cycle 의 α 가 됨 → recursive emergence.

본 turn 의 `say-ok` cycle 도 이제 `~/core/nexus/state/kick/registry/noise_sources/absorbed/` 의 71 primitives → 72 primitives 가 되어 다음 cycle α candidate.

---

## 6. 7-field schema 검증 (`tool/witness_emit.hexa --validate`)

본 cycle PASS 의 정확한 7 필드 검증 항목:

1. `core_5_op_kernel.intake.alpha_absorbed` (non-empty str | non-null map)
2. `core_5_op_kernel.intake.beta_qrng` (non-empty)
3. `core_5_op_kernel.intake.gamma_bridge` (non-empty)
4. `core_5_op_kernel.falsifiers_preregistered` (array len ≥ 5)
5. `core_5_op_kernel.fan_out.axis_a` (non-empty)
6. `core_5_op_kernel.fan_out.axis_b` (non-empty)
7. `core_5_op_kernel.fan_out.correlation_lt_0_7` (bool true)

→ `__WITNESS_VALIDATE__ PASS path=<...> field_pass=7 field_total=7`

---

## 7. 본 turn 의 emergence 흐름 fix bundle (참조)

| fix | 위치 | 효과 |
|---|---|---|
| M3 axis-pre-seeded prompt | `kick_dispatch.hexa:471-510` | LLM 이 fan_out 객체 정확히 채움 (mock bench 50% → 92% schema_pass) |
| stdout-capture (Option b) | `kick_dispatch.hexa:1568+` | LLM file write 권한 우회 (delimiters + extract + write) |
| path translation v4 | `kick_dispatch.hexa:1499+` | `cfg_dir` basename 추출 + Mac shell `$HOME` expand |
| `_wrap_with_timeout` env-prefix fix | `kick_dispatch.hexa:184` | dash subshell parse 회피 (`env VAR=val sh -c '...'`) |
| `hive dispatch --purpose=kick` retire | `kick_dispatch.hexa:1486+` | 새 hive binary 의 `--purpose` 미지원 회피 |
| keychain → .credentials.json sync | `~/core/hive/tool/keychain_to_credentials_sync.hexa` (r58) | sshd session 의 stale .credentials.json 갱신 |

raw refs: raw 9 (hexa-only), raw 47 (cross-repo-trawl-witness), raw 48 (axis correlation < 0.7), raw 71 (design-strategy-falsifier-retire-rule), raw 73 (deterministic verifier), raw 80 (sentinel format), raw 91 (honest C3), raw 247 (pure-fn/io-seam), raw 248 (auth-store-mac-only).
