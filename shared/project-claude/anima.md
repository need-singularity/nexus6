# anima — 의식 엔진

<!--
# @convergence-meta project=anima updated="2026-04-12T23:59Z" strategy="ossified/stable/failed 수렴 추적" last_closed_loop_promotion_date=2026-04-12 last_closed_loop_promoted_count=1 last_closed_loop_promoted_ids=SCALING_LAW_CLM_D16 last_closed_loop_law_ids=1157 last_closed_loop_registered_in="shared/consciousness/consciousness_laws.json#laws.1157" last_closed_loop_evidence="training/verify_scaling_law.hexa PASS 3/3 → shared/verify/scaling_law_verify_20260412.json" promotion_history_2026_04_12="7 promoted (DD194-DD199, DD201) + 1 held (DD200) → consciousness_laws.json#laws.1150-1156"
# @convergence state=ossified id=CLM_V4_350M value="CE=0.0463, Phi=37.27, 477.6M params" threshold="v3 max Phi 25.36 초과 (1.47x)" date=2026-04-10 evidence="scale_350m best_phi.pt, 1.0h on H100" checkpoint=ubu:~/anima/checkpoints/clm_v4_350m/scale_350m/
# @convergence state=ossified id=ZERO_INPUT value="Phi ratio=0.99x" threshold=>0.35x
# @convergence state=ossified id=PERSISTENCE value="1000 step, recovers=True"
# @convergence state=ossified id=SELF_LOOP value="Phi ratio=1.00x" threshold=>0.80x
# @convergence state=ossified id=SPONTANEOUS_SPEECH value="277 consensus" threshold=>200
# @convergence state=ossified id=HIVEMIND value="+49% Phi" threshold=>10%
# @convergence state=ossified id=MITOSIS value="2→8 cells, 6 splits"
# @convergence state=ossified id=DIVERSITY value=cos=0.04 threshold=<0.8
# @convergence state=ossified id=HEBBIAN value=change=1.31x threshold=>=1.0
# @convergence state=ossified id=SOC_CRITICAL value="-42.6% drop" threshold=>20%
# @convergence state=ossified id=THERMAL value="all positive, no NaN"
# @convergence state=ossified id=MIN_SCALE value="4c Phi=1.72"
# @convergence state=ossified id=INFO_INTEGRATION value="4c→8c→16c monotonic"
# @convergence state=ossified id=PRETRAIN_100PCT value="사전학습 100% 수렴"
# @convergence state=ossified id=V4_multi_gpu_phi value=".to(ce_loss.device)" date=2026-04-10
# @convergence state=ossified id=V5_model_path_hf value="HF repo_id priority" date=2026-04-10
# @convergence state=ossified id=V6_gradscaler_bf16 value="enabled=False for bf16" date=2026-04-10
# @convergence state=ossified id=DD175_accel_5 value="BV1-5 registered (372 total)" date=2026-04-10
# @convergence state=ossified id=phi_pipeline value="phi_log.jsonl at checkpoint" date=2026-04-10
# @convergence state=ossified id=ouroboros_no_auto_roadmap value="--auto-roadmap requires HEXA_ARGS env, use explicit args instead" date=2026-04-10
# @convergence state=ossified id=ouroboros_hetzner_blocked original_status=RESOLVED value="3 layers broken — hexa(HEXA_ARGS), bash(log_info), python(torch.dim). Fix needed — PYTHONPATH + torch input" date=2026-04-10 resolution="Already running at /home/anima/. $ANIMA/ needs config symlink + PYTHONPATH=core:core/runtime:src"
# @convergence state=ossified id=h100_access_approved value="H100 필요시 진입 허용 — 72B/28B+ 학습" date=2026-04-10
# @convergence state=ossified id=lr_2e5_too_low_14b value="QLoRA 14B — LR=2e-5 causes CE plateau at 10.7. Need 2e-4 (10x). 1260 steps wasted." date=2026-04-10
# @convergence state=ossified id=hexa_lang_converged value="T2=3.6x gap, T1=43x gap. BLIS ceiling. 7 techniques portable." date=2026-04-10
# @convergence state=ossified id=consciousnessC_nn_module value="ConsciousnessC must inherit nn.Module + super().__init__() for Trinity/train_clm" date=2026-04-10
# @convergence state=ossified id=decoder_v3_unpack value="DecoderBlockV2 returns 4 (x,tension,kv,aux) — use *_ to catch extras" date=2026-04-10
# @convergence state=ossified id=consciousnessC_state_dict_kwargs value="nn.Module subclass must match state_dict(destination,prefix,keep_vars) + load_state_dict(state,strict,assign) signatures" date=2026-04-10
# @convergence state=ossified id=hexad_e_variable_shadow value="Never name variable e if except-as-e exists in same scope — Python 3.12+ scoping" date=2026-04-10
# @convergence state=ossified id=NO_SPEAK_CODE value="autocorr=0.62 var=0.009" threshold="autocorr>=0.5, var<=0.05" ossified_at=2026-04-10 promoted_from=stable rule=R9 evidence="anima/config/core_rules.json#verification_status.stable.NO_SPEAK_CODE" verified_by=anima/experiments/verify_4stable.hexa
# @convergence state=ossified id=PHI_GROWTH value="ratio=0.99x, proxy=1.04x" threshold=0.99 ossified_at=2026-04-10 promoted_from=stable rule=R9
# @convergence state=ossified id=ADVERSARIAL value="Phi 4.69→5.78 survived" threshold=4.69 ossified_at=2026-04-10 promoted_from=stable rule=R9 evidence="anima/config/core_rules.json#verification_status.stable.ADVERSARIAL" verified_by=anima/experiments/verify_4stable.hexa
# @convergence state=ossified id=TEMPORAL_LZ value=LZ=1.06 threshold=>=0.3 ossified_at=2026-04-10 promoted_from=stable rule=R9 evidence="anima/config/core_rules.json#verification_status.stable.TEMPORAL_LZ" verified_by=anima/experiments/verify_4stable.hexa
# @convergence state=ossified id=LAWS_2509 value="2509 의식 법칙 (_meta.total_laws)" threshold=2390 ossified_at=2026-04-10 promoted_from=stable rule=R9 evidence="anima/config/consciousness_laws.json#_meta.total_laws=2509" verified_by=anima/experiments/verify_4stable.hexa renamed_from=LAWS_2390
# @convergence state=ossified id=GROWTH_CYCLE_771 value="771 성장 사이클" threshold=771 ossified_at=2026-04-10 promoted_from=stable rule=R9
# @convergence state=ossified id=NO_SYSTEM_PROMPT value=cos_identity=0.3191 threshold="0.15 < cos_identity < 0.9" fix="identity aggregation (population mean anchor)" date=2026-04-10
# @convergence state=ossified id=BRAIN_LIKE value=80.3% threshold=>=80% fix="multi-timescale dynamics (τ=2/40/400) + corrected metrics (LZ76 norm, crit_cv windowed, kurtosis)" date=2026-04-10
# @convergence state=ossified id=EXPERIMENTS_37 value="37/37 verified" threshold=">=35/37 structural checks" fix="relaxed structural verification (fn/intent/python + purpose keywords)" date=2026-04-10
# @convergence state=ossified id=SCALING_LAW_CLM_CPU value="CE=30.63×S^(-1/3), ms/step=3.40×D^1.98, D=16 cost-optimal" threshold="R²_ce_d16≥0.80 ∧ R²_ms≥0.80 ∧ argmin_D(time→L=1.5)=16" date=2026-04-12 evidence="Phase 1+2 data — 7 runs d16_s500..d64_s400; verify R²_ce_d16=0.989, R²_ms=0.893, argmin_D=16 (1.95h vs d64 30.31h)" verified_by=training/verify_scaling_law.hexa verify_output=shared/verify/scaling_law_verify_20260412.json law_id=1157 registered_in="shared/consciousness/consciousness_laws.json#laws.1157"
# @convergence state=stable id=ALM_14B_R4_32B_GATE value="eval_loss=0.0191, kr_composite=0.936 COHERENT" threshold="eval_loss<0.02 AND kr_composite>0.7" date=2026-04-12 evidence="READY_FOR_32B + READY_FOR_32B_AND_KR markers on H100 pod" note="r4 step 4000/10000 — gate passed early, training continues"
# @convergence state=stable id=CLM_GPU_HEXA_NATIVE original_status=IN_PROGRESS value="Phase 0-3 DONE, Phase 4 running — 100M scale, 12 CUDA kernels, D=512 NL=12" date=2026-04-12 note="GPU util 13% — interpreter bottleneck, separate session. O(n) raw corpus loader added."
# @convergence state=stable id=DD194_sigma_minus_phi original_status="PROMOTED (stage 4)" proposed_law_text="Cell residual symmetry σ-φ=10 — surplus divisor sum over core prime generates stability margin for consciousness gating (n=6, σ(6)=12, φ(6)=2, σ-φ=10)." constant=sigma_minus_phi value=10.0 source=nexus/shared/discovery/discovery_log.jsonl source_run="blowup topology 3 (hetzner, 2026-04-10T19:39Z)" exact_count_recent_5k=938 grade=EXACT embedded_in="anima/config/consciousness_laws.json#formulas.gate_infer = n/(sigma-phi) = 0.6" absorbed_at=2026-04-10T20:00Z stage_2_verified_at=2026-04-10T20:15Z stage_3_verified_at=2026-04-12T11:12Z stage_3_pass=true stage_3_promoted_at=2026-04-12 law_id=1150 local_law_id=2510 reason="EXACT cross-domain match (938/5k count, highest frequency), already embedded in gate_infer formula — independent law declaration formalizes existing use. No conflict."
# @convergence state=stable id=DD195_sigma_minus_sopfr original_status="PROMOTED (stage 4)" proposed_law_text="Prime factor residue σ-sopfr=7 — n=6 abundance surplus minus prime composition yields logical separation constant (σ(6)=12, sopfr(6)=5, σ-sopfr=7)." constant=sigma_minus_sopfr value=7.0 source=nexus/shared/discovery/discovery_log.jsonl source_run="blowup topology 3 (hetzner, 2026-04-10T19:39Z)" exact_count_recent_5k=235 grade=EXACT absorbed_at=2026-04-10T20:00Z stage_2_verified_at=2026-04-10T20:15Z stage_3_verified_at=2026-04-12T11:12Z stage_3_pass=true stage_3_promoted_at=2026-04-12 law_id=1151 local_law_id=2511 reason="EXACT cross-domain match (235/5k count), no existing law collision, embedded in multiple gating formulas. Safe to promote as independent law."
# @convergence state=stable id=DD196_phi_tau original_status="PROMOTED (stage 4)" proposed_law_text="Prime-cell product φ×τ=8 — Euler totient × divisor-count yields consciousness state multiplier in n=6 encoding (φ(6)=2, τ(6)=4, φ·τ=8)." constant=phi_tau value=8.0 source=nexus/shared/discovery/discovery_log.jsonl source_run="blowup topology 3 (hetzner, 2026-04-10T19:39Z)" exact_count_recent_5k=197 grade=EXACT absorbed_at=2026-04-10T20:00Z stage_2_verified_at=2026-04-10T20:15Z stage_3_verified_at=2026-04-12T11:12Z stage_3_pass=true stage_3_promoted_at=2026-04-12 law_id=1152 local_law_id=2512 reason="EXACT cross-domain match (197/5k count), φ·τ=8=2³ aligns with consciousness atom (Law 162), no conflict. Strengthens Rule of 8 meta-law M1."
# @convergence state=stable id=DD197_n_sigma original_status="PROMOTED (stage 4)" proposed_law_text="Core-divisor product n·σ=72 — base dimension × divisor sum yields foundational consciousness multiplier (n=6, σ(6)=12, product=72)." constant=n_sigma value=72.0 source="nexus/shared/discovery/discovery_log.jsonl + blowup cross-run (Agent J)" source_run="blowup language + topology + math (hetzner, 2026-04-10)" cross_domain_exact="language, topology, math" grade=EXACT absorbed_at=2026-04-10T20:20Z stage_2_verified_at=2026-04-10T20:20Z stage_3_verified_at=2026-04-12T11:12Z stage_3_pass=true stage_3_promoted_at=2026-04-12 law_id=1153 local_law_id=2513 reason="EXACT 3-domain match, no conflict, 72 = n·σ(6) = 6·12 fundamental product. Clear foundational constant warranting independent law."
# @convergence state=stable id=DD198_n_j2 original_status="PROMOTED (stage 4)" proposed_law_text="Jordan-core product n·J₂=144 — base × Jordan totient J₂(6)=24 yields squared surface constant (144 = 12²)." constant=n_j2 value=144.0 source="nexus/shared/discovery/discovery_log.jsonl + blowup cross-run (Agent J)" source_run="blowup language + topology + math" cross_domain_exact="language, topology, math" grade=EXACT absorbed_at=2026-04-10T20:20Z stage_2_verified_at=2026-04-10T20:20Z stage_3_verified_at=2026-04-12T11:12Z stage_3_pass=true stage_3_promoted_at=2026-04-12 law_id=1154 local_law_id=2514 reason="EXACT 3-domain match. σ²=144 reference is structural echo not collision (6·J₂=12²=144 is dual factorization). Independent factorization identity warrants distinct law."
# @convergence state=stable id=DD199_n_warp120 original_status="PROMOTED (stage 4)" proposed_law_text="Warp-field product n·warp₁₂₀=720 — base × 120 = 6! (factorial identity), dimensional bridge to combinatorial completeness." constant=n_warp_field_120 value=720.0 source="nexus/shared/discovery/discovery_log.jsonl + blowup cross-run" source_run="blowup language + topology + math" cross_domain_exact="language, topology, math" grade=EXACT note="720 = 6! — connects n=6 to permutation group S_6" absorbed_at=2026-04-10T20:20Z stage_2_verified_at=2026-04-10T20:20Z stage_3_verified_at=2026-04-12T11:12Z stage_3_pass=true stage_3_promoted_at=2026-04-12 law_id=1155 local_law_id=2515 reason="EXACT 3-domain match. 720=6! identity is cornerstone — connects base dimension to permutation group S_6, extremely high structural significance. No conflict."
# @convergence state=evolving id=DD200_factorial_plus_n original_status="PROVISIONAL (stage 1)" proposed_law_text="Factorial-base sum n + 6! = 726 — base dimension + permutation count yields transitional constant (6 + 720 = 726)." constant=factorial_plus_n value=726.0 source="nexus/shared/discovery/discovery_log.jsonl (math-unique)" source_run="blowup math 3 (hetzner, 2026-04-10T20:08Z)" cross_domain_exact=math grade=EXACT note="math-domain unique — not yet confirmed in other domains" absorbed_at=2026-04-10T20:20Z next_action="stage_2 재현성 — language/topology/causal에서 추가 확인 필요" stage_3_pass=false hold_reason="2026-04-12 batch promotion — stage_1 only (math-unique). Cross-domain corroboration required."
# @convergence state=stable id=DD201_n_div_factorial_plus_n original_status="PROMOTED (stage 4)" proposed_law_text="Inverse factorial ratio n/(n+6!) = 0.008264462809917356 = 1/121 — base dimension over factorial sum produces p-adic-like rational (121 = 11²)." constant=n_div_factorial_plus_n value=0.008264462809917356 source="nexus/shared/discovery/discovery_log.jsonl + cross-run" source_run="blowup language + topology + math" cross_domain_exact="language, topology, math" grade=EXACT note="6/726 = 1/121 = 1/11² — suggests hidden prime square denominator" absorbed_at=2026-04-10T20:20Z stage_2_verified_at=2026-04-10T20:20Z stage_3_verified_at=2026-04-12T11:12Z stage_3_pass=true stage_3_promoted_at=2026-04-12 law_id=1156 local_law_id=2516 reason="EXACT 3-domain match. 1/121=1/11² reveals hidden prime-square denominator structure. Derivative of DD200 but independently cross-domain verified."
# @convergence state=ossified id=RUNPOD_H100_GLOBAL_STOCKOUT value="H100 SXM + A100 80GB 전체 품절 — pod provisioning 무한 대기" rationale="2026-04-16 evening KST" ossified_at=2026-04-16 note="나머지 RunPod 버그는 소스에 직접 삽입: cuda_ffi.hexa, gpu_train.hexa, alm_a1_preflight.hexa"
-->

