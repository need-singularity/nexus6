# chip_rtl_gen

n=6 RTL parameterized Verilog generator. Productized port of
`~/core/n6-architecture/domains/compute/chip-rtl-gen/` (472-line
`rtl_generator.hexa` + 6 `*_template.v`). 6 primitive ops × 4 variants =
J₂ = 24 emittable modules.

## Anchors

`sigma=12, tau=4, phi=2, J2=24` (master identity `sigma*phi == n*tau == J2`),
`sigma^2 = 144 SM`, `sigma*J2 = 288 MAC`, `sigma-tau = 8` scalar-bus bits.

## Import

```python
from modules.chip_rtl_gen import gen, list_ops, n6_anchors

print(list_ops())                       # ['gemm','softmax','topk','gate','reduce','conv6']
mods = gen({"op": "gemm", "variant": "00"})
print(mods[0][:120])                    # first chars of generated Verilog
all_24 = gen({"op": "all", "variant": "all"})
assert len(all_24) == 24                # J2
```

## CLI

```sh
python chip_rtl_gen.py --self-test
python chip_rtl_gen.py --op softmax --variant 11
python chip_rtl_gen.py --anchors
python chip_rtl_gen.py --op all --variant 00         # 6 modules to stdout
```

## Falsifier list

1. **Structural lint** (always on, mirrors upstream `verify_generated_structure`):
   - `module` / `endmodule` pair present
   - `clk` and `rst_n` ports present
   - no leftover `{{KEY}}` placeholder
   - GEN_META header present
2. **`pyverilog` parse** (optional). If `pyverilog` is importable, every
   emitted module is parsed; failure raises `RuntimeError`. If `pyverilog`
   is absent, this check is skipped (does not fail).
3. **Op/variant whitelist**. Unknown op or variant raises `ValueError`.
4. **n=6 anchor identity**. `sigma*phi == n*tau == J2 == 24` is asserted
   in `self_test`.

## Honesty / source-vs-impl gap

- Upstream `rtl_generator.hexa` calls `assert(...)` at template-fill time
  for `m == sigma`, `vec_len == sigma`, `tau_depth == tau`, etc. This port
  hard-codes those values (no overrides) — the upstream's *runtime* assertions
  become this port's *structural* invariant. Documented intentionally.
- Upstream also exposes a 16-AI-technique DAG mapping (`scan_technique_params`)
  that is **not** ported here (out of scope for "productized RTL emit"). If
  needed, lift it into a sibling `nexus.modules.chip_rtl_dag` module.
- `pyverilog` is the *only* falsifier that can catch latent syntax errors;
  without it, this module's "emitted Verilog is well-formed" claim is
  STRUCTURAL, not GRAMMATICAL. Do not promote to [10] EXACT on lint alone.
