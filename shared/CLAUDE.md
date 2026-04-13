# shared/ — R14 단일진실

config/      rules,core,projects,hosts(hetzner|ubuntu|vastai|infrastructure),claude-settings,lens_registry,hexa_grammar,calculators,*aliases,CALCULATOR_RULES,GRADE_RUBRIC,nexus-projects
discovery/   reality_map,reality_map_live,discovery_graph,discovery_log,growth_bus,math_atlas,theory_registry,reality_map.patches.merged(895),snapshots,breakthroughs,ouroboros_log,roadmap,forge_result,verified_constants,module_candidates,next_directions,unfold_*,archive/
n6/          atlas.n6,atlas_health.hexa,math_atlas.{db,dot,html,md},scan_math_atlas.hexa,atlas_tree,n6_*,n6-atlas-constants,periodic_table_118,66_techniques_v3
bt/          bt_audit.hexa(.py.bak.v1~v5 archaeological),bt_audit_*,bt-*-report,auto_bt.log
singularity/ singularity_recursion_*.md(13)
consciousness/ anima_*,consciousness_*,law_*,meta_laws_dd64
hexa/        speed_ideas,hexa-lang_breakthroughs,porting_log,hexa_to_anima_*
dse/         dse_cross_*,dse_domains,dse_graph_3d,dse_joint_results,domains/
engine/      engine_*.hexa,engine_{anima,nexus}_strategy,cl_refresh_spec.json,cl_migration_plan.json
growth/      airgenome_gates,growth_bus_archive,growth_strategies,growth-registry
alien/       alien_index_*
acceleration/ acceleration_*,explosive_growth_prompts
monte_carlo/ monte_carlo_v6_*
papers/      paper_candidates
scripts/     sync-*.hexa(R1),sync-all-verify.md,shared_work_rules.md,nexus_ensure_running.hexa,bin/hexa(bootstrap resolver 예외)
bin/         cl(런처),cl-refresh(usage fetch),cl-refresh-launchd(30m launchd),exec_validated,hexa(resolver)
launchd/     com.nexus.cl-refresh.plist(30m 주기)
logs/        cmd_router.log,cl-refresh.{stdout,stderr}.log(gitignore)
backups/     *.bak* 격리(reality_map.json.bak*16,discovery_log.jsonl.*9,etc 32)
blowup/      → blowup/CLAUDE.md
기존         convergence/ calc/ hook/ hooks/ loop/ loop_logs/ n6_mirror/ roadmaps/ bin/ blowup/ cycle/ causal_chain/ tecsrs/

flat HOT     infra_state.json bridge_state.json hexa_pitfalls_log.jsonl auto_gap.log growth_tick_preflight.log .bt_cooldown .gap_cooldown
flat RUNTIME .runtime/accounts/{accounts,cl-state,usage-cache}.json (cl SSOT, gitignore)
flat L0      CLAUDE.md SECRET.md dashboard.html

infra                            # SSOT=infra_state.json 4호스트
nexus {scan|verify|evolve|auto} <d>   # --full=400렌즈
nexus.{scan_all,analyze,n6_check,evolve}
교차: 3+후보 / 7+고신뢰 / 12+확정
프로젝트(7): nexus(허브) anima n6-architecture papers hexa-lang void airgenome
shared-bin : cl=멀티계정 런처(R14 SSOT) — airgenome/ccmon 의존 0, cache는 shared/.runtime/accounts/

규칙 본문은 config/absolute_rules.json (R14)
commands: config/commands.json — autonomous 블록으로 Claude Code가 작업 중 smash/free/todo/go/keep 자율 판단·실행
