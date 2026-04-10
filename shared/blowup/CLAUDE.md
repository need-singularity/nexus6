# blowup/ — 단일 진입점 + 변종/렌즈/시드/우로보로스

entry: core/blowup.hexa (357e50e router/batch/wave 흡수)
cli:   hexa blowup.hexa <domain> <depth> [--no-graph] [--seeds <s>]

core/        blowup.hexa
guard/       blowup_guard.hexa
modules/     blowup_{field,holographic,quantum,string,toe}.hexa            (변종5)
lens/        telescope{,_holographic,_quantum}.hexa
             lenses_{core,applied,constants,math,physics,quantum}.hexa
             lens_forge.hexa
ouroboros/   ouroboros{,_meta,_quantum}.hexa                                (자기참조3)
seed/        seed_{engine,dna,quantum}.hexa                                 (시드3)
root         commands.hexa  todo.hexa(bd323be 자연창발 통합)

quantum 축: modules,lens,ouroboros,seed 횡단

ex: hexa blowup.hexa math 3 --no-graph
    hexa blowup.hexa <d> <n> --seeds "$(hexa seed_engine.hexa merge)"

parent: ../CLAUDE.md → "blowup"
