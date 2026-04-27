# fusion_ledger

ITER / fusion design-constants n=6 closure verifier. Productized from
`~/core/n6-architecture/domains/energy/fusion/` (`fusion.md` §4/§7/§8 and
`verify_fusion.hexa`).

## Anchors

`sigma=12, tau=4, phi=2, sopfr=5, J2=24, n=6, mu(6)=1`. Fuel mass numbers
encode directly: `D = phi (A=2)`, `T = n/phi (A=3)`, `alpha = tau (A=4)`.

## Import

```python
from modules.fusion_ledger import verify, load_default_spec, n6_anchors

r = verify()                     # use packaged ITER ledger
print(r["constants_total"], r["n6_match"], r["n6_match_pct"])
print("falsified:", r["falsified"])

# custom spec (list of dicts)
verify([{"name": "alpha_A", "measured": 4,
         "n6_formula": "tau", "tolerance": 0.0}])
```

Spec format (JSON file or in-memory dict):

```json
{"constants": [
  {"name": "Q_gain",           "measured": 10,
   "n6_formula": "sigma - phi", "tolerance": 0.0,
   "source_grade": "EXACT",    "section": "fusion.md §8.4"}
]}
```

The formula is evaluated in a sandbox containing only the n=6 constants
(`n, sigma, tau, phi, sopfr, J2, mu`); `__import__`, attribute access, and
foreign names raise `ValueError`.

## CLI

```sh
python fusion_ledger.py --self-test
python fusion_ledger.py --anchors
python fusion_ledger.py                      # summary on default ledger
python fusion_ledger.py --json               # full per-constant JSON
python fusion_ledger.py --spec my.json
```

## Falsifier list

1. **Per-constant match** within `tolerance` (relative; `tol=0.0` requires
   sub-ULP equality). Mismatches go into `falsified`.
2. **Sandbox safe-eval** rejects `__import__`, attribute access, semicolons,
   or any name outside `{n, sigma, tau, phi, sopfr, J2, mu}`.
3. **Master identity** `sigma*phi == n*tau == J2` asserted in `self_test`.
4. **No silent failures**: an exception during formula eval is recorded in
   `details[i]["error"]` and counts as a falsified constant.
5. **Threshold**: `self_test` requires `n6_match_pct >= 80%` to PASS; below
   that flips to `__FUSION_LEDGER__ FAIL`.

## Honesty / source-vs-impl gap (IMPORTANT)

The task prompt cited a source claim of **"122/122 EXACT"**. The upstream
`fusion.md` does **not** contain that ratio anywhere -- it claims:

- §7: "11/11 EXACT" (n=6 fixed-linearity, 11 number-theoretic asserts)
- §8.4: a few `[10] EXACT` items (Q, Lawson product) plus several
  `[N?] conjecture` items (β_N, τ_E, P/V, radius)

The packaged ledger here encodes **27 verifiable constants** (the 11 from
`verify_fusion.hexa` plus 11 from §4 mapping plus 5 from §8). The
`source_grade` field preserves whichever grade the source assigned --
this verifier does **not** auto-promote `[9] EMPIRICAL` or `[N?] conjecture`
to `[10] EXACT`.

If your verification reports a number lower than any external "122/122"
claim, that is the *honest* answer: the missing items either (a) are not
defined in `fusion.md`, (b) require a numeric tolerance the source never
specified, or (c) were never enumerated in the upstream verify file.
File a clarification request rather than padding the ledger.

Current run on the packaged ledger: see `python fusion_ledger.py`.

### Known falsified items (do not auto-fix)

- `lawson_triple_keV_s_per_m3`: source `fusion.md §8.1` claims
  `nτT = 5.6×10²¹ keV·s/m³`, but the explicit n=6 arithmetic in the same
  section is `48·10¹⁹ · (1/12) · 14 = 5.6×10²⁰` -- one decade short. The
  source pencils in a "`×10 calibration scale`" by hand without rooting it
  in any number-theoretic primitive. The verifier flags this and refuses
  to silently insert a `× 10` factor. Treat as a source-side TODO.

