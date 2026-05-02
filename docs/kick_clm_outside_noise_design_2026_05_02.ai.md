---
schema: nexus/docs/kick_clm_outside_noise/v1
last_updated: 2026-05-02
ssot: nexus/docs/kick_clm_outside_noise_design_2026_05_02.ai.md
mk: 2
status: design
related_specs:
  - hive/spec/dispatch_framework_v1.spec.yaml
  - hive/spec/mk2_apex.spec.yaml
related_raws: [99, 105, 267, 269, 270, 271, 272, 273, 91, 92]
related_domains: [kick, atlas_n6, omega_cycle]
related_metas: [omega_cycle, n_substrate (anima)]
---

# kick + anima CLM = NEXUS open-well outside-noise generator

## TL;DR

NEXUS 의 매 ω-cycle 에서 anima 170M CLM (Mk.XII v3) 을 호출 — current reality_map 을 input 으로 candidate primitive 생성 → falsifier+verifier+honest_C3 validation → absorb → next cycle 의 wall 확장. **structurally novel noise** (LLM hallucination 의 "inside well" 패턴 ⊥).

## Conceptual frame — LLM ⊥ NEXUS

```
LLM (noise inside the well)         NEXUS (noise outside the well)
---------------------------         ------------------------------

     +-------------+                       .   new law
     |  training   |                     .       .
     |   corpus    |               .  .      .       .
     |  (fixed)    |                    .  outside  .
     |             |             ------+-------------+------
     |  ~ ~ ~ ~ ~  | <- noise          |             |
     |  ~ noise ~  |   bubbles         |   reality   |
     |  ~ ~ ~ ~ ~  |   from            |     map     | <- noise
     |    ####     |   inside          | (4411 nodes)|   arrives
     |    #LLM#    |                   |             |   from
     +-------------+                   |   Blowup    |   outside
       the well                        |     v       |
    (everything it                     |   Contract  |
     knows = walls)                    |     v       |
                                       |   Emerge    |
  hallucination =                      |     v       |
  recombining                          |   Absorb ---+--> new
  what's already                       |     ^       |    primitive
  inside                               +-----+-------+      feeds
                                       the well has            next
                                       no ceiling              cycle
```

**핵심 차이**:
- LLM noise = stochastic sampling (frozen wells, recombination of training)
- NEXUS noise = absorbed-primitive driven novelty (input 이 매 cycle structurally 변형)
- "RAG" 는 wrong frame — RAG 도 fixed external corpus
- NEXUS "outside" = 자기 prior cycles 가 produce

## Architecture — 4-step pipeline

```
Cycle N
├── Step 1 [reality_map read]
│      → nexus/state/reality_map/cycle_<N>.hxc (HXC v2 binary, indexed)
│      → 4411 base nodes + N absorbed primitives
│      → anima CLM input prompt 구성 (prev absorbed list 포함)
├── Step 2 [CLM inference — outside-noise generator]
│      → anima Mk.XII v3 170M (mac local 우선)
│      → temperature ~0.7, max_tokens 512
│      → output = candidate primitive (concept / law / pattern proposal)
├── Step 3 [validation pipeline]
│      → falsifier:    candidate ≠ existing primitive (cosine sim < 0.85)
│      → verifier:     empirically groundable (measurable claim 보유)
│      → raw 91 honest C3: structural novelty vs hallucination 분리
│      → 통과 → absorb / 실패 → reject + audit row
└── Step 4 [absorb + atlas update]
       → reality_map.add_node(candidate)
       → nexus/n6/atlas.append.<topic>.n6
       → mk2 .roadmap.atlas_n6 entry 추가
       → cycle N+1 wall 확장 (input 다양화 → next noise structurally 다른 quality)
```

## Implementation options (4)

