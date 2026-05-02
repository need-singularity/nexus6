# anima_clm_invoke 3-mode benchmark — landing report

date: 2026-05-02
schema: nexus/bench_outside_noise_clm_modes/1
predecessor: BG-A (anima/tool/anima_clm_invoke.hexa wrapper land + nexus handler wire)
scope: BG-A2 — measure-only, no migration, read-only against BG-A artifacts

---

## TL;DR

The mock and local paths of the cross-repo CLM wrapper are wired and
measurable; hf path is wired but inert in this environment. Across n=10
latency samples and n=20 quality samples per mode, the mock path emits
candidates in ~0.9 s with deterministic 7-key JSON contract output, while
the local "wired pre-flight" path runs ~0.7 s and yields a higher tri-validation
pass-rate because its description string contains the empirical-keyword
"contract" and its name template avoids dup collisions with the
reality_map cycle_4 baseline. The hf path is consistently SKIPPED because
no HUGGINGFACE_API_TOKEN is exported in the local shell.

Verdict: PASS for mock+local; PARTIAL_HF_SKIPPED_NO_TOKEN for hf. The bench
file is reproducible at the deterministic-fields level (B5/B6/byte content)
across two consecutive runs; the latency fields are not byte-identical due
to inherent subprocess scheduling jitter.

---

## 3-mode result matrix

| metric | mock | local | hf |
|--------|------|-------|----|
| status | PASS | PASS (wired pre-flight) | SKIPPED (no token) |
| B1 latency mean (ms) | 897 | 685 | n/a |
| B1 latency stddev (ms) | 119 | 48 | n/a |
| B2 throughput proxy (output_bytes / latency, x10) | 663 | 1266 | 0 |
| B3 cost per call (USD x100) | 0 | 0 | 0 (deferred — pre-flight only) |
| B4 rss-kb mean | 1984 | 1984 | n/a |
| B5 max jaccard vs reality_map (x1000) | 487 | 56 | n/a |
| B6 validation pass-rate (x1000) | 250 | 1000 | n/a |
| B6 dup_fail (n=20) | 10 | 0 | n/a |
| B6 verifier_fail (n=20) | 5 | 0 | n/a |
| B6 honest_c3_fail (n=20) | 5 | 0 | n/a |
| mean output bytes | 238 | 347 | 0 |

Notes on the numbers:

- B1 absolute latency is dominated by hexa subprocess startup + resolver-bypass
  shell (~0.5 s baseline on this mac); true CLM forward time is in the noise.
  The mock path being slower than local is counter-intuitive — both pay the
  same subprocess overhead, but mock path runs the seed-branch logic which
  occasionally triggers the dishonest emit path that produces a slightly
  longer string. The 200 ms gap is within ~2 stddev of mock and ~4 stddev of
  local, so the ordering is borderline rather than robust.
- B2 throughput is deliberately a proxy: it divides the JSON-line byte length
  by the wallclock latency and rescales to "tokens-per-second-times-10" assuming
  ~4 bytes per token. It is intended for cross-mode ordering, not for
  comparison with real LoRA throughput numbers.
- B5 jaccard novelty: the mock path repeatedly emits names that collide with
  its own cycle-seed pattern (and one description string contains the word
  "pattern" which lexically overlaps with the n6/Hexad node descriptions in
  reality_map cycle_4). Local mode emits a distinct name template
  ("local_wired_primitive_cycle_<n>_plen_<p>") that has near-zero token
  overlap with the canonical n6 substrate.
- B6 mock pass-rate of 25 % is not a defect — the wrapper deliberately
  rotates through four cycle-seed branches (concept/law/pattern/dishonest)
  and one of them triggers the duplicate-name fall-through and another sets
  honest_c3_pass=false. This is the wrapper's selftest contract surface.
- B6 local pass-rate of 100 % means the wired pre-flight description string
  ("contract" + "pre-flight") matches the empirical-keyword regex without
  ever colliding on the dup or honest predicates.
- B4 rss-kb is identical between modes because both pay the hexa subprocess
  cost in the parent shell snapshot, not the child process; this is a known
  measurement limit (see caveat C4).

---

## use-case recommendation matrix

| use-case | recommended mode | rationale |
|----------|------------------|-----------|
| selftest reproducibility | mock | only mode with byte-identical 2-run guarantee per cycle-seed |
| handler smoke at $0 cost | mock | deterministic, no dependencies |
| local-pipe end-to-end check | local | wired pre-flight verifies wrapper + handler subprocess plumbing without weight load |
| real Mk.XII v3 forward (deferred) | local | when actual safetensors land in state/v10_benchmark_v4_clm/clm_v4_530m, this is the path |
| novel-candidate generation | local then hf | local for $0 floor, hf for diversity beyond cycle-seed determinism |
| validation pass-rate maximization | local | description template matches verifier keyword set; mock intentionally fails 75 % |
| stress / cost-sensitive batch | mock | $0 + fastest deterministic path |