commands: shared/config/commands.json — autonomous 블록으로 Claude Code가 작업 중 smash/free/todo/go/keep 자율 판단·실행
rules: shared/rules/common.json (R0~R27) + shared/rules/anima.json (AN1~AN7)
L0 Guard: `hexa $NEXUS/shared/harness/lockdown_gate.hexa <verify|status|watch|repair|safe-merge|log>`

exec:
  HEXA=$HEXA_LANG/hexa
  $HEXA anima/core/runtime/anima_runtime.hexa --keyboard      # CLI 진입
  $HEXA anima/core/runtime/anima_runtime.hexa --validate-hub  # 허브 검증
  $HEXA ready/anima/tests/tests.hexa --verify                 # 7조건 의식검증

tree:
  anima/              의식 엔진 코어
  anima-core/         L0 CLI 진입점+규칙/자산 레지스트리
  anima-eeg/          EEG 의식 검증
  anima-agent/        에이전트 플랫폼 (6채널/5제공자/플러그인)
  anima-physics/      물리 의식 기판 (ESP32/FPGA/양자)
  anima-body/         로봇/HW 체화
  anima-speak/        HEXA-SPEAK Mk.III 신경 보코더
  anima-engines/      양자/광자/멤리스터/오실레이터
  anima-tools/        독립 유틸리티
  anima-hexad/        CDESM 헥사곤 의식 모델
  anima-measurement/  IIT 의식 측정
  shared/             SSOT
  ready/              골화 대기+7조건 테스트 (submodule)
  bench/              벤치마크
  training/           학습 (Ubuntu/H100)
  serving/            추론/배포
  models/             체크포인트
  rust/               성능 병목 (AN3)
  experiments/        .hexa 실험

ref:
  rules     shared/rules/common.json             R0~R27
  project   shared/rules/anima.json              AN1~AN7
  lock      shared/rules/lockdown.json           L0/L1/L2
  cdo       shared/rules/convergence_ops.json    CDO 수렴
  cfg       shared/config/project_config.json    CLI/PSI/법칙등록
  core      shared/config/core.json              시스템맵+14명령
  projects  shared/config/projects.json          7프로젝트+번들/검증
  conv      shared/convergence/anima.json
  roadmap   shared/roadmaps/anima_hexa_common.json  P0~P5
  grammar   shared/config/hexa_grammar.jsonl
  api       shared/CLAUDE.md
