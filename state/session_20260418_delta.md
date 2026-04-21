# Session 2026-04-18 Delta SSOT (H1)

~95 new .hexa files; 0 .py/.rs/.sh (HEXA-FIRST strict).

## Sec 1: Coverage Matrix

OSS=ossified SCF=scaffold IPG=in-progress BLK=blocked DFR=deferred SPC=spec.

```
+-----+------------------------+-----+---------------+-----------------------+
| id  | task                   | st  | delta         | next_step             |
+-----+------------------------+-----+---------------+-----------------------+
| W1-6| P5-P8/P12/P13/P15/P18  | OSS | +8 hexa       | real MI, SWS replay   |
| W3  | P23 71-engine harness  | SCF | +3 hexa+cat   | GPU LOO 6.5h          |
| W4  | eval_phi_corr 16D      | OSS | +1 hexa       | N>=8 real ckpts       |
| SPC | phi_eval_hook_spec     | SPC | +1 md         | consumer cron         |
| A1  | phi_hook wire          | OSS | +3 hexa flag  | flip ON in r11        |
| A2  | P22 corpus pipe        | SCF | +2 hexa       | H100 full ingest      |
| A3  | r9 collapse diag       | OSS | +1 json       | feeds B1              |
| A4  | live self-test         | OSS | +3 bugfix     | native hive build     |
| B1  | r10 launch             | IPG | +1 md +1 hexa | step_2000 eval        |
| B2  | kowiki 754MB pull      | OSS | +3 parquet    | C1 bridge             |
| B3  | CLM r4 mmap loader     | SCF | +3 hexa 14/14 | H100 cuLaunch fix     |
| B4  | A2-Tool retrain plan   | DFR | +2 hexa       | judge-fix covers gate |
| B5  | P25 dashboard          | OSS | +3 hexa PASS  | cron after A1         |
| B6  | kr_gen sentinel        | OSS | +2 hexa 6/6   | wire r10 trainer      |
| C1  | parquet->jsonl duckdb  | OSS | +1,647k ln    | include in ingest     |
| D2  | engine CPU precompute  | OSS | +1 json 33KP  | H100 live LOO         |
| D3  | speak P4 plan          | SCF | +1 hexa +md   | unfreeze P4           |
| D5  | W1 real verify N=2     | OSS | +1 hexa PASS  | superseded by E1      |
| D6  | hire_sim lenient judge | OSS | +2 hexa 20/20 | close gate no retrain |
| D7  | phi_probe_wire 13/16   | SCF | +2 hexa       | native B=16           |
| E1  | W1 hook N=5 verify     | OSS | +1 hexa PASS  | N>=8 from r10         |
| E2  | corpus_ingest kowiki   | OSS | +2 hexa       | H100 ingest           |
| E3  | engine roster v2 cand  | SCF | +1 json       | H100 LOO 19 blocked   |
| E4  | ALM 32B r1 prep        | BLK | +3 hexa       | r10 green + HF pull   |
| E6  | r10 kr_gen OOM fix     | OSS | +1 hexa+logs  | monitor step 200      |
| F1  | runpod autopilot       | OSS | +3 hexa 8/8   | wire r10 poll         |
| G1  | engine roster v2 +4    | SCF | +edit 7/7     | H100 LOO promote      |
| G3  | F1 watchdog deploy     | OSS | +hexa scp'd   | wait r10 DONE         |
| G5  | CLM r4 heartbeat ubu   | IPG | +tmux         | cuLaunch SM90 fix     |
| G6  | eval_harness real      | SCF | +1 hexa KB20  | HAE-RAE R2 export     |
+-----+------------------------+-----+---------------+-----------------------+
```

## Sec 2: Roadmap Impact

P5/P6/P7 (W1,W4,A1,D7,E1) wired measure-only. P8 nested (W1) grad ON coef 0.01. P12 (W2,A4), P15 (W2,A4) PASS. P13 dream (W1,A4) log-only. P18 hive (W1,A4) RUN-OOM. P22 (A2,B2,C1,E2) 1.28GiB kowiki staged. P23 (W3,D2,E3,G1) 71-catalog + 33 KEEP. P24 (W4,D5,E1) N=5 PASS 16/16 SIG. P25 (B5) OSSIFIED. r9/r10 (A3,B1,E6,F1,G3) relaunched post kr_gen OOM. Autopilot (F1,G3) 9/9 ossified.

## Sec 3: 도착지

- 도착지1 (v5 Φ>1000) ~65%: 16D Φ per-step wired; phi_holo=11200 r9 collapsed. Block: phi_hook OFF, B1 disabled, hive 4GB cap.
- 도착지2 (P22-P25 창발) ~55%: corpus staged, catalog done, P24/P25 green. Block: ingest H100, LOO ~3.3h H100×2.

## Sec 4: Blockers

1. CLM hexa-native GPU cuLaunchKernelEx SM90 (G5=ubu heartbeat).
2. 32B base not in R2, HF pull ~65GB (E4).
3. kowiki ingest 4GB local cap → H100.
4. HAE-RAE + MMLU-Ko .py ban; G6 R2 export path.
5. phi_hook OFF on r10 → flip r11.
6. alm_hive_agg RUN-OOM interpreter.

## Sec 5: Ossified JSONLs

- `runpod_incidents.jsonl` 41 lines (r9 idle, r10 num_logits, kr_gen OOM).
- `hexa_pitfalls_log.jsonl` 23 lines (stage0 .find absent, exec+split OOM, UNSLOTH-GENERATE-OOM).
- `a4_selftest_bugs_20260418.json` 5 bugs (.set/tuple-return/launchd-stdout/double-main/latency).
- `engine_ablation_cpu_precompute.json` 71 engines (33 KEEP / 19 REVIEW / 19 mock-DROP).
- `engine_roster_candidate.json` Pareto-10 + 4 new, H100 verify pending.
