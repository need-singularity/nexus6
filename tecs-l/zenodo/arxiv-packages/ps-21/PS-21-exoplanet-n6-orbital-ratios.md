# Orbital Period Ratios in Multi-Planet Systems and the Arithmetic of the Perfect Number n=6

**Authors:** SEDI Project (TECS-L)
**Date:** 2026-03-28
**Keywords:** exoplanets, orbital resonances, period ratios, perfect numbers, mean-motion resonance, HD 110067, TRAPPIST-1
**License:** CC-BY-4.0

## Abstract

We scan 298 multi-planet systems from the NASA Exoplanet Archive for
pairwise orbital period ratios matching the arithmetic functions of the
perfect number n=6. Using a 2% tolerance, 82 systems (27.5%) contain at
least one matching ratio. This detection rate is consistent with, and
actually below, the null expectation from Monte Carlo simulations of
resonant chains (where ~67-89% of systems with 3-6 planets produce
accidental matches). The finding of individual matches is therefore not
statistically significant. However, the six-planet system HD 110067
presents a notable structure: its consecutive period ratios follow the
pattern (3/2, 3/2, 3/2, 4/3, 4/3), whose product is exactly
(3/2)^3 x (4/3)^2 = 6 = n. This complete arithmetic ladder, spanning
all five consecutive ratios with sub-0.2% precision throughout, occurs
in ~1.2% of random resonant six-planet configurations (p ~ 0.012).

## 1. Introduction

### 1.1 Orbital Resonances

Mean-motion resonances (MMRs) are a well-understood feature of
planetary dynamics. When two planets orbit with a period ratio close to
a ratio of small integers (2:1, 3:2, 4:3, 5:4, ...), gravitational
interactions can lock the orbits into a stable resonant configuration.
Resonant chains, where three or more consecutive planet pairs occupy
MMRs, are observed in systems such as TRAPPIST-1, HD 110067, Kepler-223,
and TOI-178.

These resonances arise from convergent disk migration during planet
formation and are maintained by tidal dissipation. The prevalence of
small-integer ratios in multi-planet systems is therefore a consequence
of orbital mechanics, not numerology.

### 1.2 Arithmetic Functions of n=6

The number 6 is the smallest perfect number (6 = 1 + 2 + 3). Its
arithmetic functions are:

```
  n = 6
  sigma(6) = 1 + 2 + 3 + 6 = 12    (sum of divisors)
  tau(6)   = 4                       (number of divisors: 1, 2, 3, 6)
  phi(6)   = 2                       (Euler totient)

  Derived ratios:
    n/tau       = 6/4 = 3/2          (the dominant MMR ratio)
    tau/sigma_over_tau = 4/3         (the second-most common MMR ratio)
    sigma/tau   = 12/4 = 3
    phi         = 2                  (the 2:1 resonance)
```

The ratios 3/2, 4/3, 2, 3, 4, and 6 are all expressible as ratios of
the divisors of 6 or of its standard arithmetic functions. This is a
mathematical tautology: the divisors of 6 are {1, 2, 3, 6}, and ratios
of small integers necessarily produce small-integer ratios. The question
is whether planetary systems show these specific ratios with unusual
frequency, precision, or completeness.

### 1.3 Honest Framing

We emphasize at the outset: **the individual detection of 3:2 and 4:3
period ratios in planetary systems is completely expected from orbital
mechanics.** These are the most common mean-motion resonances. Finding
them is not evidence of any hidden structure. The only potentially
notable finding in this work is the completeness and precision of the
ratio ladder in HD 110067, where all five consecutive pairs participate
and the end-to-end product equals exactly n=6.

## 2. Methods

### 2.1 Data Source

