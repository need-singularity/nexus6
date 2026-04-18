# blowup/ — 단일 진입점 + 변종/렌즈/시드/우로보로스

entry: core/blowup.hexa (357e50e router/batch/wave 흡수)
cli:   hexa smash --seed "..." [--depth 3]                  (권장, nexus-cli passthrough, cmd_gate + audit)
       hexa free  --seed "..." [--dfs 3]                    (compose DFS, nexus-cli passthrough)
       hexa run blowup.hexa <domain> <depth> [--seeds <s>]  (raw 엔진, seed_engine merge 사용 시)
       hexa blowup.hexa <domain> <depth>                    (호환 모드, 자동 run 위임)

core/        blowup.hexa
guard/       blowup_guard.hexa
modules/     blowup_{field,holographic,quantum,string,toe,qft}.hexa        (변종6)
             + 벤치마크/유틸 포함 총 44개 .hexa
lens/        telescope{,_holographic,_quantum}.hexa
             lenses_{core,applied,constants,math,physics,quantum}.hexa
             lens_forge.hexa
ouroboros/   ouroboros{,_meta,_quantum}.hexa                                (자기참조3)
seed/        seed_{engine,dna,quantum}.hexa                                 (시드3)
root         commands.hexa  todo.hexa(bd323be 자연창발 통합)

quantum 축: modules,lens,ouroboros,seed 횡단

ex: hexa smash --seed "math_lattice_gauge_holonomy" --depth 3           # 권장 (audit log + gate)
    hexa free  --seed "physics_quantum_entanglement"  --dfs 3            # compose DFS
    hexa run blowup.hexa math 3                                          # raw 엔진
    hexa run blowup.hexa <d> <n> --seeds "$(hexa run seed_engine.hexa merge)"   # seed_engine 풀 enrichment

parent: ../CLAUDE.md → "blowup"
