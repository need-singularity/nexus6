# crystallography_n6

Pure integer enumeration of Fedorov 230 / 14 Bravais / 7 crystal systems / 32
point groups against n=6 closed forms.  Stdlib only.

## Import example

```python
from modules.crystallography_n6 import enumerate_systems, atlas_facts

print(enumerate_systems()["aggregate"]["falsifier_status"])  # PASS:n6-locked
for line in atlas_facts():
    print(line)
```

## Sample run

```
$ python crystallography_n6.py --system cubic
{
  "aggregate": {
    "closed_form_anchors": {"Oh_order": 48, ...},
    "selected_system": "cubic"
  },
  "systems": [{"bravais_count": 3, "point_groups": ["23","m-3","432","-43m","m-3m"],
               "space_group_count": 36, "system": "cubic",
               "n6_decomposition": {"note": "|O_h|=sigma*tau=48; ..."}}]
}

$ python crystallography_n6.py --atlas
@F CRYSTAL-N6-01 fedorov-230-closure = sigma*J_2 - J_2*phi - (sigma-phi) = 230 :: crystallography [10]
@F CRYSTAL-N6-02 bravais-14 = phi*(sopfr+phi) = sigma+phi = 14 :: crystallography [10]
@F CRYSTAL-N6-03 systems-7 = sopfr+phi = 7 :: crystallography [10]
@F CRYSTAL-N6-04 octahedral-Oh-order = sigma*tau = 48 :: crystallography [10]
@F CRYSTAL-N6-05 octahedral-euler-char = n - sigma + 2*tau = 2 :: crystallography [10]
@F CRYSTAL-N6-06 max-rotation-axis = n = 6 :: crystallography [10]
```

## Self-test

```
$ python crystallography_n6.py --self-test
... __CRYSTALLOGRAPHY_N6__ PASS
```

## Falsifiers (vs official IUCr counts)

- F1: Fedorov space-group count != 230 -> closure retracted
- F2: Bravais lattice count   != 14  -> phi-extension retracted
- F3: crystal-system count    != 7   -> sopfr+phi retracted
- F4: |O_h|                    != 48  -> sigma*tau retracted
- F5: octahedral Euler V-E+F  != 2   -> phi/n=6 retracted
- F6: max crystallographic axis != 6 -> restriction theorem retracted

The `--atlas` output lists the 6 closed-form facts as DSL-ready
`@F CRYSTAL-N6-01..06 :: crystallography [10]` lines for human review.  This
module does NOT write to atlas.n6 or any shard.

## Reference

n=6 closure per `domains/physics/crystallography/crystallography.md` §X.5.