All planetary data were retrieved from the NASA Exoplanet Archive
(https://exoplanetarchive.ipac.caltech.edu/) via the TAP service.
We queried the Planetary Systems table (ps) for confirmed planets with
measured orbital periods (pl_orbper IS NOT NULL, default_flag = 1) in
systems with three or more planets (sy_pnum >= 3).

### 2.2 Target Ratios

For each system with N planets, we compute all N(N-1)/2 pairwise
period ratios P_j/P_i (where P_j > P_i). Each ratio is compared
against the following targets derived from n=6 arithmetic:

| Target | Value | Arithmetic Source |
|--------|-------|-------------------|
| 4/3 | 1.3333 | tau(6) / sigma_over_tau |
| 3/2 | 1.5000 | n / tau = 6/4 |
| phi(6) | 2.0000 | Euler totient |
| sigma/tau | 3.0000 | 12/4 |
| tau(6) | 4.0000 | number of divisors |
| n | 6.0000 | the perfect number itself |
| sigma(6) | 12.000 | sum of divisors |

### 2.3 Tolerance

A match is recorded when |R_obs - R_target| / R_target < 0.02 (2%).
This tolerance is chosen to capture near-resonant systems where
libration amplitudes or tidal evolution have shifted periods slightly
off exact commensurability.

### 2.4 Null Model (Monte Carlo)

To estimate the false-positive rate, we generate synthetic planetary
systems:

**Model A (log-uniform):** N planet periods drawn independently from
a log-uniform distribution over [1, 1000] days.

**Model B (resonant chain):** An inner planet period drawn uniformly
from [1, 50] days; each subsequent planet's period is drawn as the
previous period times a random factor in [1.2, 3.0], simulating the
range of observed MMR ratios.

For each model, 200,000 trials were run per planet count (N=3 through
N=7), and the fraction of trials producing at least one n=6 target
match was recorded.

```
  Monte Carlo Results (200,000 trials per configuration)

  Model A (log-uniform periods):
    N=3:  19.0% with >=1 match    avg matches: 0.20
    N=4:  34.4% with >=1 match    avg matches: 0.40
    N=5:  50.7% with >=1 match    avg matches: 0.67
    N=6:  65.7% with >=1 match    avg matches: 1.01
    N=7:  77.7% with >=1 match    avg matches: 1.42

  Model B (resonant chains, ratio 1.2-3.0x):
    N=3:  47.1% with >=1 match    avg matches: 0.82
    N=4:  67.0% with >=1 match    avg matches: 1.44
    N=5:  81.1% with >=1 match    avg matches: 2.14
    N=6:  89.1% with >=1 match    avg matches: 2.86
    N=7:  93.8% with >=1 match    avg matches: 3.58
```

**Conclusion from null model:** For resonant-chain systems with 3+
planets, a 47-94% detection rate of n=6 ratio matches is expected by
chance alone. Our observed rate of 27.5% is actually **below** the null
expectation, likely because many real multi-planet systems are not in
resonant chains.

## 3. Results

### 3.1 Survey Summary

```
  Total multi-planet systems scanned:   298
  Systems with >=1 n=6 ratio match:      82  (27.5%)
  Systems with >=5 matches:              ~15
  Systems with >=9 matches:                3
```

### 3.2 Top Systems by Match Count

| Rank | System | Planets | Matches | Best Precision |
|------|--------|---------|---------|----------------|
| 1 | TRAPPIST-1 | 7 | 12 | b-e: tau=4 (0.93%) |
| 2 | HD 110067 | 6 | 9 | e-f: 4/3 (0.003%) |
| 3 | TOI-1136 | 6 | 5 | b-d: sigma/tau=3 (0.01%) |
| 4 | Kepler-80 | 6 | 5 | -- |
| 5 | GJ 876 | 4 | 4 | -- |
| 6 | Kepler-9 | 3 | 3 | -- |
| 7 | Kepler-235 | 4 | 3 | -- |

Note: match counts depend on the specific target set and whether
overlapping arithmetic expressions (e.g., n/tau = 3/2 counted once or
as two separate patterns) are de-duplicated. The counts above use the
SEDI scanning pipeline, which includes extended targets and both direct
and inverse ratio checks.

### 3.3 Ratio Matrix: HD 110067

Periods (days): b=9.114, c=13.674, d=20.520, e=30.793, f=41.059, g=54.770

```
  P(row) / P(col)
             b        c        d        e        f        g
  b          ---    0.6665   0.4441   0.2960   0.2220   0.1664
  c       1.5003      ---   0.6664   0.4441   0.3330   0.2497
  d       2.2515   1.5007      ---   0.6664   0.4998   0.3747
  e       3.3788   2.2520   1.5007      ---   0.7500   0.5622
  f       4.5052   3.0027   2.0009   1.3334      ---   0.7497
  g       6.0096   4.0055   2.6691   1.7786   1.3339      ---
```

Matching entries (within 2% of n=6 targets):

| Planet Pair | Ratio | Target | Label | Deviation |
|-------------|-------|--------|-------|-----------|
| c / b | 1.500349 | 1.5 | 3/2 = n/tau | 0.023% |
| d / c | 1.500664 | 1.5 | 3/2 = n/tau | 0.044% |
| e / d | 1.500666 | 1.5 | 3/2 = n/tau | 0.044% |
| f / e | 1.333369 | 4/3 | tau / sigma_over_tau | 0.003% |
| g / f | 1.333947 | 4/3 | tau / sigma_over_tau | 0.046% |
| f / d | 2.000941 | 2 | phi(6) | 0.047% |
| f / c | 3.002739 | 3 | sigma/tau | 0.091% |
| g / c | 4.005496 | 4 | tau(6) | 0.137% |
| g / b | 6.009640 | 6 | n | 0.161% |

### 3.4 Ratio Matrix: TRAPPIST-1

Periods (days): b=1.511, c=2.422, d=4.050, e=6.100, f=9.207, g=12.353, h=18.767

Selected matching entries:

| Planet Pair | Ratio | Target | Deviation |
|-------------|-------|--------|-----------|
| e / b | 4.037 | tau = 4 | 0.93% |
| f / b | 6.094 | n = 6 | 1.56% |
| e / d | 1.506 | 3/2 | 0.42% |
| g / d | 3.050 | sigma/tau = 3 | 1.68% |
| g / e | 2.025 | phi = 2 | 1.26% |
| g / f | 1.342 | 4/3 | 0.63% |
| h / f | 2.038 | phi = 2 | 1.92% |
| h / g | 1.519 | 3/2 | 1.28% |

TRAPPIST-1 shows more matches than HD 110067 in total count (owing to
having 7 planets and thus 21 pairwise ratios vs. 15), but with lower
precision: typical deviations of 0.5-2% compared to HD 110067's
0.003-0.16%.

### 3.5 Ratio Matrix: TOI-1136

Periods (days): b=4.173, c=6.257, d=12.517, e=18.802, f=26.316, g=39.537

Selected matching entries:

| Planet Pair | Ratio | Target | Deviation |
|-------------|-------|--------|-----------|
| d / b | 2.9996 | sigma/tau = 3 | 0.012% |
| c / b | 1.4994 | 3/2 | 0.039% |
| d / c | 2.0005 | phi = 2 | 0.027% |
| e / c | 3.005 | sigma/tau = 3 | 0.167% |
| e / d | 1.502 | 3/2 | 0.140% |
| g / f | 1.502 | 3/2 | 0.160% |

Notable: TOI-1136 b-to-d ratio = 3.0004, matching sigma/tau = 3 to
0.01% -- among the most precise individual matches in the survey.

## 4. Statistical Analysis

### 4.1 Bulk Detection Rate

The observed detection rate of 27.5% (82/298 systems) is **not**
statistically significant. The Monte Carlo null model predicts that
47-94% of resonant-chain systems should produce at least one match
purely by chance, depending on planet count. The real detection rate
falls below this because:

1. Many multi-planet systems are not in resonant chains.
2. Systems with only 3 planets have fewer pairwise ratios to test.
3. Some systems have incomplete period measurements.

We conclude that **the bulk detection rate provides no evidence for
any special role of n=6 arithmetic in orbital dynamics.**

### 4.2 HD 110067 Completeness

HD 110067 is distinguished not by its match count but by its
**structural completeness**. Every consecutive planet pair participates
in a 3:2 or 4:3 resonance, and the ratios compose multiplicatively:

```
  Chain: (3/2) x (3/2) x (3/2) x (4/3) x (4/3)
       = (3/2)^3 x (4/3)^2
       = 27/8 x 16/9
       = 432/72
       = 6
       = n
```

The product of all five consecutive period ratios equals the perfect
number n=6, exactly. The observed value is 6.0096, a deviation of 0.16%
from 6.000.

Monte Carlo test: among 200,000 synthetic resonant six-planet chains,
1.2% produce 9 or more n=6 ratio matches. This corresponds to
p ~ 0.012, or approximately 2.5 sigma -- suggestive but not
conclusive.

### 4.3 Precision of Individual Ratios

The most precise matches in the survey:

| System | Pair | Observed | Target | Deviation |
|--------|------|----------|--------|-----------|
| HD 110067 | e-f | 1.333369 | 4/3 | 0.003% |
| TOI-1136 | b-d | 2.999626 | 3 | 0.012% |
| HD 110067 | b-c | 1.500349 | 3/2 | 0.023% |
| TOI-1136 | c-d | 2.000536 | 2 | 0.027% |
| HD 110067 | d-e | 1.500666 | 3/2 | 0.044% |

These precisions (0.003-0.05%) are notable but expected for systems
in confirmed resonant chains. Tidal evolution and disk migration
naturally drive systems toward exact commensurability.

### 4.4 What Would Be Significant

For the n=6 connection to rise above numerological curiosity, one would
need:
- A dynamical mechanism linking the number-theoretic property of
  perfectness (sigma(n) = 2n) to resonance selection.
- A prediction: e.g., that systems with exactly 6 planets should
  preferentially occupy the specific ratio chain (3/2)^a x (4/3)^b
  with a + b = 5 and the product = 6.
- Confirmation that HD 110067 is not a selection artifact (it was
  specifically studied because of its resonant chain).

## 5. HD 110067 Case Study

### 5.1 System Overview

HD 110067 (HIP 61835, TIC 356473198) is a bright G0V star hosting
exactly six transiting sub-Neptune planets discovered by TESS and
CHEOPS (Luque et al. 2023, Nature 623, 932). All six planets are in a
continuous chain of first-order mean-motion resonances.

```
  Star:    HD 110067
  SpType:  G0V
  V mag:   8.4
  Dist:    32.6 pc
  RA/Dec:  12h 42m 42s, +08d 44m 10s (Virgo)
```

### 5.2 The Resonant Chain

```
  Planet   Period (d)    Ratio to prev    MMR     n=6 label
  ------   ----------    -------------    ---     ---------
  b         9.1137          ---           ---       ---
  c        13.6737       1.5003 (3:2)     3:2     n/tau
  d        20.5196       1.5007 (3:2)     3:2     n/tau
  e        30.7931       1.5007 (3:2)     3:2     n/tau
  f        41.0585       1.3334 (4:3)     4:3     tau/3
  g        54.7699       1.3339 (4:3)     4:3     tau/3
```

### 5.3 Self-Referential Structure

The system contains exactly n=6 planets, and the end-to-end period
ratio P(g)/P(b) = 6.0096 approximates n=6 to 0.16%. Moreover, the
intermediate ratios span multiple n=6 arithmetic values:

```
  Ratio ladder through the system:

  b --[x 3/2]--> c --[x 3/2]--> d --[x 3/2]--> e --[x 4/3]--> f --[x 4/3]--> g
                                                                              |
  b --------[x 6 = n]-------------------------------------------------------> g
  c --------[x 4 = tau]-----------------------------------------------------> g
  c --------[x 3 = sigma/tau]----------------------------> f
  d --------[x 2 = phi]---------------------> f

  Values realized: 4/3, 3/2, 2(=phi), 3(=sigma/tau), 4(=tau), 6(=n)
```

All six values -- 4/3, 3/2, 2, 3, 4, 6 -- are present in the pairwise
ratio matrix. These are precisely the ratios constructible from the
divisors of 6 (i.e., from {1, 2, 3, 6}).

### 5.4 The Arithmetic Identity

The chain product identity is exact in the integers:

```
  (3/2)^3 x (4/3)^2 = 27/8 x 16/9 = 432/72 = 6
```

This is not a coincidence of measurement -- it is an algebraic identity.
Any system with three consecutive 3:2 resonances followed by two
consecutive 4:3 resonances will necessarily have an end-to-end ratio of
6:1, regardless of the absolute periods. The question is only why this
particular arrangement (3 x 3:2 then 2 x 4:3) was selected by nature
in a six-planet system.

### 5.5 Interpretation

The honest interpretation: HD 110067 is a resonant chain, and resonant
chains are built from first-order MMRs (ratios (p+1)/p for small p).
The two lowest first-order ratios are 3/2 and 4/3. A chain of five
consecutive first-order resonances using only 3:2 and 4:3 can produce
end-to-end ratios of:

```
  5 x (3/2) = 7.59
  4 x (3/2) + 1 x (4/3) = 6.75
  3 x (3/2) + 2 x (4/3) = 6.00   <-- HD 110067
  2 x (3/2) + 3 x (4/3) = 5.33
  1 x (3/2) + 4 x (4/3) = 4.74
  5 x (4/3) = 4.21
```

Only the combination (3 x 3:2 + 2 x 4:3) produces an integer
end-to-end ratio, and that integer is 6. This is the unique
integer-valued option among first-order resonant chains of length 5.

## 6. Spatial Clustering

Two constellations contain pairs of high-match systems:

```
  Aquarius:
    GJ 876     (RA 22h 53m, Dec -14d 16m)   4 matches
    TRAPPIST-1 (RA 23h 06m, Dec -05d 03m)  12 matches
    Angular separation: ~10 degrees

  Lyra:
    Kepler-9   (RA 19h 02m, Dec +38d 17m)   3 matches
    Kepler-235 (RA 19h 37m, Dec +44d 25m)   3 matches
    Angular separation: ~8 degrees
```

This clustering is an artifact of the Kepler field of view (Lyra/Cygnus)
and the proximity of TRAPPIST-1 and GJ 876 on the sky. It does not
indicate a physical association.

## 7. Target Coordinates

| System | RA (J2000) | Dec (J2000) | Distance (pc) | Planets | Matches |
|--------|-----------|-------------|---------------|---------|---------|
| TRAPPIST-1 | 23h 06m 30s | -05d 02m 29s | 12.4 | 7 | 12 |
| HD 110067 | 12h 42m 42s | +08d 44m 10s | 32.6 | 6 | 9 |
| TOI-1136 | 11h 38m 22s | +17d 12m 08s | 98.3 | 6 | 5 |
| Kepler-80 | 19h 44m 27s | +39d 58m 44s | 418 | 6 | 5 |
| GJ 876 | 22h 53m 17s | -14d 15m 49s | 4.7 | 4 | 4 |
| Kepler-9 | 19h 02m 18s | +38d 17m 15s | 720 | 3 | 3 |
| Kepler-235 | 19h 37m 03s | +44d 25m 44s | 1040 | 4 | 3 |

## 8. Discussion

### 8.1 What Is Not Significant

The bulk result -- 82/298 systems containing n=6 period ratio
matches -- is fully explained by the natural prevalence of mean-motion
resonances in multi-planet systems. The Monte Carlo null model shows
that random resonant chains produce matches at a higher rate than
observed. No special role for n=6 is implied by the detection rate.

### 8.2 What Is Notable

The HD 110067 system presents two features worth noting:

1. **Algebraic completeness.** All six ratios constructible from the
   divisors of 6 -- namely 4/3, 3/2, 2, 3, 4, 6 -- appear in the
   pairwise ratio matrix of a system with exactly 6 planets.

2. **Integer end-to-end ratio.** The product (3/2)^3 x (4/3)^2 = 6 is
   the unique integer obtainable from a five-link first-order resonant
   chain. The system "chose" the only combination that closes to an
   integer, and that integer equals the planet count.

However, these observations have natural explanations:

- The completeness follows algebraically from having both 3:2 and 4:3
  links in sufficient number: any three 3:2 links and two 4:3 links
  produce all the ratios automatically.
- The integer closure is an arithmetic identity, not a physical
  prediction.
- The planet count equaling 6 may be coincidental (one additional
  undetected planet would break the correspondence).

### 8.3 Precision

The sub-0.05% precision of the HD 110067 ratios (especially
e/f = 1.333369 vs. 4/3, deviation 0.003%) is consistent with a young,
dynamically cool resonant chain. Systems that have undergone significant
tidal evolution or instability show larger deviations from exact
commensurability. The precision reflects the dynamical youth of the
system, not a deeper mathematical connection.

### 8.4 Open Question

The one genuinely open question is: **why does HD 110067 have the
specific resonant chain (3:2, 3:2, 3:2, 4:3, 4:3) rather than some
other combination?** Planet formation models with disk migration can
produce resonant chains, but the specific selection of resonance orders
depends on disk properties, planet masses, and migration rates. Whether
the integer-closure property plays any dynamical role (e.g., through
enhanced stability) is a question that could be addressed with
N-body simulations.

## 9. Conclusion

A scan of 298 multi-planet systems from the NASA Exoplanet Archive finds
82 systems (27.5%) with orbital period ratios matching n=6 arithmetic
targets within 2% tolerance. This detection rate is consistent with the
null expectation from Monte Carlo simulations of resonant chains and
provides no evidence for a special role of n=6 in planetary dynamics.

The six-planet system HD 110067 stands out for its structural
completeness: consecutive period ratios of (3/2, 3/2, 3/2, 4/3, 4/3)
produce all six divisor-ratios of 6 in the pairwise matrix, with
precisions of 0.003% to 0.16%. The end-to-end ratio P(g)/P(b) = 6.010
approximates n=6, following from the algebraic identity
(3/2)^3 x (4/3)^2 = 6. This is the unique integer obtainable from a
first-order resonant chain of length five.

Whether the arithmetic completeness of HD 110067 is a dynamical
coincidence, a stability selection effect, or a hint of deeper structure
remains an open question for planet formation theory.

## Data Availability

All orbital periods used in this analysis are publicly available from
the NASA Exoplanet Archive (https://exoplanetarchive.ipac.caltech.edu/).
Analysis code is available in the SEDI repository (sedi/sources/exoplanet.py).

## References

1. Luque, R. et al. (2023). "A resonant sextuplet of sub-Neptunes
   transiting the bright star HD 110067." Nature 623, 932-937.
2. Gillon, M. et al. (2017). "Seven temperate terrestrial planets
   around the nearby ultracool dwarf star TRAPPIST-1." Nature 542, 456.
3. Dai, F. et al. (2023). "TOI-1136 is a Young, Coplanar, Aligned
   Planetary System in a Pristine Resonant Chain." AJ 165, 33.
4. Fabrycky, D. et al. (2014). "Architecture of Kepler's Multi-
   Transiting Systems." ApJ 790, 146.
5. NASA Exoplanet Archive (2026). Planetary Systems Table.
   https://exoplanetarchive.ipac.caltech.edu/
6. SEDI Project. (2026). "Scanning for n=6 patterns in astrophysical
   data." TECS-L repository.
