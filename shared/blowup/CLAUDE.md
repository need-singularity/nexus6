# blowup/ — 단일 진입점 + 변종/렌즈/시드/우로보로스

> 진입점: `core/blowup.hexa` (router/batch/wave 흡수, 357e50e)
> `hexa blowup.hexa <domain> <depth> [--no-graph] [--seeds <s>]`

## 트리

| 폴더 | 내용 |
|---|---|
| `core/` | `blowup.hexa` — 단일 진입점 |
| `guard/` | `blowup_guard.hexa` — 안전 가드 |
| `modules/` | `blowup_{field,holographic,quantum,string,toe}.hexa` — 변종 5 |
| `lens/` | `telescope{,_holographic,_quantum}.hexa` + `lenses_{core,applied,constants,math,physics,quantum}.hexa` + `lens_forge.hexa` |
| `ouroboros/` | `ouroboros{,_meta,_quantum}.hexa` — 자기참조 루프 3 |
| `seed/` | `seed_{engine,dna,quantum}.hexa` — 시드 3 |
| (root) | `commands.hexa`, `todo.hexa` (bd323be: todo.hexa 자연창발 통합) |

`quantum` 변종이 modules/lens/ouroboros/seed 모두에 존재 — quantum 축이 횡단 차원.

## 사용

```bash
hexa blowup.hexa math 3 --no-graph
hexa blowup.hexa <d> <n> --seeds "$(hexa seed_engine.hexa merge)"
```