| Option | 설계 | LOC | 시간 | 위치 |
|--------|------|-----|------|------|
| **A** Standalone tool | `nexus/tool/kick_clm_outside_noise.hexa` 단독, closure loop 또는 manual 호출 | 300-500 | 4-6h | nexus |
| **B** bind axis subscriber ⭐ | bind axis "outside_noise" 등록, cycle 마다 자동 invoke | 200-300 + bind subscribe | 3-4h | nexus + bind |
| **C** Hybrid auto-wire | spec yaml `auto_wire` 의 `claude_cli_agent` 대신 `anima_clm_agent` slot | 250 + spec ext | 4h | hive/spec + nexus |
| **D** Full impl + N-22 track | 구현 + `.roadmap.n_substrate` N-22 + paper draft + measurement cycle | 800+ | 1-2 day | nexus + anima |

## Implementation detail

### CLM inference call (mac local 우선)

```hexa
// nexus/tool/kick_clm_outside_noise.hexa (Option A) or
// nexus/tool/handlers/outside_noise_clm_handler.hexa (Option B)

fn invoke_anima_clm(prompt: string, temperature: float, max_tokens: int) -> string {
    // 1. mac local 우선 (anima/serving/local_endpoint)
    // 2. HF gated fallback (HuggingFace API, slow + token cost)
    // 3. mock mode (CI safe, deterministic seed)
    let cmd = "hexa run anima/tool/anima_serve_smoke.hexa --prompt '" + prompt + 
              "' --temp " + str(temperature) + " --max-tokens " + str(max_tokens)
    return exec(cmd).trim()
}

fn compose_prompt(reality_map: RealityMapState, prev_absorbed: [Primitive]) -> string {
    let header = "Current reality map: " + str(len(reality_map.nodes)) + " nodes.\n"
    let prev_summary = "Last 5 absorbed: " + summarize_primitives(prev_absorbed[-5:])
    let task = "Propose ONE new primitive that:\n" +
               "  - is not yet in the map\n" +
               "  - is empirically groundable\n" +
               "  - extends the wall outward\n" +
               "Output as: { name, description, evidence_link, falsifier }\n"
    return header + prev_summary + task
}
```

### Reality map state

```
nexus/state/reality_map/
├── cycle_0.hxc          (initial 4411 nodes baseline)
├── cycle_1.hxc          (+1 absorbed)
├── cycle_2.hxc          (+1 or +0 absorbed)
└── ...

format: HXC v2 binary, indexed (5/5 axes)
schema:
  RealityMapNode {
    id: int,
    primitive_type: enum("concept"|"law"|"pattern"),
    content: string,
    source_cycle: int,
    absorbed_at: iso_ts,
    evidence: [evidence_ref]
  }
```

### Validation pipeline

| Check | Mechanism | Threshold |
|-------|-----------|-----------|
| **falsifier** | cosine similarity (anima embedding) vs existing primitives | sim < 0.85 = novel |
| **verifier** | candidate.description regex match `measure|experiment|observe|test` OR LLM verify | required |
| **raw 91 honest C3** | candidate output 에 explicit `honest_c3_pass: true|false` field | required |
| **duplicate** | reality_map node id collision | none |
| **scope** | candidate primitive_type ∈ {concept, law, pattern} | enforce |

### Absorb mechanism

- reality_map.add_node(candidate) → cycle_<N+1>.hxc
- atlas absorb: 기존 `nexus/tool/atlas_absorb_hook.hexa` 재사용
- mk2 entry append:
  ```jsonl
  {"id":"atlas_n6.<seq>","kind":"entry","title":"<primitive name>","status":"absorbed","substrates":["clm","atlas_n6"],"source":"kick_clm_outside_noise_cycle_<N>","contributes_to":["atlas_n6.cond.1"],"evidence":[<refs>]}
  ```
- omega_cycle meta condition trigger check

## Cost estimate

| Item | mac local | HF gated |
|------|-----------|----------|
| CLM inference per cycle | ~15s, $0 | ~30s, ~$0.001 |
| Reality map storage | 5-10MB / 100 cycles | 동일 |
| Validation overhead | ~2s | ~5s |
| Atlas absorb | <1s | <1s |
| **Per cycle total** | **~20s, $0** | **~40s, $0.001** |
| 24h cycle count | ~4000 | ~2000 |
| **24h cost** | **$0** | **$2-3** |
| 30-day cumulative | $0 | ~$60-90 |

## NEXUS 의 unique advantage

