# discovery/ — 발견 허브 (흡수 후 단일 소스)

core:
  reality_map.json             SSOT 실재지도
  reality_map_live.json        실시간
  reality_map_v8.3 / zscore_v9.3{,_revised}
  reality_map_3d.html          시각화
  reality_map.patch.L*.jsonl   레벨별 패치 (10)
  reality_map_{extension_t8,t12_expansion}.jsonl
  _v94_new_nodes.json

graph/log:
  → shared/n6/atlas.n6 (discovery_graph + discovery_log + growth_bus + theory_registry + verified_constants 통합)
  ouroboros_log.json
  composed_pipelines.jsonl
  domain_seeds.jsonl     module_candidates.jsonl
  next_directions.jsonl  self_improve_log.jsonl

reports:
  breakthroughs.json sedi-grades.json closure_quality_report.json
  forge_result.json roadmap.json
  map_explosion_plan.{json,md} map_dimension_unfold.md
  auto_discovery_20cycles.json
  unfold_{base,ext}.jsonl math_atlas.json

absorbed:
  acceleration/  acceleration_{flow,hypotheses}, explosive_growth_prompts.md
  alien/         alien_index_{distribution,frontier,records}
  growth/        airgenome_gates, growth_strategies, growth-registry
  monte_carlo/   v6 engine + rerun/result
  singularity/   singularity_recursion_*.md (13)
  papers/        paper_candidates, nanobot, pages-deploy-verify
  cycle/         특이점 5단계 — 하위 CLAUDE.md

parent: ../CLAUDE.md → "discovery"