The cross-mode trade-off is essentially: mock is the fastest deterministic
floor with intentional validation failures for testing, local is the wired
contract layer with the highest pass-rate, and hf is the only path that
will eventually exercise a real third-party model — but only once the
gating token is supplied and a per-call cost cap is enforced.

---

## raw 92 falsifier registration outcomes

The bench pre-registered six measurable falsifiers (B1 through B6). All
six emitted concrete numeric outputs in the modes where the wrapper did
not return SKIP. The hf mode's six metrics are all reported as zero with
an explicit `SKIPPED_no_token` status, which is the pre-registered
graceful-degrade path rather than a measurement failure.

The strongest falsifiable claim from this run is "the local mode wired
pre-flight contract has higher tri-validation pass-rate than the mock
mode under the cycle_4 reality_map baseline" — measured 1000/1000 vs
250/1000 with no overlap. If a future cycle changes the reality_map node
descriptions to contain the local pre-flight name pattern, the local
pass-rate will drop and this claim will be falsified.

---

## file index

| file | sha256 | LOC / bytes |
|------|--------|-------------|
| nexus/bench/bench_outside_noise_clm_modes.hexa | 4bcc83d03e3c0fdcd0c8bc83b2ffe106454c6fcb5d9dd49c4ef26f5b0614ffb3 | 613 LOC |
| nexus/state/bench_outside_noise_clm_modes/results_2026_05_02.json | b7c65e3e78a37c1f3e62e62d38ca92feff5ccfce624b7cd1026d03fd59ff4205 | 1675 bytes |
| anima/tool/anima_clm_invoke.hexa (BG-A, read-only) | a509747cc029f3af0c55296f0a0f41c18844cf577250e78ebbb77ea3b1273a10 | 364 LOC |
| nexus/tool/handlers/outside_noise_clm_handler.hexa (BG-A, read-only) | 0d57f29b601a11b4e4e859e698641f0da3e02a6fd1d28d1db37e0f4023a2a480 | 590 LOC |
| nexus/state/markers/outside_noise_clm_real_inference_landed.marker (BG-A) | (timestamped 2026-05-02T14:07:58Z) | 671 bytes |
| nexus/state/markers/anima_clm_3_mode_benchmark_landed.marker (BG-A2) | (this run) | — |

Selftest evidence: 5/5 PASS for the bench file (`hexa run nexus/bench/bench_outside_noise_clm_modes.hexa --selftest`).

---

## raw#10 caveats

- C1 — local mode is "wired pre-flight," not a real Mk.XII v3 forward.
  The wrapper's local path requires both `ready/core/conscious_chat.py`
  and the `clm_v4_530m` metadata directory; both are present, but the
  actual safetensor weights are not loaded. Real-forward latency will
  almost certainly dominate the current 0.7 s number once weights land.
- C2 — hf mode is fully wired but cannot be measured without a token.
  No live HF call was attempted, so the $0.50 micro-budget cap was not
  exercised. When a future cycle exports HUGGINGFACE_API_TOKEN, the
  bench will execute hf without modification; the cost cap is enforced
  at the wrapper layer and re-stated in the results JSON header.
- C3 — n=10 latency / n=20 quality is small. The mock latency stddev is
  119 ms on a mean of 897 ms (CV ~13 %), which is above the threshold
  where a single outlier could shift the mean. A future cycle should
  bump n_lat to 50 once the local real-forward path lands.
- C4 — B4 rss-kb is sampled in the parent shell process, not the child
  hexa subprocess. The reported 1984 kb is therefore a constant baseline
  rather than a true per-call memory footprint. A higher-fidelity
  measurement requires either `/usr/bin/time -l` parsing or a per-pid
  `ps` snapshot inside the child — both deferred.
- C5 — B5 is jaccard token-set similarity, not cosine vector similarity.
  hexa-lang lacks a native embedding stack and the cross-repo subprocess
  cost of invoking a sentence-transformer Python harness was judged too
  high for this cycle. Jaccard is monotonic with semantic similarity at
  the bag-of-words level but loses ordering for synonyms.
- C6 — Bench-time wrapper output write uses bash heredoc with a
  `ANIMA_BENCH_EOF` sentinel because hexa-lang in this dispatch build
  has no `open()/write()/close()` builtins (verified via runtime error
  on the first run). If a future JSON body legitimately contains the
  sentinel string, the heredoc will terminate early; the probability is
  negligible for the current schema but should be re-asserted if the
  schema grows.
- C7 — BG-A marker arrived at 2026-05-02T14:07:58Z, after the bench
  file's first execution at 23:09 local time but before the second
  byte-identical run at 23:10. The bench was therefore executed twice:
  once with `bg_a_marker_present=false`, once with `=true`. The final
  results JSON on disk reflects the marker-present state. The two
  runs differed only in the `bg_a_marker_present` and `bg_a_status`
  fields plus the latency jitter; all B5/B6 deterministic fields were
  byte-identical.