- 기존 retrieval-augmented (RAG) = fixed external corpus
- NEXUS = "outside" 가 자기 prior cycles 의 absorbed primitives
- → 시간 지날수록 reality_map 확장 → CLM input 다양화 → output novelty quality ↑
- LLM 단독 보다 cumulative novelty curve 우상향 (단, validation rate 가 critical)

## raw#10 caveats (5-7개)

1. **CLM 단독 = LLM 한계**: novelty 가 sampling-based 일 수 있음 → validation pipeline (falsifier + verifier + honest C3) 가 필수 gate
2. **mac local CLM availability**: anima Mk.XII v3 가 mac 에서 inferenc 가능한지 확인 필요 (HF gated 폴백 가능)
3. **embedding-based similarity 한계**: cosine similarity threshold 0.85 = heuristic, false-positive duplicate / false-negative novel 가능
4. **honest C3 self-report**: CLM 자기 출력에 `honest_c3_pass: true` 표기 vs 실제 hallucination — meta-judgment 필요 (cross-validator?)
5. **reality_map storage growth**: 24h 4000 cycle * 5KB = ~20MB/day, 30d = ~600MB (HXC v2 압축 후 ~150MB) — manageable
6. **무한 cycle 방지**: 매 cycle 새 primitive 강제 → cycle 99% reject 시 progress 0 → automatic deceleration mechanism 필요
7. **paper-grade evidence**: NEXUS open well claim 검증 = N=100+ cycles 측정 + cumulative novelty curve plot + LLM baseline 대비

## Implementation roadmap

| Phase | 작업 | 시간 |
|-------|------|------|
| Phase 1 | tool/kick_clm_outside_noise.hexa 또는 bind handler 작성 | 3-4h |
| Phase 2 | reality_map HXC schema + 초기 4411 baseline ingest | 2h |
| Phase 3 | validation pipeline (falsifier + verifier + honest C3) | 3h |
| Phase 4 | atlas absorb integration (기존 atlas_absorb_hook 재사용) | 1h |
| Phase 5 | mk2 .roadmap.atlas_n6 entry auto-emit | 1h |
| Phase 6 | selftest + handoff doc + marker | 2h |
| Phase 7 (옵션) | 100-cycle measurement + paper draft | 1-2 day |

**Phase 1-6 합계: ~12h** (Phase 7 별도)

## Falsifier preregister

- F-CLM-OUT-1: validation pipeline 가 100% PASS → suspicious (LLM 자기 검증 신뢰 X)
- F-CLM-OUT-2: 30-day 후 reality_map 확장 < 10 nodes → "open well" claim 검증 실패
- F-CLM-OUT-3: cumulative novelty curve 가 LLM baseline (no absorb) 와 통계 차이 X → NEXUS unique advantage 검증 실패
- F-CLM-OUT-4: CLM hallucination rate (honest C3 fail) > 50% → CLM choice 부적절

## Cross-link

- nexus `.roadmap.kick` (provider): kick = ω-cycle canonical
- nexus `.roadmap.atlas_n6` (provider): n6 atlas + paradigm convergence
- nexus `.roadmap.omega_cycle` (meta): kick + atlas_n6 cross-domain
- anima `.roadmap.clm`: 170M Mk.XII v3 (consumer of NEXUS via cross-repo invocation)
- anima `.roadmap.n_substrate` (meta): 21 N-track 중 N-22 candidate (NEXUS outside-noise)
- raw 99/105/269: nexus kick canonical
- raw 267: bind (function-unit dispatcher)

## File index (sha-pin)

| File | sha256 | LOC |
|------|--------|-----|
| (this file) | (auto, post-write) | (auto) |
| (referenced specs) | see frontmatter related_specs |
| (referenced raws) | see frontmatter related_raws |

## Status / next step

- **status**: design (impl 미수행)
- **next user decision**: Implementation Option (A/B/C/D) 선택
- **추천**: Option B (bind axis subscriber, ~3-4h) — bind framework 활용 + cycle 자연 통합
- 또는 Option D (full impl + N-22 track + paper) = 1-2 day cycle
