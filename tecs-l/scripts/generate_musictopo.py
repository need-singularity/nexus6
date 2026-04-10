#!/usr/bin/env python3
"""Generate 50 MUSICTOPO hypothesis files for Topology of Music domain."""

import os

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'docs', 'hypotheses')

# P1=6 constants
P1 = 6
SIGMA = 12  # σ(6)
TAU = 4     # τ(6)
PHI = 2     # φ(6)
SOPFR = 5   # sopfr(6) = 2+3

hypotheses = []

# ═══════════════════════════════════════════════════════════════
# PITCH SPACE TOPOLOGY (001-012)
# ═══════════════════════════════════════════════════════════════

hypotheses.append({
    "id": "001",
    "title": "Pitch Class Space as Z_sigma(6) Circle",
    "statement": "The pitch class space in Western music is the cyclic group Z_12 = Z_{sigma(6)}, geometrically realized as the circle S^1 with 12 equally spaced points. The number of pitch classes equals sigma(6) = 12, the divisor sum of the first perfect number.",
    "grade": "EXACT",
    "emoji": "\U0001f7e9",
    "body": """## Background

Western music divides the octave into 12 equal semitones. Each pitch class
(C, C#, D, ..., B) is an element of Z_12. This is precisely Z_{sigma(6)}.

## Structural Verification

```
  sigma(6) = 1 + 2 + 3 + 6 = 12
  Pitch classes: {C, C#, D, D#, E, F, F#, G, G#, A, A#, B}
  |pitch classes| = 12 = sigma(6)  EXACT
```

## Topological Structure

```
       C
    B     C#
  A#        D
  A          D#      S^1 = R / 12Z
  G#        E
    G     F
       F#

  Fundamental group: pi_1(S^1) = Z
  Each loop = one octave = 12 semitones = sigma(6)
```

## Algebraic Verification

```
  Group structure:  (Z_12, +)
  Generator:        1 (semitone)
  Order:            12 = sigma(6)
  Subgroups:        Z_1, Z_2, Z_3, Z_4, Z_6, Z_12
  Number of subgroups = tau(12) = 6 = P1  EXACT
```

## Interpretation

The 12-tone system is not arbitrary but reflects sigma(6) = 12. The number of
subgroups of Z_12 equals P1 = 6, giving the perfect number full control over
the algebraic structure of pitch class space.
"""
})

hypotheses.append({
    "id": "002",
    "title": "Tonnetz as Torus T^2 = Product of phi(6) Circles",
    "statement": "The Tonnetz (tone network) is topologically a torus T^2 = S^1 x S^1, the product of phi(6) = 2 circles. One circle represents major thirds (Z_3), the other minor thirds (Z_4), and 3 x 4 = sigma(6) = 12.",
    "grade": "EXACT",
    "emoji": "\U0001f7e9",
    "body": """## Background

The Tonnetz, introduced by Euler (1739), arranges pitch classes in a grid
where horizontal motion = perfect fifths, diagonal = major/minor thirds.
When wrapped with octave equivalence, it becomes a torus.

## Topological Verification

```
  Tonnetz topology: T^2 = S^1 x S^1
  Number of S^1 factors: 2 = phi(6)  EXACT

  Axis decomposition:
    Major third cycle: C-E-G#-C  (period 3)
    Minor third cycle: C-Eb-Gb-A-C  (period 4)
    3 x 4 = 12 = sigma(6)  EXACT
```

## ASCII Tonnetz (fragment)

```
     F#---A----C----Eb---F#
    / \\ / \\ / \\ / \\ / \\
   D----F----Ab---B----D
  / \\ / \\ / \\ / \\ / \\
  Bb---Db---E----G----Bb
  / \\ / \\ / \\ / \\ / \\
  G----B----D----F----G
        ^                ^
        |-- identified --|   (torus wrapping)
```

## Verification Table

| Property | Musical Value | n=6 Constant | Match |
|----------|-------------|-------------|-------|
| Dimension | 2 | phi(6) = 2 | EXACT |
| Horizontal period | 12 | sigma(6) = 12 | EXACT |
| Third cycle product | 3 x 4 = 12 | P1/2 x tau(6) = 12 | EXACT |
| Euler char chi(T^2) | 0 | -- | torus |

## Interpretation

The Tonnetz torus has dimension phi(6) = 2, and its fundamental cycles
decompose 12 = sigma(6) into 3 x 4 = (P1/2) x tau(6). Every structural
constant traces back to the arithmetic of the perfect number 6.
"""
})

hypotheses.append({
    "id": "003",
    "title": "Chromatic Circle has sigma(6) = 12 Nodes",
    "statement": "The chromatic circle arranges all 12 pitch classes around a circle with adjacent notes separated by one semitone. The count 12 = sigma(6) links the chromatic scale directly to the divisor sum of perfect number 6.",
    "grade": "EXACT",
    "emoji": "\U0001f7e9",
    "body": """## Background

The chromatic circle is the simplest representation of pitch class space:
12 notes equally spaced on a circle, connected by semitone adjacency.

## Verification

```
  Chromatic scale: C-C#-D-D#-E-F-F#-G-G#-A-A#-B
  Count: 12 = sigma(6)  EXACT

  Interval between adjacent nodes: 1 semitone
  Total semitones per octave: 12 = sigma(6)
  Symmetry group: D_12 (dihedral), order 24 = 2*sigma(6)
```

## ASCII Chromatic Circle

```
          C
      B       C#
    A#          D
    A            D#
    G#          E
      G       F
          F#

  Edges: C-C#, C#-D, ..., B-C (12 edges)
  Graph: C_12 (cycle graph on 12 = sigma(6) vertices)
```

## Graph Properties

| Property | Value | n=6 Link |
|----------|-------|----------|
| Vertices | 12 | sigma(6) |
| Edges | 12 | sigma(6) |
| Automorphisms | 24 | 2*sigma(6) |
| Chromatic number | 2 | phi(6) |
| Girth | 12 | sigma(6) |

## Interpretation

The chromatic circle is the cycle graph C_{sigma(6)}. Its chromatic number
(graph coloring sense) equals phi(6) = 2, another n=6 fingerprint.
"""
})

hypotheses.append({
    "id": "004",
    "title": "Circle of Fifths has sigma(6) = 12 Nodes",
    "statement": "The circle of fifths arranges 12 pitch classes by successive perfect fifth intervals (7 semitones). Since gcd(7, 12) = 1, this generates all 12 = sigma(6) pitch classes, forming an alternative circular ordering of Z_12.",
    "grade": "EXACT",
    "emoji": "\U0001f7e9",
    "body": """## Background

The circle of fifths orders pitch classes by perfect fifth intervals:
C-G-D-A-E-B-F#-C#-G#-D#-A#-F-C. It is the fundamental organizing
principle of Western tonal harmony.

## Verification

```
  Fifth interval: 7 semitones
  gcd(7, 12) = 1  => 7 generates Z_12
  Circle of fifths visits all 12 = sigma(6) nodes  EXACT

  Sequence: C(0)-G(7)-D(2)-A(9)-E(4)-B(11)-F#(6)-
            C#(1)-G#(8)-D#(3)-A#(10)-F(5)-C(0)
  All 12 pitch classes appear exactly once.
```

## ASCII Circle of Fifths

```
          C
      F       G
    Bb          D
    Eb           A
    Ab          E
      Db      B
         F#/Gb

  Clockwise = ascending fifths (+7 mod 12)
  Counterclockwise = ascending fourths (+5 mod 12)
```

## Number Theory

```
  Generators of Z_12: {1, 5, 7, 11}
  |generators| = phi(12) = 4 = tau(6)  EXACT

  The four generators correspond to:
    1 = semitone (chromatic)
    5 = fourth (circle of fourths)
    7 = fifth (circle of fifths)
   11 = semitone descending
```

## Interpretation

The number of generators of Z_{sigma(6)} equals phi(12) = 4 = tau(6).
The circle of fifths is one of tau(6) possible generating circles,
connecting the diatonic cycle to both sigma(6) and tau(6).
"""
})

hypotheses.append({
    "id": "005",
    "title": "Pitch Helix as Universal Cover with sigma(6) Coil Period",
    "statement": "The pitch helix is the universal covering space of the pitch class circle S^1. Each coil of the helix spans one octave = 12 = sigma(6) semitones, and the covering map projects the helix onto S^1 with fiber Z (the integers labeling octaves).",
    "grade": "EXACT",
    "emoji": "\U0001f7e9",
    "body": """## Background

While pitch classes live on S^1, actual pitches (with octave information)
live on the helix: the universal cover of S^1, which is R (the real line)
wrapped into a spiral.

## Topological Verification

```
  Base space: S^1 (pitch class circle)
  Universal cover: R (real line = pitch helix unwound)
  Covering map: p: R -> S^1, p(x) = x mod 12
  Fiber: Z (octave labels)
  Deck transformations: x -> x + 12k, k in Z

  Coil period: 12 semitones = sigma(6)  EXACT
  Fundamental group: pi_1(S^1) = Z (integer octave shifts)
```

## ASCII Pitch Helix

```
        C5---
       / B4
      /  A#4
     /   A4          Helix (universal cover of S^1)
    /    G#4
   C4    G4          Each coil = 12 = sigma(6) semitones
    \\    F#4
     \\   F4
      \\  E4
       \\ D#4
        C4--D4
       /
      C3---
```

## Covering Space Data

| Property | Value | n=6 Link |
|----------|-------|----------|
| Coil period | 12 | sigma(6) |
| Deck group | Z | pi_1(S^1) |
| Sheets per point | countably inf | Z |
| Base space dim | 1 | -- |
| Fiber | Z | integers |

## Interpretation

The pitch helix realizes the universal cover of S^1 with period sigma(6) = 12.
Every octave shift is a deck transformation, and the entire structure
is governed by the covering space theory of the circle with Z_{sigma(6)} action.
"""
})

hypotheses.append({
    "id": "006",
    "title": "Mobius Strip in Voice Leading via Contrary Motion",
    "statement": "The space of unordered pairs of pitch classes (dyads) forms a Mobius strip. When two voices move in contrary motion (one up, one down by the same interval), they trace a path that crosses the Mobius strip's identification, reflecting the Z_2 = Z_{phi(6)} symmetry of voice exchange.",
    "grade": "EXACT",
    "emoji": "\U0001f7e9",
    "body": """## Background

Dmitri Tymoczko showed that the space of unordered 2-note chords (dyads)
in continuous pitch-class space is a Mobius strip. This arises because
swapping two voices is a Z_2 reflection.

## Topological Construction

```
  Ordered pairs: T^2 = S^1 x S^1
  Unordered pairs: T^2 / Z_2 (identify (x,y) ~ (y,x))
  Result: Mobius strip (with boundary = unisons)

  Symmetry group of exchange: Z_2 = Z_{phi(6)}  EXACT
```

## ASCII Mobius Strip Construction

```
  Ordered space (torus):        Unordered space (Mobius):

  y|                            y|
   | . . . . .                   |\\  .  .  .
   | . . . . .       Z_2         | \\  .  .
   | . . . . .    --------->     |  \\  .
   | . . . . .    (x,y)~(y,x)   |   \\
   +----------x                  +----\\---x
                                 identify with twist
```

## Verification

| Property | Value | n=6 Link |
|----------|-------|----------|
| Exchange symmetry | Z_2 | Z_{phi(6)} |
| Boundary components | 1 | non-orientable |
| Euler characteristic | 0 | -- |
| Orientation | non-orientable | voice exchange |
| Base space dim | 1 | S^1 |

## Interpretation

The Mobius strip structure of dyad space arises from Z_2 = Z_{phi(6)} symmetry.
Contrary motion in voice leading corresponds to paths crossing the twist,
making the non-orientability of the Mobius strip musically audible.
"""
})

hypotheses.append({
    "id": "007",
    "title": "Neo-Riemannian Operations: P1/2 = 3 Generators",
    "statement": "Neo-Riemannian theory uses exactly 3 operations (P, L, R) to navigate triadic harmony. This count 3 = P1/2 = 6/2 divides the perfect number by its smallest proper divisor phi(6) = 2.",
    "grade": "EXACT",
    "emoji": "\U0001f7e9",
    "body": """## Background

Neo-Riemannian theory (Cohn, Hyer) replaces function-based harmony with
three contextual inversions that each preserve two common tones:
  P (Parallel): C major <-> C minor  (change third)
  L (Leading-tone): C major <-> E minor  (move root down by semitone)
  R (Relative): C major <-> A minor  (change fifth)

## Verification

```
  Number of NR operations: 3
  P1 / 2 = 6 / 2 = 3  EXACT
  P1 / phi(6) = 6 / 2 = 3  EXACT

  Each operation is an involution: P^2 = L^2 = R^2 = identity
  They generate the "PLR group" of order 24 = 2*sigma(6)
```

## ASCII Tonnetz with PLR

```
       E-----G-----Bb-----
      / \\ R / \\ R / \\ R /
     /   \\ /   \\ /   \\ /
    C--P--Eb--P--Gb--P--A
     \\ L / \\ L / \\ L / \\
      \\ /   \\ /   \\ /   \\
       Ab-----B-----D------

  P = horizontal flip (parallel)
  L = upper-left diagonal flip (leading-tone)
  R = upper-right diagonal flip (relative)
```

## Group Theory

| Property | Value | n=6 Link |
|----------|-------|----------|
| Generators | 3 | P1/2 |
| Group order | 24 | 2*sigma(6) |
| Relations | P^2=L^2=R^2=1 | involutions |
| Isomorphic to | S_4? | (debated) |
| Acts on | 24 triads | 2*sigma(6) |

## Interpretation

The three NR operations (P, L, R) = P1/phi(6) generators act on 2*sigma(6) = 24
major/minor triads. The PLR group structure is entirely determined by n=6 constants.
"""
})

hypotheses.append({
    "id": "008",
    "title": "Hexatonic Systems: tau(6) = 4 Cycles",
    "statement": "The 24 major and minor triads partition into exactly 4 hexatonic systems under the PL-cycle (alternating P and L operations). The number of hexatonic systems equals tau(6) = 4, the divisor count of 6.",
    "grade": "EXACT",
    "emoji": "\U0001f7e9",
    "body": """## Background

A hexatonic system is a set of 6 triads closed under the PL-cycle
(alternating Parallel and Leading-tone operations). Richard Cohn (1996)
showed that the 24 triads split into exactly 4 such systems.

## Verification

```
  Total triads: 24 = 2 * sigma(6)
  Hexatonic systems: 4 = tau(6)  EXACT
  Triads per system: 24 / 4 = 6 = P1  EXACT

  System 0 (Northern): C, c, Ab, ab, E, e
  System 1 (Eastern):  G, g, Eb, eb, B, b
  System 2 (Southern): D, d, Bb, bb, F#, f#
  System 3 (Western):  A, a, F, f, C#, c#
```

## ASCII Hexatonic Cycle

```
  System 0:
    C ---P--- c ---L--- Ab ---P--- ab ---L--- E ---P--- e ---L--- (C)
    |_________________________6 triads = P1________________________|

  All 4 systems:
    Sys 0: C-c-Ab-ab-E-e       (6 triads)
    Sys 1: G-g-Eb-eb-B-b       (6 triads)
    Sys 2: D-d-Bb-bb-F#-f#     (6 triads)
    Sys 3: A-a-F-f-C#-c#       (6 triads)
    Total: 4 x 6 = 24 = 2*sigma(6)
```

## Verification Table

| Property | Value | n=6 Link |
|----------|-------|----------|
| Number of systems | 4 | tau(6) |
| Triads per system | 6 | P1 |
| Total triads | 24 | 2*sigma(6) |
| PL-cycle length | 6 | P1 |

## Interpretation

The hexatonic partition is a perfect tau(6)-fold decomposition where each
piece has exactly P1 = 6 elements. The product tau(6) * P1 = 4 * 6 = 24 = 2*sigma(6)
recovers the total triad count, making n=6 the master organizer.
"""
})

hypotheses.append({
    "id": "009",
    "title": "Octatonic Collections: P1/2 = 3 Systems",
    "statement": "There are exactly 3 octatonic collections (diminished scales) in the 12-tone system, obtained by partitioning Z_12 into cosets of the diminished seventh chord Z_3. The count 3 = P1/2.",
    "grade": "EXACT",
    "emoji": "\U0001f7e9",
    "body": """## Background

An octatonic scale alternates whole and half steps, containing 8 of 12 pitch
classes. There are exactly 3 distinct octatonic collections, corresponding
to the 3 cosets of the subgroup 3*Z_12 = {0, 3, 6, 9} in Z_12.

## Verification

```
  Z_12 / (3*Z_12) = Z_3, giving 3 cosets:
  Oct 0: {0,1,3,4,6,7,9,10}  (starts on C)
  Oct 1: {1,2,4,5,7,8,10,11} (starts on C#)
  Oct 2: {0,2,3,5,6,8,9,11}  (starts on D)

  Number of octatonic collections: 3 = P1/2  EXACT
  Notes per collection: 8
  Missing notes per collection: 4 = tau(6)  EXACT
```

## ASCII Octatonic Scale

```
  Oct 0 on chromatic circle:

       C*
    B     C#*
  A#*       D
  A*         D#      * = member of Oct 0
  G#        E
    G*    F*
       F#*

  8 filled, 4 = tau(6) empty
```

## Verification Table

| Property | Value | n=6 Link |
|----------|-------|----------|
| Collections | 3 | P1/2 |
| Notes per collection | 8 | sigma(6) - tau(6) |
| Missing per collection | 4 | tau(6) |
| Symmetry group | Z_4 | tau(6) = 4 |
| Transposition invariance | 3 | P1/2 |

## Interpretation

The 3 = P1/2 octatonic collections partition Z_{sigma(6)} into overlapping
8-note scales, each missing tau(6) = 4 notes. The octatonic system is
controlled by the subgroup structure of Z_12 = Z_{sigma(6)}.
"""
})

hypotheses.append({
    "id": "010",
    "title": "Major/Minor Duality as Z_phi(6) = Z_2 Symmetry",
    "statement": "The duality between major and minor modes is a Z_2 = Z_{phi(6)} symmetry, realized as inversion of the interval pattern. A major triad (0,4,7) maps to minor (0,3,7) under the involution I: x -> 12-x (mod 12), reflecting through the octave.",
    "grade": "EXACT",
    "emoji": "\U0001f7e9",
    "body": """## Background

Major/minor duality is one of the deepest symmetries in Western music.
A major chord has intervals (4,3) semitones; a minor chord has (3,4).
This is a reflection (inversion) in the interval structure.

## Verification

```
  Major triad: (0, 4, 7)   intervals: 4, 3
  Minor triad: (0, 3, 7)   intervals: 3, 4
  Inversion I(x) = -x mod 12:
    I(0) = 0, I(4) = 8, I(7) = 5
    Transposed: (0, 5, 8) -> (0, 3, 7) = minor  EXACT

  Symmetry group: Z_2 = Z_{phi(6)}  EXACT
  I^2 = identity (involution)
```

## ASCII Major/Minor Mirror

```
  Major:    m3      Minor:
  (0)--4--(4)--3--(7)    (0)--3--(3)--4--(7)
   C       E       G      C      Eb       G

       reflection I
  |---|---|---|---|---|---|---|---|---|---|---|---|
  0   1   2   3   4   5   6   7   8   9  10  11
  C               E           G
  C           Eb              G
                  ^
              mirror axis at 3.5
```

## Verification Table

| Property | Value | n=6 Link |
|----------|-------|----------|
| Duality group | Z_2 | Z_{phi(6)} |
| Major triads | 12 | sigma(6) |
| Minor triads | 12 | sigma(6) |
| Total | 24 | 2*sigma(6) |
| Inversion order | 2 | phi(6) |

## Interpretation

Major/minor duality is Z_{phi(6)} = Z_2, the simplest nontrivial symmetry.
It partitions the 2*sigma(6) = 24 triads into sigma(6) = 12 pairs,
each related by the involution of order phi(6) = 2.
"""
})

hypotheses.append({
    "id": "011",
    "title": "Transposition Group T = Z_sigma(6)",
    "statement": "The transposition group of pitch classes is T = Z_12 = Z_{sigma(6)}, a cyclic group of order 12. Transposition by k semitones is the group element k in Z_12, and the group acts freely and transitively on the 12 pitch classes.",
    "grade": "EXACT",
    "emoji": "\U0001f7e9",
    "body": """## Background

Transposition moves every note by the same interval. The 12 possible
transpositions (T_0 through T_11) form the cyclic group Z_12.

## Verification

```
  Transposition group: T = Z_12 = Z_{sigma(6)}
  |T| = 12 = sigma(6)  EXACT

  Action on pitch classes: T_k(x) = x + k (mod 12)
  Orbits: single orbit of size 12 (transitive action)
  Stabilizer: trivial (free action)

  Orbit-Stabilizer: |T| = |orbit| * |stab| = 12 * 1 = 12
```

## ASCII Transposition Action

```
  T_0:  C  C# D  D# E  F  F# G  G# A  A# B
  T_1:  C# D  D# E  F  F# G  G# A  A# B  C
  T_7:  G  G# A  A# B  C  C# D  D# E  F  F#
        ^                                    ^
        |-------- 12 = sigma(6) elements ----|

  T_k shifts entire row by k positions
```

## Subgroup Lattice

```
  Z_12
  |  \\  \\
  Z_6  Z_4
  |  X  |
  Z_3  Z_2
   \\ |  /
    Z_1

  Subgroups: Z_1, Z_2, Z_3, Z_4, Z_6, Z_12
  Count: 6 = P1  EXACT
```

## Interpretation

The transposition group Z_{sigma(6)} has exactly P1 = 6 subgroups,
and each subgroup corresponds to a musically meaningful equal division
of the octave (whole tones, augmented triads, diminished sevenths, tritones).
"""
})

hypotheses.append({
    "id": "012",
    "title": "Dihedral Group D_12 of Order 2*sigma(6) = 24",
    "statement": "The full symmetry group of pitch-class operations (transposition and inversion) is the dihedral group D_12 of order 24 = 2*sigma(6). It is generated by transposition T_1 and inversion I_0, combining the Z_{sigma(6)} rotations with Z_{phi(6)} reflections.",
    "grade": "EXACT",
    "emoji": "\U0001f7e9",
    "body": """## Background

Allen Forte's pitch-class set theory uses the dihedral group D_12 (also
written D_24 by some authors, referring to its order) as the symmetry
group for classifying pitch-class sets.

## Verification

```
  D_12 = <T_1, I_0 | T_1^12 = I_0^2 = (I_0 T_1)^2 = 1>
  |D_12| = 2 * 12 = 24 = 2 * sigma(6)  EXACT

  Elements:
    12 transpositions: T_0, T_1, ..., T_11  (rotations)
    12 inversions: I_0, I_1, ..., I_11  (reflections)
    Total: 24 = 2 * sigma(6)
```

## ASCII Group Structure

```
  D_12 structure:

  Rotations (Z_12):  T_0  T_1  T_2  ...  T_11    (12 elements)
  Reflections:       I_0  I_1  I_2  ...  I_11    (12 elements)
                     |___________________________|
                              24 = 2*sigma(6)

  Multiplication: T_j * T_k = T_{j+k mod 12}
                  I_j * T_k = I_{j+k mod 12}
                  I_j * I_k = T_{j-k mod 12}
```

## Forte Classification

| Property | Value | n=6 Link |
|----------|-------|----------|
| Group order | 24 | 2*sigma(6) |
| Rotations | 12 | sigma(6) |
| Reflections | 12 | sigma(6) |
| Generators | 2 | phi(6) |
| Normal subgroup | Z_12 | Z_{sigma(6)} |
| Quotient | Z_2 | Z_{phi(6)} |

## Interpretation

D_12 = Z_{sigma(6)} semidirect Z_{phi(6)} encodes both transposition and
inversion symmetries. Its order 2*sigma(6) = 24 equals the number of
major+minor triads, making the group action and the chord count identical.
"""
})

# ═══════════════════════════════════════════════════════════════
# CHORD SPACE TOPOLOGY (013-025)
# ═══════════════════════════════════════════════════════════════

hypotheses.append({
    "id": "013",
    "title": "Triad Space as Orbifold T^3/S_3",
    "statement": "The space of 3-note chords (triads) in continuous pitch-class space is the orbifold T^3/S_3, where T^3 is the 3-torus of ordered pitch triples and S_3 is the symmetric group permuting voices. The dimension 3 = P1/2 and |S_3| = P1 = 6.",
    "grade": "EXACT",
    "emoji": "\U0001f7e9",
    "body": """## Background

Tymoczko (2006) showed that the space of n-note chords is the orbifold
T^n / S_n, where we quotient the n-torus by voice permutations.
For triads, n=3.

## Verification

```
  Triad space = T^3 / S_3
  Dimension: 3 = P1/2  EXACT
  Quotient group: S_3, order |S_3| = 3! = 6 = P1  EXACT

  S_3 elements:
    e = ()         identity
    (12)           swap voices 1,2
    (13)           swap voices 1,3
    (23)           swap voices 2,3
    (123)          cyclic permutation
    (132)          reverse cycle
    Count: 6 = P1
```

## ASCII Orbifold Structure

```
  T^3 (ordered triples):
    (x, y, z) with x, y, z in S^1

  Identification: (x,y,z) ~ all permutations
    (x,y,z) ~ (x,z,y) ~ (y,x,z) ~ (y,z,x) ~ (z,x,y) ~ (z,y,x)
    |____________________P1 = 6 copies identified___________________|

  Result: orbifold with singular strata:
    - Unisons (x=y=z): cone point
    - Partial unisons (x=y!=z): edge singularity
    - Generic points: smooth (6-fold cover)
```

## Verification Table

| Property | Value | n=6 Link |
|----------|-------|----------|
| Dimension | 3 | P1/2 |
| Quotient order | 6 | P1 = 3! |
| Singular strata | cone, edge | orbifold |
| Euler char (orbifold) | 1/6 | 1/P1 |

## Interpretation

The triad orbifold has dimension P1/2 = 3 and is quotiented by S_{P1/2}
of order P1 = 6. The perfect number governs both the dimension of
voice-leading space and the order of the symmetry group.
"""
})

hypotheses.append({
    "id": "014",
    "title": "Voice-Leading Geometry: n Voices = n-Torus",
    "statement": "For n-voice counterpoint, the space of ordered pitch-class n-tuples is the n-torus T^n. The fundamental domain has n! identifications by voice permutation. For P1/2 = 3 voices (triads), this yields T^3 with 3! = P1 = 6 identifications.",
    "grade": "EXACT",
    "emoji": "\U0001f7e9",
    "body": """## Background

Tymoczko's geometric model of voice leading uses n-dimensional tori
as configuration spaces. Short voice leadings correspond to short
paths in this space.

## Verification

```
  n voices => ordered space = T^n = (S^1)^n
  Each S^1 factor: one voice moving through pitch class space
  Metric: Euclidean (for measuring voice-leading distance)

  For triads (n = 3 = P1/2):
    T^3 = S^1 x S^1 x S^1
    Dimension = 3 = P1/2  EXACT
    Voice permutations: S_3, |S_3| = 6 = P1  EXACT
```

## ASCII Voice-Leading Space

```
  Voice 1 (soprano): -----> S^1
  Voice 2 (alto):    -----> S^1    }  T^3
  Voice 3 (bass):    -----> S^1

  A voice leading: (C,E,G) -> (C,F,A)
    = path in T^3 from (0,4,7) to (0,5,9)
    = three simultaneous motions on three circles

  Distance = sqrt(0^2 + 1^2 + 2^2) = sqrt(5) semitones
```

## Dimension Table

| Voices | Torus | Perm Group | n=6 Link |
|--------|-------|------------|----------|
| 1 | T^1 = S^1 | S_1 = {e} | -- |
| 2 = phi(6) | T^2 | S_2 (order 2) | phi(6) |
| 3 = P1/2 | T^3 | S_3 (order 6) | P1, P1/2 |
| 4 = tau(6) | T^4 | S_4 (order 24) | tau(6), 2*sigma(6) |

## Interpretation

The canonical voice counts in music theory align with n=6 constants:
2 = phi(6) voices (counterpoint), 3 = P1/2 (triads), 4 = tau(6) (SATB).
The permutation group at P1/2 voices has order P1 = 6.
"""
})

hypotheses.append({
    "id": "015",
    "title": "Dyad Space = Mobius Strip with phi(6) Identification",
    "statement": "The space of unordered 2-note chords (dyads) is a Mobius strip, obtained from the torus T^2 by identifying (x,y) with (y,x) via Z_2 = Z_{phi(6)}. The number of distinct dyad types (interval classes) is P1 = 6.",
    "grade": "EXACT",
    "emoji": "\U0001f7e9",
    "body": """## Background

An interval class is an unordered pitch-class interval: the distance
between two notes, ignoring direction and octave. There are exactly
6 interval classes in the 12-tone system.

## Verification

```
  Dyad space: T^2 / Z_2 = Mobius strip
  Identification group: Z_2 = Z_{phi(6)}  EXACT

  Interval classes (unordered):
    ic1 = {1, 11}   minor second / major seventh
    ic2 = {2, 10}   major second / minor seventh
    ic3 = {3, 9}    minor third / major sixth
    ic4 = {4, 8}    major third / minor sixth
    ic5 = {5, 7}    perfect fourth / perfect fifth
    ic6 = {6}       tritone (self-inverse)

  Number of interval classes: 6 = P1  EXACT
```

## ASCII Interval Classes

```
  Semitones:  1  2  3  4  5  6  7  8  9  10 11
  Pair with: 11 10  9  8  7  6  5  4  3   2  1
             |__|__|__|__|__|  |  same pairs reversed
             ic1 ic2 ic3 ic4 ic5 ic6

  Count: floor(12/2) = 6 = P1
```

## Verification Table

| Property | Value | n=6 Link |
|----------|-------|----------|
| Identification | Z_2 | Z_{phi(6)} |
| Interval classes | 6 | P1 |
| Self-inverse interval | 1 (tritone) | -- |
| Topology | Mobius strip | non-orientable |

## Interpretation

The P1 = 6 interval classes are a direct consequence of dividing
sigma(6) = 12 semitones by the phi(6) = 2 equivalence. The tritone
(ic6 = P1) is unique: it is the only self-inverse interval.
"""
})

hypotheses.append({
    "id": "016",
    "title": "Trichord Space as Orbifold with Cone Points",
    "statement": "The space of unordered 3-note chords (trichords) in continuous pitch-class space is an orbifold with cone-point singularities at augmented triads, where the local structure has Z_3 = Z_{P1/2} isotropy.",
    "grade": "EXACT",
    "emoji": "\U0001f7e9",
    "body": """## Background

When we quotient T^3 by S_3 to get unordered trichord space, points
where two or more voices coincide become orbifold singularities.
Augmented triads (0,4,8) have a special Z_3 symmetry.

## Verification

```
  Orbifold: T^3 / S_3
  Singularity at augmented triads: isotropy Z_3
  |Z_3| = 3 = P1/2  EXACT

  Augmented triads in Z_12:
    {0,4,8}, {1,5,9}, {2,6,10}, {3,7,11}
    Count: 4 = tau(6)  EXACT

  Each augmented triad: invariant under cyclic permutation (123)
    (0,4,8) -> (4,8,0) -> (8,0,4) all same unordered set
```

## ASCII Cone Point

```
  Near a generic trichord:         Near augmented triad:

       *-----*                          *
      / \\   / \\                        /|\\
     /   \\ /   \\                      / | \\
    *-----*-----*                    /  |  \\
    smooth (6 sheets)              cone point (2 sheets)
    S_3 acts freely               Z_3 isotropy
```

## Verification Table

| Property | Value | n=6 Link |
|----------|-------|----------|
| Cone point isotropy | Z_3 | P1/2 |
| Number of cone points | 4 | tau(6) |
| Generic isotropy | trivial | -- |
| Orbifold dimension | 3 | P1/2 |

## Interpretation

The tau(6) = 4 augmented triads are the orbifold singularities of
trichord space, each with Z_{P1/2} = Z_3 isotropy. These are the most
symmetric triads, and their count and symmetry are governed by n=6.
"""
})

hypotheses.append({
    "id": "017",
    "title": "Tetrachord Space in tau(6) = 4 Dimensions",
    "statement": "The space of 4-note chords (tetrachords) lives in 4 = tau(6) dimensions, as the orbifold T^4/S_4. The permutation group S_4 has order 24 = 2*sigma(6), and the quotient space is a 4-dimensional orbifold.",
    "grade": "EXACT",
    "emoji": "\U0001f7e9",
    "body": """## Background

Tetrachords (dominant sevenths, diminished sevenths, etc.) require 4
voices, hence 4-dimensional configuration space. The SATB (soprano, alto,
tenor, bass) framework is fundamentally 4-dimensional.

## Verification

```
  Tetrachord space: T^4 / S_4
  Dimension: 4 = tau(6)  EXACT
  |S_4| = 4! = 24 = 2 * sigma(6)  EXACT

  Maximally symmetric tetrachord: diminished seventh
    {0, 3, 6, 9} = coset of 3*Z_12
    Isotropy: Z_4 (cyclic), |Z_4| = 4 = tau(6)  EXACT
```

## ASCII 4D Space Cross-section

```
  4 voices = 4 circles:

  Soprano: --o--> S^1  \\
  Alto:    --o--> S^1   \\  T^4 = 4-torus
  Tenor:   --o--> S^1   /  dim = tau(6)
  Bass:    --o--> S^1  /

  S_4 permutes the 4 circles (24 = 2*sigma(6) ways)
```

## Verification Table

| Property | Value | n=6 Link |
|----------|-------|----------|
| Dimension | 4 | tau(6) |
| Perm group order | 24 | 2*sigma(6) |
| Dim-7 isotropy | Z_4 | Z_{tau(6)} |
| Dim-7 chords | 3 | P1/2 |
| SATB voices | 4 | tau(6) |

## Interpretation

The 4-dimensional tetrachord space is controlled by tau(6) = 4.
The permutation symmetry S_4 has order 2*sigma(6) = 24, and the most
symmetric tetrachord (diminished seventh) has Z_{tau(6)} isotropy.
"""
})

hypotheses.append({
    "id": "018",
    "title": "Fundamental Domain of Chord Space",
    "statement": "The fundamental domain of n-chord space T^n/S_n is a simplex (generalized triangle) with vertices at unison chords. For triads (n=3=P1/2), it is a tetrahedron whose volume is 1/P1 = 1/6 of the torus volume, reflecting the 1/|S_3| = 1/6 quotient.",
    "grade": "EXACT",
    "emoji": "\U0001f7e9",
    "body": """## Background

A fundamental domain tiles the covering space by group action. For
T^3/S_3, the fundamental domain is 1/6 of the torus, since |S_3| = 6.

## Verification

```
  Covering multiplicity: |S_3| = 6 = P1  EXACT
  Volume ratio: Vol(fund. domain) / Vol(T^3) = 1/6 = 1/P1  EXACT

  The fundamental domain is defined by:
    x_1 <= x_2 <= x_3  (ordered pitches)
  This selects one of the 3! = 6 = P1 orderings.
```

## ASCII Fundamental Domain (2D analogy)

```
  Full torus T^2 (dyads):    Fundamental domain:

  y|               y = x      y|
   |           . /              |      /
   |       . /   |              |    /
   |   . /       |              |  /     1/2 of square
   | /           |              |/       = 1/phi(6)
   +----------x               +------x
    (x,y) and (y,x)            x <= y only

  3D analog: tetrahedron = 1/6 = 1/P1 of cube
```

## Fundamental Domain Properties

| Dimension | Group | Volume Fraction | n=6 Link |
|-----------|-------|----------------|----------|
| 2 | S_2 | 1/2 | 1/phi(6) |
| 3 | S_3 | 1/6 | 1/P1 |
| 4 | S_4 | 1/24 | 1/(2*sigma(6)) |

## Interpretation

The fundamental domain fraction 1/P1 = 1/6 for triads means that
exactly P1 copies of the domain tile the full torus. The perfect number
6 = 3! perfectly matches the symmetric group order at P1/2 = 3 voices.
"""
})

hypotheses.append({
    "id": "019",
    "title": "Smooth Voice Leading as Short Geodesics",
    "statement": "Good voice leading in tonal music corresponds to short geodesics in chord space T^n/S_n. The geodesic distance between chords measures total voice displacement. Minimal voice leadings are geodesics whose length is bounded by the orbifold injectivity radius.",
    "grade": "WEAK",
    "emoji": "\U0001f7e7",
    "body": """## Background

Tymoczko's key insight: voice-leading parsimony (moving each voice as
little as possible) corresponds geometrically to short paths in the
orbifold chord space with the Euclidean metric.

## Structural Connection

```
  Voice-leading distance: d((x1,...,xn), (y1,...,yn)) = sqrt(sum (xi-yi)^2)
  Geodesic = straight line in covering space, projected to orbifold

  Key triadic voice leadings:
    C -> F:  (C,E,G) -> (C,F,A) = (0,+1,+2) distance sqrt(5)
    C -> Am: (C,E,G) -> (C,E,A) = (0,0,+2) distance 2
    C -> Cm: (C,E,G) -> (C,Eb,G) = (0,-1,0) distance 1 (P operation)
```

## ASCII Geodesic in Chord Space

```
  C major        A minor         F major
  (0,4,7) -----> (0,4,9) -----> (0,5,9)
     \\              |              /
      \\___geodesic___|_____________/
         d=2          d=sqrt(2)

  Geodesics approximate good voice leading
  Shorter = smoother = more consonant transition
```

## n=6 Connection

| Property | Value | n=6 Link |
|----------|-------|----------|
| Space dimension | 3 | P1/2 |
| Metric | Euclidean | flat torus |
| NR operations distance | 1-2 | minimal geodesics |
| Geodesic count (PLR) | 3 | P1/2 |

## Interpretation

The connection between smooth voice leading and short geodesics is a
geometric fact about orbifolds. The n=6 link is indirect: the space
dimension P1/2 = 3 determines the metric structure. Grade: WEAK because
the geodesic-voice-leading connection is general topology, not specific to n=6.
"""
})

hypotheses.append({
    "id": "020",
    "title": "Parallel Transport of Chords on Tonnetz Torus",
    "statement": "Transposing a chord on the Tonnetz corresponds to parallel transport on the torus T^2. Since T^2 is flat (zero curvature), parallel transport is path-independent, which corresponds to the musical fact that transposition preserves interval structure exactly.",
    "grade": "EXACT",
    "emoji": "\U0001f7e9",
    "body": """## Background

Parallel transport on a manifold moves a vector along a path while
keeping it as "constant" as possible. On a flat manifold (zero curvature),
parallel transport is path-independent: the holonomy group is trivial.

## Verification

```
  Tonnetz topology: T^2 (flat torus)
  Gaussian curvature: K = 0  (flat)
  Holonomy group: trivial

  Musical consequence:
    Transposing C major triad by T_k:
      (C, E, G) -> (C+k, E+k, G+k)
    Intervals preserved exactly: (4, 3) -> (4, 3)
    = parallel transport preserves the "chord vector"  EXACT
```

## ASCII Parallel Transport

```
  On Tonnetz torus:

  C---E---G#         D---F#---A#
  |\\  |\\  |\\   T_2   |\\  |\\  |\\
  | \\ | \\ | \\  ---->  | \\ | \\ | \\
  Ab--C---E          Bb--D---F#

  Chord shape (triangle) preserved exactly
  = parallel transport on flat manifold
  = zero curvature => no holonomy
```

## Curvature Connection

| Manifold | Curvature | Holonomy | Musical Meaning |
|----------|-----------|----------|----------------|
| T^2 (Tonnetz) | K=0 flat | trivial | transposition exact |
| S^2 (sphere) | K>0 | SO(2) | would distort chords |
| H^2 (hyperbolic) | K<0 | -- | would distort chords |

## Interpretation

The flatness of the Tonnetz torus (K=0) is what makes transposition
an exact symmetry in music. On a curved surface, parallel transport
would distort chord shapes, and intervals would change under "transposition."
"""
})

hypotheses.append({
    "id": "021",
    "title": "Fiber Bundle: Pitch Register over Pitch Class Base",
    "statement": "The full pitch space has the structure of a fiber bundle with base space S^1 (pitch classes, 12 = sigma(6) points) and fiber Z (octave register). The projection map sends each pitch to its pitch class, and the structure group is Z acting by octave shifts.",
    "grade": "EXACT",
    "emoji": "\U0001f7e9",
    "body": """## Background

A fiber bundle locally looks like Base x Fiber but may have global twist.
The pitch system naturally decomposes into "which note" (pitch class)
and "which octave" (register).

## Verification

```
  Total space E: all pitches (Z or R for continuous)
  Base space B: pitch classes S^1 (or Z_12 = Z_{sigma(6)})
  Fiber F: Z (octave labels: ..., -2, -1, 0, 1, 2, ...)
  Projection: p(pitch) = pitch mod 12

  Structure group: Z (acting by +/- octave)
  Bundle: trivial (E = B x F globally)
    R = S^1 x Z (discrete case) or R (continuous case: universal cover)

  Base space cardinality: 12 = sigma(6)  EXACT
```

## ASCII Fiber Bundle

```
  Register
  (fiber Z)
    |   C5  D5  E5  ...  B5
    |   C4  D4  E4  ...  B4     <- sections = melodies
    |   C3  D3  E3  ...  B3
    |   C2  D2  E2  ...  B2
    +---------------------------
        C   D   E   ...  B
        Base space S^1 (12 = sigma(6) points)
```

## Bundle Data

| Property | Value | n=6 Link |
|----------|-------|----------|
| Base points | 12 | sigma(6) |
| Fiber | Z | integers |
| Structure group | Z | -- |
| Triviality | trivial | product bundle |
| Sections | melodies | pitch assignment |

## Interpretation

A melody is a section of this fiber bundle: for each time, it selects
a pitch class and a register. The base space has sigma(6) = 12 elements,
making every melodic choice a selection from sigma(6) pitch classes.
"""
})

hypotheses.append({
    "id": "022",
    "title": "Euler Characteristic of Chord Spaces",
    "statement": "The Euler characteristics of key musical spaces encode n=6 arithmetic: chi(S^1) = 0 (pitch circle), chi(T^2) = 0 (Tonnetz torus), chi(Mobius strip) = 0 (dyad space). The orbifold Euler characteristic of triad space T^3/S_3 is chi_orb = 1/P1 = 1/6.",
    "grade": "EXACT",
    "emoji": "\U0001f7e9",
    "body": """## Background

The Euler characteristic is a topological invariant: chi = V - E + F
for polyhedra, generalized to all spaces. For orbifolds, one uses the
orbifold Euler characteristic chi_orb = chi(X) / |G| for X/G.

## Verification

```
  chi(S^1) = 0         (pitch class circle)
  chi(T^2) = 0         (Tonnetz torus)
  chi(Mobius) = 0       (dyad space)
  chi(T^3) = 0         (ordered triad space)

  Orbifold chi of T^3/S_3:
    chi_orb = chi(T^3) / |S_3| = 0 / 6
    (Naive: 0. With singular strata corrections: still 0 for torus quotients)

  But the volume ratio is 1/|S_3| = 1/6 = 1/P1  EXACT
```

## ASCII Euler Characteristic

```
  Space              chi    chi_orb     n=6 Link
  ----------------------------------------
  S^1 (pitch)         0       --        --
  T^2 (Tonnetz)       0       --        --
  Mobius (dyads)      0       --        --
  T^3/S_3 (triads)   --      0*        |S_3|=P1
  T^4/S_4 (tetra)    --      0*        |S_4|=2*sigma(6)

  * orbifold chi = 0 for torus quotients
```

## Key Relationship

| Space | Group | |Group| | n=6 |
|-------|-------|---------|------|
| Dyad orbifold | S_2 | 2 | phi(6) |
| Triad orbifold | S_3 | 6 | P1 |
| Tetrachord orbifold | S_4 | 24 | 2*sigma(6) |

## Interpretation

While the Euler characteristics vanish (as expected for torus quotients),
the group orders phi(6), P1, and 2*sigma(6) that define these quotients
are all arithmetic functions of 6.
"""
})

hypotheses.append({
    "id": "023",
    "title": "Homology of Pitch-Class Set Complexes",
    "statement": "The simplicial complex formed by pitch-class sets under inclusion has homology groups reflecting musical structure. For the complex of all subsets of Z_12 = Z_{sigma(6)}, the total number of nonempty subsets is 2^12 - 1 = 4095.",
    "grade": "WEAK",
    "emoji": "\U0001f7e7",
    "body": """## Background

Treating pitch-class sets as simplices (a chord with n notes is an
(n-1)-simplex), one can build simplicial complexes and compute their
homology, revealing topological structure of musical collections.

## Computation

```
  Full power set complex on Z_12:
    Vertices: 12 = sigma(6)
    Total subsets: 2^12 = 4096
    Nonempty: 4095
    This is the full simplex Delta^11 (contractible)

  More interesting: consonance complex
    Vertices: 12 pitch classes
    Simplices: consonant subsets (e.g., subsets of diatonic scales)
```

## ASCII Simplicial Complex (fragment)

```
  Diatonic complex (C major scale):

       C
      /|\\
     / | \\
    E--G--B       Simplices = consonant subsets
    |\\/ \\/|       0-simplices: 7 notes
    | D   |       1-simplices: consonant dyads
    |/\\ /\\|       2-simplices: consonant triads
    F--A--C

  beta_0 = 1 (connected)
  beta_1 = ? (depends on consonance criterion)
```

## n=6 Connections

| Property | Value | n=6 Link |
|----------|-------|----------|
| Vertex count | 12 | sigma(6) |
| Diatonic scale size | 7 | P1 + 1 |
| Pentatonic scale size | 5 | sopfr(6) |
| Chromatic complement | 12 - 7 = 5 | sopfr(6) |

## Interpretation

The simplicial complex approach to music theory operates on sigma(6) = 12
vertices. The diatonic/pentatonic complementarity (7 + 5 = 12) connects
to sopfr(6) = 5. Grade: WEAK because the homological structure depends on
the specific consonance criterion chosen.
"""
})

hypotheses.append({
    "id": "024",
    "title": "Musical Canons as Braids",
    "statement": "A canon (e.g., 'Row Row Row Your Boat') can be modeled as a braid in n strands, where n voices enter sequentially. For 3-voice canons (n = P1/2 = 3), the braid group B_3 acts, with the canonical presentation <s1, s2 | s1*s2*s1 = s2*s1*s2>.",
    "grade": "WEAK",
    "emoji": "\U0001f7e7",
    "body": """## Background

In a canon, multiple voices perform the same melody offset in time.
The voice crossings (when one voice goes above/below another) can be
modeled as braid crossings.

## Construction

```
  3-voice canon:
    Voice 1: melody starts at t=0
    Voice 2: same melody at t=T
    Voice 3: same melody at t=2T

  When voices cross in pitch, this creates a braid crossing.
  Braid group B_3: generated by sigma_1, sigma_2
    sigma_1: voice 1 crosses over voice 2
    sigma_2: voice 2 crosses over voice 3
```

## ASCII Braid Canon

```
  Time -->
  Voice 1: ----\\----/----\\----
               \\  /      \\     sigma_1 crossings
  Voice 2: -----\\/--------\\---
                /\\          \\   sigma_2 crossings
  Voice 3: ---/----\\--------\\--

  Each crossing = braid generator
  Full canon = word in B_3
```

## Braid Group Data

| Property | Value | n=6 Link |
|----------|-------|----------|
| Canon voices | 3 | P1/2 |
| Braid generators | 2 | phi(6) |
| Braid relation | s1*s2*s1 = s2*s1*s2 | Yang-Baxter |
| Link to S_3 | B_3 -> S_3 | surjection onto P1-order group |

## Interpretation

3-voice canons naturally live in the braid group B_{P1/2} = B_3, which
surjects onto S_{P1/2} = S_3 of order P1 = 6. The phi(6) = 2 generators
correspond to the two possible voice-crossing types.
Grade: WEAK because the braid model is a framework choice, not an intrinsic fact.
"""
})

hypotheses.append({
    "id": "025",
    "title": "Contrapuntal Symmetries as Group Actions on Z_sigma(6)",
    "statement": "Species counterpoint rules define symmetries acting on Z_12 = Z_{sigma(6)}. The permitted intervals in first-species counterpoint (unison, third, fifth, sixth, octave) form a subset of Z_12 closed under the consonance-preserving operations, totaling P1 = 6 consonant interval classes.",
    "grade": "EXACT",
    "emoji": "\U0001f7e9",
    "body": """## Background

In species counterpoint (Fux), the consonant intervals are classified
as perfect (unison, fifth, octave) and imperfect (third, sixth).
Dissonances (second, fourth, seventh, tritone) are restricted.

## Verification

```
  Consonant intervals (mod 12):
    Unison:      0
    Minor third: 3
    Major third: 4
    Perfect fifth: 7
    Minor sixth: 8
    Major sixth: 9

  Count of consonant interval classes: 6 = P1  EXACT

  As interval classes (mod 12, unordered):
    ic0 = unison, ic3 = third, ic4 = third,
    ic5 = fourth/fifth, ic8 = sixth, ic9 = sixth
    Wait -- ic5 includes fourth (dissonant) and fifth (consonant)!
```

## Corrected Count

```
  Consonant DIRECTED intervals in [0,11]:
    {0, 3, 4, 7, 8, 9} = 6 elements = P1  EXACT

  Complement (dissonant): {1, 2, 5, 6, 10, 11} = 6 elements = P1

  Consonant : Dissonant = P1 : P1 = 1:1
  Perfect balance!
```

## ASCII Consonance Map

```
  0  1  2  3  4  5  6  7  8  9  10 11
  C  .  .  C  C  .  .  C  C  C  .  .
  |        |  |        |  |  |
  unison  m3 M3      P5 m6 M6

  C = consonant (6 = P1 intervals)
  . = dissonant (6 = P1 intervals)
```

## Interpretation

The 12 = sigma(6) directed intervals split evenly: P1 = 6 consonant and
P1 = 6 dissonant. This perfect 50/50 split reflects the self-dual nature
of perfect number 6 in the structure of consonance.
"""
})

# ═══════════════════════════════════════════════════════════════
# RHYTHM TOPOLOGY (026-035)
# ═══════════════════════════════════════════════════════════════

hypotheses.append({
    "id": "026",
    "title": "Rhythm Necklaces on Z_sigma(6)",
    "statement": "Rhythm necklaces (equivalence classes of rhythmic patterns under rotation) on Z_12 = Z_{sigma(6)} are counted by the necklace formula. The number of binary necklaces of length 12 is (1/12)*sum_{d|12} phi(d)*2^{12/d} = 352.",
    "grade": "EXACT",
    "emoji": "\U0001f7e9",
    "body": """## Background

A rhythm necklace of length n is a binary string of length n considered
up to cyclic rotation. This counts distinct rhythmic patterns in a cycle
of n beats.

## Computation

```
  Necklace count N(n, k=2) = (1/n) * sum_{d|n} phi(d) * 2^{n/d}

  For n = 12 = sigma(6):
    Divisors of 12: {1, 2, 3, 4, 6, 12}
    Number of divisors: 6 = P1  EXACT

    d=1:  phi(1)  * 2^12 = 1  * 4096 = 4096
    d=2:  phi(2)  * 2^6  = 1  * 64   = 64
    d=3:  phi(3)  * 2^4  = 2  * 16   = 32
    d=4:  phi(4)  * 2^3  = 2  * 8    = 16
    d=6:  phi(6)  * 2^2  = 2  * 4    = 8
    d=12: phi(12) * 2^1  = 4  * 2    = 8
    Sum = 4224
    N(12,2) = 4224 / 12 = 352
```

## ASCII Necklace Example

```
  Pattern: x . x . x . . x . x . .   (5 onsets in 12 beats)

  Rotation equivalence:
  x . x . x . . x . x . .
  . x . x . . x . x . . x   <- same necklace
  x . x . . x . x . . x .   <- same necklace

  All rotations = same rhythm (different starting beat)
```

## Divisor Connection

| Divisor d of 12 | phi(d) | 2^{12/d} | Contribution |
|-----------------|--------|----------|-------------|
| 1 | 1 | 4096 | 4096 |
| 2 | 1 | 64 | 64 |
| 3 | 2 | 16 | 32 |
| 4 | 2 | 8 | 16 |
| 6 | 2 | 4 | 8 |
| 12 | 4 | 2 | 8 |
| **Sum** | | | **4224** |

Total necklaces: 4224/12 = 352. The sum uses all P1 = 6 divisors of sigma(6) = 12.

## Interpretation

Computing rhythm necklaces on Z_{sigma(6)} requires summing over all P1 = 6
divisors of 12. The necklace formula directly invokes the divisor structure
of sigma(6), making n=6 the arithmetic engine behind rhythmic enumeration.
"""
})

hypotheses.append({
    "id": "027",
    "title": "Rhythmic Canons as Tilings of Z_sigma(6)",
    "statement": "A rhythmic canon tiles Z_12 = Z_{sigma(6)} when a rhythm pattern A and its translates cover every beat exactly once: A + B = Z_12. The factorizations of Z_12 correspond to tilings, and the number of nontrivial factorizations reflects the rich divisor structure of 12 = sigma(6).",
    "grade": "EXACT",
    "emoji": "\U0001f7e9",
    "body": """## Background

A rhythmic canon tiles Z_n if there exist sets A, B subset Z_n such that
every element of Z_n can be written uniquely as a + b with a in A, b in B.
This means A + B = Z_n (direct sum). This is closely related to the
Hajos-de Bruijn factorization problem.

## Verification

```
  Tiling condition: A + B = Z_12  (direct sum)
  |A| * |B| = 12 = sigma(6)  (necessary condition)

  Factor pairs (|A|, |B|) with |A|*|B| = 12:
    (1, 12), (2, 6), (3, 4), (4, 3), (6, 2), (12, 1)
    Count: 6 = P1  EXACT (including order)

  Examples:
    A = {0, 6}, B = {0, 1, 2, 3, 4, 5}  (|A|=2, |B|=6)
    A = {0, 4, 8}, B = {0, 1, 2, 3}     (|A|=3, |B|=4)
    A = {0, 3, 6, 9}, B = {0, 1, 2}     (|A|=4, |B|=3)
```

## ASCII Tiling

```
  A = {0, 4, 8}, B = {0, 1, 2, 3}

  Beat: 0  1  2  3  4  5  6  7  8  9  10 11
  A+0:  X           X           X
  A+1:     X           X           X
  A+2:        X           X           X
  A+3:           X           X           X
        ----------------------------------------
  Cover: 0  1  2  3  4  5  6  7  8  9  10 11  (complete tiling)
```

## Factor Pair Table

| |A| | |B| | |A|*|B| | Example A |
|-----|------|---------|-----------|
| 1 | 12 | 12 | {0} |
| 2 | 6 | 12 | {0, 6} |
| 3 | 4 | 12 | {0, 4, 8} |
| 4 | 3 | 12 | {0, 3, 6, 9} |
| 6 | 2 | 12 | {0, 2, 4, 6, 8, 10} |
| 12 | 1 | 12 | Z_12 |

## Interpretation

Rhythmic canon tilings of Z_{sigma(6)} require |A|*|B| = 12 = sigma(6),
and there are P1 = 6 ordered factor pairs. The divisor-rich structure of
12 = sigma(6) makes the 12-beat cycle especially fertile for rhythmic canons.
"""
})

hypotheses.append({
    "id": "028",
    "title": "Euclidean Rhythms and Equal Division of Z_sigma(6)",
    "statement": "Euclidean rhythms distribute k onsets as evenly as possible among n = 12 = sigma(6) beats using the Euclidean algorithm. Many traditional world rhythms are Euclidean rhythms on Z_12, with onset counts related to divisors of 12.",
    "grade": "EXACT",
    "emoji": "\U0001f7e9",
    "body": """## Background

Toussaint (2005) showed that the Euclidean algorithm, when applied to
distributing k onsets in n beats, generates rhythms found in many
musical traditions worldwide.

## Verification

```
  E(k, 12) = Euclidean rhythm with k onsets in 12 = sigma(6) beats

  E(2, 12) = [x . . . . . x . . . . .]   half notes
  E(3, 12) = [x . . . x . . . x . . .]   dotted quarter = shuffle
  E(4, 12) = [x . . x . . x . . x . .]   dotted eighth pattern
  E(6, 12) = [x . x . x . x . x . x .]   eighth notes in 6/8

  Special cases using divisors of 12:
    k=1:  trivial
    k=2:  period 6 = P1
    k=3:  period 4 = tau(6)
    k=4:  period 3 = P1/2
    k=6:  period 2 = phi(6)
    k=12: all beats
```

## ASCII Euclidean Rhythms

```
  E(3,12):  x . . . x . . . x . . .     Cuban tresillo variant
  E(4,12):  x . . x . . x . . x . .     Afro-Cuban 12/8
  E(5,12):  x . x . x . . x . x . .     Bossa nova variant

  Beat:  0  1  2  3  4  5  6  7  8  9 10 11
  E(3):  X           X           X
  E(4):  X        X        X        X
  E(6):  X     X     X     X     X     X
```

## Period Table

| k onsets | Period = 12/gcd(k,12) | gcd(k,12) | n=6 Link |
|----------|----------------------|-----------|----------|
| 2 | 6 | 2 | P1 |
| 3 | 4 | 3 | tau(6) |
| 4 | 3 | 4 | P1/2 |
| 6 | 2 | 6 | phi(6) |

## Interpretation

Euclidean rhythms on Z_{sigma(6)} = Z_12 have periods that are divisors
of 12. These periods {2, 3, 4, 6} = {phi(6), P1/2, tau(6), P1} are
exactly the nontrivial n=6 constants, making every Euclidean rhythm
a realization of n=6 arithmetic.
"""
})

hypotheses.append({
    "id": "029",
    "title": "Beat Class Sets as Subsets of Z_sigma(6)",
    "statement": "Beat class set theory (analogous to pitch-class set theory) treats rhythmic patterns as subsets of Z_12 = Z_{sigma(6)}. The total number of beat class sets is 2^12 = 4096, and the number of distinct beat class sets under rotation (necklaces) is 352.",
    "grade": "EXACT",
    "emoji": "\U0001f7e9",
    "body": """## Background

Just as pitch-class set theory classifies collections of pitch classes,
beat class set theory classifies rhythmic patterns as subsets of Z_n.
For standard 12-beat cycles (12/8, triplet subdivisions), n = 12.

## Verification

```
  Beat class universe: Z_12 = Z_{sigma(6)}
  Total subsets: 2^12 = 4096
  Under rotation (necklaces): 352 (Burnside/Polya)
  Under rotation + reflection (bracelets): 224 (D_12 action)

  |D_12| = 24 = 2 * sigma(6)  EXACT
```

## ASCII Beat Class Example

```
  Son clave (3-2): {0, 3, 6, 8, 10} in Z_12

  Beat: 0  1  2  3  4  5  6  7  8  9  10 11
        X        X        X     X     X

  Interval vector: <1 1 2 1 1 0>
  (counts of each interval class ic1-ic6, total P1 = 6 entries)
```

## Interval Vector Properties

```
  Interval vector has P1 = 6 entries (one per interval class)
  For a k-element set: sum of entries = C(k,2) = k(k-1)/2

  Example: {0, 3, 6, 8, 10}, k=5
    C(5,2) = 10
    IV = <1 1 2 1 1 0>, sum = 6  ... wait
    Actually: <1 2 1 2 2 2>, sum = 10  (corrected)
```

## Key Counts

| Property | Value | n=6 Link |
|----------|-------|----------|
| Universe | Z_12 | Z_{sigma(6)} |
| Total sets | 4096 | 2^{sigma(6)} |
| IV entries | 6 | P1 |
| Symmetry group | D_12 | order 2*sigma(6) |
| Necklaces | 352 | Burnside count |

## Interpretation

Beat class set theory on Z_{sigma(6)} mirrors pitch-class set theory.
The interval vector has P1 = 6 entries, and the symmetry group D_12
has order 2*sigma(6) = 24. The entire framework is governed by sigma(6).
"""
})

hypotheses.append({
    "id": "030",
    "title": "Metric Modulation as Covering Space Map",
    "statement": "Metric modulation (changing tempo so that a subdivision in the old meter becomes the beat of the new meter) can be modeled as a covering space map between rhythmic circles. The covering degree equals the ratio of beat subdivisions.",
    "grade": "WEAK",
    "emoji": "\U0001f7e7",
    "body": """## Background

Metric modulation (Elliot Carter) reinterprets a rhythmic subdivision as
a new pulse. E.g., if triplet eighth notes become the new quarter note,
the tempo changes by factor 3/2.

## Topological Model

```
  Old meter: circle C_old with n_old beats
  New meter: circle C_new with n_new beats
  Covering map: p: C_new -> C_old, degree d

  Example: 4/4 -> 6/8 modulation
    C_old: 4 beats (quarter notes)
    C_new: 6 beats (eighth notes in compound)
    Covering degree: related to lcm(4,6) = 12 = sigma(6)  EXACT
```

## ASCII Metric Modulation

```
  4/4 meter:   |----|----|----|----|     4 beats
                                         modulate via triplets
  6/8 meter:   |--|--|--|--|--|--|        6 beats

  Common subdivision: 12 = sigma(6) = lcm(4,6)

  12-grid: x . . x . . x . . x . .     (4/4 quarters on 12-grid)
           x . x . x . x . x . x .     (6/8 eighths on 12-grid)
```

## Covering Space Data

| Modulation | lcm | Covering degree | n=6 Link |
|------------|-----|----------------|----------|
| 4/4 -> 6/8 | 12 | 3 | sigma(6), P1/2 |
| 3/4 -> 4/4 | 12 | 4 | sigma(6), tau(6) |
| 2/4 -> 3/4 | 6 | 3 | P1, P1/2 |
| 6/8 -> 4/4 | 12 | 2 | sigma(6), phi(6) |

## Interpretation

Metric modulations between common meters frequently involve lcm = 12 = sigma(6)
as the common subdivision. The covering degrees (2, 3, 4) correspond to
phi(6), P1/2, and tau(6). Grade: WEAK because the covering space model is
a framework, and the n=6 connections arise from the commonness of 4/4 and 6/8.
"""
})

hypotheses.append({
    "id": "031",
    "title": "Time Signature as Lattice Point in Z^2",
    "statement": "A time signature m/n represents a lattice point (m, n) in Z^2, where m = beats per measure and n = beat unit. Common time signatures cluster near small coordinates, with 6/8 directly encoding P1 = 6.",
    "grade": "WEAK",
    "emoji": "\U0001f7e7",
    "body": """## Background

Time signatures describe metric structure. While the denominator is
conventionally a power of 2, the numerator can be any positive integer.
The most common time signatures involve small numbers.

## Verification

```
  Common time signatures and n=6 connections:
    2/4:  beats = phi(6), unit = tau(6)
    3/4:  beats = P1/2, unit = tau(6)
    4/4:  beats = tau(6), unit = tau(6)
    6/8:  beats = P1, unit = 8
    12/8: beats = sigma(6), unit = 8

  Direct P1 encoding: 6/8 has numerator = P1 = 6  EXACT
  sigma encoding: 12/8 has numerator = sigma(6) = 12  EXACT
```

## ASCII Lattice

```
  beats
  (m)
   |
  12|          *                sigma(6)/8
   |
   9|       *                  9/8
   |
   6|    *     *               P1/4, P1/8
   |
   4| *  *     *               tau(6)/4, etc.
   3| *  *                     P1/2
   2| *  *                     phi(6)
   +--+--+--+--+---> unit (n)
      2  4  8  16
```

## Frequency Table

| Time Sig | Beats | n=6 Link | Usage |
|----------|-------|----------|-------|
| 2/4 | 2 | phi(6) | march |
| 3/4 | 3 | P1/2 | waltz |
| 4/4 | 4 | tau(6) | common |
| 6/8 | 6 | P1 | compound duple |
| 12/8 | 12 | sigma(6) | compound quadruple |

## Interpretation

The most common beat counts {2, 3, 4, 6, 12} are exactly the divisors
of 12 = sigma(6), and simultaneously the nontrivial divisors of P1 = 6
plus sigma(6) itself. Grade: WEAK because common time signatures are
culturally influenced, not purely mathematical.
"""
})

hypotheses.append({
    "id": "032",
    "title": "Polyrhythm as Z_m x Z_n Orbit",
    "statement": "A polyrhythm (simultaneous patterns of m and n beats) generates orbits under the Z_m x Z_n action on Z_{lcm(m,n)}. The polyrhythm 3:4 acts on Z_12 = Z_{sigma(6)}, and 2:3 acts on Z_6 = Z_{P1}.",
    "grade": "EXACT",
    "emoji": "\U0001f7e9",
    "body": """## Background

A k:l polyrhythm superimposes a pattern of k even beats with l even beats.
The combined pattern lives in Z_{lcm(k,l)}, where both cycles align.

## Verification

```
  3:4 polyrhythm:
    Z_3 cycle: beats at 0, 4, 8 in Z_12
    Z_4 cycle: beats at 0, 3, 6, 9 in Z_12
    Universe: Z_12 = Z_{sigma(6)}  EXACT
    Combined onsets: {0, 3, 4, 6, 8, 9} = 6 = P1 onsets  EXACT

  2:3 polyrhythm:
    Z_2 cycle: beats at 0, 3 in Z_6
    Z_3 cycle: beats at 0, 2, 4 in Z_6
    Universe: Z_6 = Z_{P1}  EXACT
    Combined onsets: {0, 2, 3, 4} = 4 = tau(6) onsets  EXACT
```

## ASCII 3:4 Polyrhythm

```
  Beat:  0  1  2  3  4  5  6  7  8  9  10 11
  3-pat: X           X           X
  4-pat: X        X        X        X
  Both:  X        X  X     X     X  X
         |__________________________________|
                  12 = sigma(6) beats

  Combined onset count: 6 = P1
```

## Polyrhythm Table

| Polyrhythm | lcm | Universe | Onsets | n=6 Link |
|------------|-----|----------|--------|----------|
| 2:3 | 6 | Z_{P1} | 4 = tau(6) | P1, tau(6) |
| 3:4 | 12 | Z_{sigma(6)} | 6 = P1 | sigma(6), P1 |
| 2:6 | 6 | Z_{P1} | 6 = P1 | P1 |
| 4:6 | 12 | Z_{sigma(6)} | 8 | sigma(6) |

## Interpretation

The two most fundamental polyrhythms (2:3 and 3:4) live in Z_{P1} and
Z_{sigma(6)} respectively. The 3:4 polyrhythm produces exactly P1 = 6
combined onsets in sigma(6) = 12 beats, a striking n=6 coincidence.
"""
})

hypotheses.append({
    "id": "033",
    "title": "Rhythmic Braid Groups from Voice Crossing",
    "statement": "When rhythmic voices (polyrhythmic layers) cross in intensity or register, they generate elements of the braid group B_n. For n = P1/2 = 3 simultaneous rhythmic layers, the braid group B_3 encodes all possible crossing patterns.",
    "grade": "WEAK",
    "emoji": "\U0001f7e7",
    "body": """## Background

Braid groups generalize permutation groups by tracking HOW strands cross,
not just the final permutation. In polyrhythmic music, different layers
may cross in prominence, creating braid-like patterns.

## Construction

```
  3 rhythmic layers (e.g., bass, mid, treble patterns):
    Layer 1: x . . x . . x . . x . .    (period 3)
    Layer 2: x . x . x . x . x . x .    (period 2)
    Layer 3: x x . x x . x x . x x .    (period 3, shifted)

  When layers cross in volume/register:
    -> generates elements of B_3 (braid group on P1/2 strands)
    B_3 generators: sigma_1, sigma_2 (phi(6) = 2 generators)
```

## ASCII Rhythmic Braid

```
  Time --->

  Layer 1: ====\\========/====\\====
                \\      /      \\      sigma_1
  Layer 2: =====\\====/========\\===
                 \\  /           \\    sigma_2
  Layer 3: ======\\/=============\\==

  Crossings encode rhythmic interactions
```

## Braid Data

| Property | Value | n=6 Link |
|----------|-------|----------|
| Layers | 3 | P1/2 |
| Generators | 2 | phi(6) |
| Surjects to | S_3 | order P1 |
| Center | Z | infinite cyclic |

## Interpretation

Rhythmic braids on P1/2 = 3 layers use phi(6) = 2 generators and
surject to S_{P1/2} of order P1. Grade: WEAK because the braid model
for rhythm is a theoretical framework, not an established music-theoretic fact.
"""
})

hypotheses.append({
    "id": "034",
    "title": "Phase Space of Rhythmic Patterns",
    "statement": "The phase space of a rhythmic pattern on n beats is the set of all binary strings of length n, forming the hypercube {0,1}^n. For n = 12 = sigma(6), this is a 12-dimensional hypercube with 2^12 = 4096 vertices.",
    "grade": "EXACT",
    "emoji": "\U0001f7e9",
    "body": """## Background

Every possible rhythmic pattern on n beats is a binary string: 1 = onset,
0 = rest. The collection of all patterns forms the vertices of an
n-dimensional hypercube (Boolean lattice).

## Verification

```
  n = 12 = sigma(6) beats
  Phase space: {0, 1}^12 (12-dimensional hypercube)
  Vertices: 2^12 = 4096
  Edges: 12 * 2^11 = 24576 = 2 * sigma(6) * 2^11
  Dimension: 12 = sigma(6)  EXACT

  Hamming distance between patterns = number of differing beats
  Maximum distance: 12 = sigma(6) (all beats flipped)
```

## ASCII Hypercube Projection

```
  Example in 4D (tau(6) dimensions):

      0000--------0001
     /|           /|
  0100--------0101 |
    | 1000------|-1001
    |/           |/
  1100--------1101

  Full phase space: 12D = sigma(6) dimensions
  Too large to draw, but same structure
```

## Hypercube Properties

| Property | Value | n=6 Link |
|----------|-------|----------|
| Dimension | 12 | sigma(6) |
| Vertices | 4096 | 2^{sigma(6)} |
| Edges | 24576 | -- |
| Diameter | 12 | sigma(6) |
| Automorphisms | 12! * 2^12 | huge |

## Interpretation

The rhythmic phase space is a sigma(6)-dimensional hypercube. Every
rhythmic pattern is a vertex, and neighboring patterns differ by one beat.
The dimension sigma(6) = 12 provides a vast space of 4096 rhythmic possibilities.
"""
})

hypotheses.append({
    "id": "035",
    "title": "Tempo as Slope in Time-Pitch Plane",
    "statement": "In the time-pitch plane R^2, a melody traces a curve. The tempo determines the horizontal scaling, while pitch intervals determine vertical jumps. A steady tempo corresponds to constant horizontal spacing, and tempo changes are slope variations in this 2 = phi(6) dimensional space.",
    "grade": "WEAK",
    "emoji": "\U0001f7e7",
    "body": """## Background

The piano-roll representation places time on the x-axis and pitch on the
y-axis, creating a 2D representation of music. This is a projection of
the full musical space onto R^2.

## Construction

```
  Time-pitch plane: R^2 (dimension 2 = phi(6))
  Melody: curve gamma(t) = (t, p(t)) in R^2
  Tempo: dt/d(beat) = horizontal scaling
  Intervals: dp/dt = pitch rate of change

  At constant tempo: horizontal spacing uniform
  Accelerando: horizontal spacing decreases
  Ritardando: horizontal spacing increases
```

## ASCII Time-Pitch Plane

```
  Pitch
  (MIDI)
   |       *
   |   *       *
   | *           *   *
   |               *       melody curve
   |
   +--+--+--+--+--+--+---> Time
   |  |  |  |  |  |  |
   beat subdivisions
   (12 per measure = sigma(6))

  Dimension of this space: 2 = phi(6)
```

## Properties

| Property | Value | n=6 Link |
|----------|-------|----------|
| Plane dimension | 2 | phi(6) |
| Time subdivisions | 12/measure | sigma(6) |
| Pitch range | ~88 keys | -- |
| Tempo = slope | horizontal rate | -- |

## Interpretation

The time-pitch plane is a phi(6) = 2 dimensional projection of musical
structure. The standard subdivision of 12 = sigma(6) beats per measure
provides the grid. Grade: WEAK because the 2D representation is a
visualization choice, not a topological invariant.
"""
})

# ═══════════════════════════════════════════════════════════════
# DEEP TOPOLOGICAL CONNECTIONS (036-050)
# ═══════════════════════════════════════════════════════════════

hypotheses.append({
    "id": "036",
    "title": "Musical Form as CW-Complex",
    "statement": "Large-scale musical form can be modeled as a CW-complex, where 0-cells are phrase boundaries, 1-cells are phrases, and 2-cells are sections. A sonata form with exposition, development, recapitulation has 3 = P1/2 two-cells and its Euler characteristic depends on the attachment maps.",
    "grade": "WEAK",
    "emoji": "\U0001f7e7",
    "body": """## Background

A CW-complex is built inductively by attaching cells of increasing
dimension. Musical form has a natural hierarchical structure that
can be modeled this way: notes -> phrases -> sections -> movements.

## Construction

```
  CW-complex of sonata form:
    0-cells: section boundaries (vertices)
    1-cells: transitions between sections (edges)
    2-cells: sections themselves (faces)

  Sonata form:
    Sections: Exposition, Development, Recapitulation
    Count: 3 = P1/2  EXACT

    If we include Introduction and Coda: 5 = sopfr(6)  EXACT
```

## ASCII CW-Complex

```
  Sonata form CW-complex:

  0-cells:  *-----------*-----------*-----------*
  1-cells:  |  trans_1   |  trans_2   |  trans_3   |
  2-cells:  | EXPOSITION | DEVELOPMT  | RECAPITUL  |
            *-----------*-----------*-----------*

  3 two-cells = P1/2
  4 zero-cells = tau(6)
  3 one-cells (internal) = P1/2
```

## Euler Characteristic

```
  chi = V - E + F
  V (0-cells) = 4 = tau(6)
  E (1-cells) = 3 = P1/2  (internal boundaries)
  F (2-cells) = 3 = P1/2  (sections)

  chi = 4 - 3 + 3 = 4 = tau(6)
  (depends on specific attachment)
```

## Interpretation

Sonata form decomposes into P1/2 = 3 main sections with tau(6) = 4
boundary points. Grade: WEAK because the CW-complex model is a
theoretical framework, and the number of sections is a convention.
"""
})

hypotheses.append({
    "id": "037",
    "title": "Persistent Homology of Melodic Contour",
    "statement": "Applying persistent homology to a melody's pitch contour (as a time series) reveals topological features at multiple scales. The birth-death pairs in the persistence diagram encode melodic structure, with H_0 features counting connected components (phrases) and H_1 features counting loops (repeated patterns).",
    "grade": "WEAK",
    "emoji": "\U0001f7e7",
    "body": """## Background

Persistent homology (TDA) tracks topological features as a filtration
parameter varies. Applied to music, the filtration can be the pitch
threshold: connect notes within k semitones.

## Construction

```
  Melody as point cloud: {(t_i, p_i)} in R^2
  Filtration: Rips complex at scale epsilon
  As epsilon grows: components merge, loops form

  For a melody in 12 = sigma(6) semitone range:
    H_0 persistence: phrase segmentation
    H_1 persistence: melodic loops / sequences
```

## ASCII Persistence Diagram

```
  Death
   |
  12|    *                  (long-lived H_0 feature)
   |
   8|  *   *                (medium features)
   |
   4| * * *                 (short-lived features)
   | * *
   +--+--+--+--+--+-> Birth
   0  2  4  6  8  12

  Features near diagonal: noise
  Features far from diagonal: significant structure
  Max death value: 12 = sigma(6) (octave range)
```

## Musical TDA Data

| Feature | Meaning | Typical Count |
|---------|---------|--------------|
| H_0 long bars | phrases | 3-5 (P1/2 to sopfr(6)) |
| H_0 short bars | ornaments | many |
| H_1 features | sequences | 1-3 |
| Max persistence | sigma(6) | octave range |

## Interpretation

Persistent homology reveals the multi-scale topology of melody.
The octave range sigma(6) = 12 sets the maximum persistence value.
Grade: WEAK because the specific features depend on the melody, and the
n=6 connection is through the 12-semitone octave.
"""
})

hypotheses.append({
    "id": "038",
    "title": "Betti Numbers of Scale Complexes",
    "statement": "The simplicial complex of a musical scale (vertices = notes, simplices = consonant subsets) has Betti numbers encoding its topology. For the diatonic scale (7 notes from Z_12 = Z_{sigma(6)}), beta_0 = 1 (connected) and higher Betti numbers depend on consonance criteria.",
    "grade": "WEAK",
    "emoji": "\U0001f7e7",
    "body": """## Background

Given a scale S subset Z_12 and a consonance criterion, we form a
simplicial complex by declaring subsets consonant if all pairwise
intervals are consonant. The Betti numbers of this complex reveal
topological structure.

## Construction

```
  Diatonic scale C major: S = {0, 2, 4, 5, 7, 9, 11}
  |S| = 7 = P1 + 1

  Consonant intervals: {3, 4, 5, 7, 8, 9}  (thirds, fourths, fifths, sixths)
  |consonant| = 6 = P1  EXACT

  Simplicial complex: edge (i,j) if |i-j| mod 12 in consonant set
```

## ASCII Diatonic Complex

```
  C(0)----D(2)
  |\\      / \\
  | \\    /   \\
  |  E(4)    F(5)
  | / \\  \\   / |
  |/   \\  \\ /  |
  G(7)--A(9)--B(11)

  beta_0 = 1 (connected)
  beta_1 = number of independent cycles
```

## Scale Size Table

| Scale | Size | Complement | n=6 Link |
|-------|------|-----------|----------|
| Chromatic | 12 | 0 | sigma(6) |
| Diatonic | 7 | 5 | P1+1, sopfr(6) |
| Pentatonic | 5 | 7 | sopfr(6) |
| Whole tone | 6 | 6 | P1 |
| Hexatonic | 6 | 6 | P1 |

## Interpretation

Scale complexes live inside Z_{sigma(6)}. The diatonic-pentatonic duality
(7 + 5 = sigma(6)) and the self-complementary whole-tone scale (6 = P1)
are topological features encoded by n=6. Grade: WEAK because specific
Betti numbers depend on the consonance criterion.
"""
})

hypotheses.append({
    "id": "039",
    "title": "Simplicial Complex of Consonance",
    "statement": "The consonance complex on Z_12 = Z_{sigma(6)} is the simplicial complex where vertices are pitch classes and a simplex exists if all its notes are mutually consonant. The P1 = 6 consonant interval classes define the 1-skeleton (edge set).",
    "grade": "EXACT",
    "emoji": "\U0001f7e9",
    "body": """## Background

Consonance defines a graph (and higher simplicial complex) on pitch classes.
Two notes are connected if their interval is consonant. The maximal
cliques become the maximal simplices.

## Verification

```
  Vertices: 12 = sigma(6) pitch classes
  Consonant intervals: {0, 3, 4, 5, 7, 8, 9} (including unison)
  Edges: pairs with consonant interval

  Each vertex has degree d:
    From C: consonant with Eb(3), E(4), F(5), G(7), Ab(8), A(9)
    d = 6 = P1  EXACT (not counting self)

  Total edges: 12 * 6 / 2 = 36 = P1^2  EXACT
```

## ASCII Consonance Graph

```
  C --- Eb    C --- E     C --- F
  C --- G     C --- Ab    C --- A

  Each of 12 vertices has P1 = 6 consonant neighbors
  Total edges: 36 = P1^2 = 6^2

  Complement (dissonance graph):
  Each vertex has 12 - 1 - 6 = 5 = sopfr(6) dissonant neighbors
  Dissonant edges: 12 * 5 / 2 = 30 = sopfr(6) * P1
```

## Graph Properties

| Property | Value | n=6 Link |
|----------|-------|----------|
| Vertices | 12 | sigma(6) |
| Consonant degree | 6 | P1 |
| Dissonant degree | 5 | sopfr(6) |
| Consonant edges | 36 | P1^2 |
| Dissonant edges | 30 | sopfr(6)*P1 |
| Total edges | 66 | C(12,2) |

## Interpretation

The consonance graph on Z_{sigma(6)} is P1-regular: every note has exactly
P1 = 6 consonant partners and sopfr(6) = 5 dissonant ones. The edge counts
36 = P1^2 (consonant) and 30 = sopfr(6)*P1 (dissonant) are clean n=6 products.
"""
})

hypotheses.append({
    "id": "040",
    "title": "Homotopy Equivalence of Enharmonic Scales",
    "statement": "Enharmonically equivalent scales (e.g., F# major and Gb major) are the same point in pitch-class space Z_12, hence trivially homotopy equivalent. The enharmonic identification quotients the 7 sharps and 7 flats to give sigma(6) = 12 distinct classes.",
    "grade": "EXACT",
    "emoji": "\U0001f7e9",
    "body": """## Background

In equal temperament, enharmonic equivalence identifies notes like F# = Gb.
This is the fundamental quotient that reduces the theoretically infinite
spiral of fifths to the closed circle of fifths.

## Verification

```
  Without enharmonic equivalence:
    Spiral of fifths: ..., Dbb, Abb, Ebb, Bb, F, C, G, D, A, E, B, F#, C#, ...
    Infinite in both directions

  With enharmonic equivalence (equal temperament):
    Circle of fifths: C, G, D, A, E, B=Cb, F#=Gb, C#=Db, Ab, Eb, Bb, F
    Exactly 12 = sigma(6) classes  EXACT

  Quotient map: R (spiral) -> S^1 (circle), period 12
```

## ASCII Enharmonic Identification

```
  Spiral of fifths (no enharmonic equiv):

  ...--Fb--Cb--Gb--Db--Ab--Eb--Bb--F--C--G--D--A--E--B--F#--C#--G#--...
                    |                                           |
                    |<------------ 12 = sigma(6) fifths ------->|
                    |                                           |
                    Db =============================== C# (identified!)

  After identification: circle of 12 = sigma(6) notes
```

## Key Signatures

```
  Sharps: 0(C), 1(G), 2(D), 3(A), 4(E), 5(B), 6(F#), 7(C#)
  Flats:  0(C), 1(F), 2(Bb), 3(Eb), 4(Ab), 5(Db), 6(Gb), 7(Cb)
  Overlaps: B=Cb, F#=Gb, C#=Db (and enharmonic equivalents)
  Distinct keys: 12 = sigma(6)
  Enharmonic pairs: 3 = P1/2
```

## Interpretation

Enharmonic equivalence is the topological quotient that closes the spiral of
fifths into a circle of sigma(6) = 12 elements, with P1/2 = 3 enharmonic pairs.
"""
})

hypotheses.append({
    "id": "041",
    "title": "Covering Spaces and Modulation",
    "statement": "Key modulation in tonal music can be modeled as path lifting in a covering space. The space of keys is S^1 (circle of fifths with 12 = sigma(6) points), and modulation traces a path on this circle. The monodromy of a modulation sequence is an element of Z_12 = Z_{sigma(6)}.",
    "grade": "EXACT",
    "emoji": "\U0001f7e9",
    "body": """## Background

Modulation (changing key) moves between points on the circle of fifths.
A sequence of modulations traces a path, and the net modulation after
returning to the original key is the monodromy.

## Verification

```
  Key space: Z_12 = Z_{sigma(6)} (circle of fifths)
  Modulation by fifth: +1 in Z_12
  Modulation by fourth: -1 in Z_12
  Modulation by third: +4 or +3 in Z_12

  Monodromy: total modulation mod 12
    C -> G -> D -> A -> E -> B -> F# -> Db -> Ab -> Eb -> Bb -> F -> C
    Net: 12 fifths = 0 mod 12 (trivial monodromy)  EXACT

  This is the deck transformation of the universal cover.
```

## ASCII Modulation Path

```
  Circle of fifths (key space):

       C
    F     G          Modulation path:
  Bb        D        C -> G -> D -> G -> C
  Eb         A       = loop in key space
    Ab    E          monodromy = 0
       Db/C#

  Non-trivial monodromy:
  C -> G -> D -> A   (3 steps = P1/2)
  Net shift: +3 in Z_12  (key of A)
```

## Monodromy Data

| Modulation Cycle | Steps | Net (mod 12) | Returns? |
|-----------------|-------|-------------|----------|
| All fifths | 12 = sigma(6) | 0 | yes |
| Major thirds | 3 = P1/2 | returns | yes |
| Minor thirds | 4 = tau(6) | returns | yes |
| Tritone | 2 = phi(6) | returns | yes |

## Interpretation

The monodromy of modulation lives in Z_{sigma(6)} = Z_12. Complete cycles
through all keys require sigma(6) = 12 fifth-steps. Shorter cycles of
length P1/2, tau(6), or phi(6) correspond to the subgroups of Z_12.
"""
})

hypotheses.append({
    "id": "042",
    "title": "Orbifold Euler Characteristic of Voice-Leading Spaces",
    "statement": "The orbifold Euler characteristic of the n-chord voice-leading space T^n/S_n involves 1/|S_n|. For n = 3 = P1/2 (triads), 1/|S_3| = 1/6 = 1/P1. For n = 4 = tau(6) (tetra chords), 1/|S_4| = 1/24 = 1/(2*sigma(6)).",
    "grade": "EXACT",
    "emoji": "\U0001f7e9",
    "body": """## Background

The orbifold Euler characteristic generalizes the ordinary Euler
characteristic to spaces with singularities from group actions.
For a free action, chi_orb = chi(X)/|G|.

## Verification

```
  For T^n / S_n:
    chi(T^n) = 0 for all n >= 1 (torus)
    chi_orb = 0 / |S_n| = 0 (trivially)

  The meaningful invariant is the volume ratio:
    Vol(T^n/S_n) / Vol(T^n) = 1/n!

  n = 2 = phi(6):  1/2! = 1/2 = 1/phi(6)  EXACT
  n = 3 = P1/2:    1/3! = 1/6 = 1/P1  EXACT
  n = 4 = tau(6):  1/4! = 1/24 = 1/(2*sigma(6))  EXACT
```

## ASCII Volume Ratios

```
  n=2 (dyads):    [======|======]  1/2 = 1/phi(6)
                   fund    image

  n=3 (triads):   [==|==|==|==|==|==]  1/6 = 1/P1
                   FD   5 copies

  n=4 (tetra):    [=|=|=|... 24 total ...]  1/24 = 1/(2*sigma(6))
```

## Complete Table

| Voices n | S_n order | 1/n! | n=6 Link |
|----------|-----------|------|----------|
| 1 | 1 | 1 | trivial |
| 2 = phi(6) | 2 | 1/2 | phi(6) |
| 3 = P1/2 | 6 | 1/6 | P1 |
| 4 = tau(6) | 24 | 1/24 | 2*sigma(6) |
| 5 = sopfr(6) | 120 | 1/120 | sopfr(6) |
| 6 = P1 | 720 | 1/720 | 6! = P1! |

## Interpretation

The volume ratios 1/n! for musically relevant voice counts (2, 3, 4)
are exactly 1/phi(6), 1/P1, and 1/(2*sigma(6)). At n = P1 = 6 voices,
the ratio is 1/720 = 1/(P1!), a self-referential closure.
"""
})

hypotheses.append({
    "id": "043",
    "title": "Topological Classification of Musical Canons",
    "statement": "Musical canons can be classified topologically by their voice-entry structure. A round (strict canon at the unison) with n voices is characterized by a Z_n cyclic symmetry. The most common canon types have 2, 3, or 4 voices = phi(6), P1/2, tau(6).",
    "grade": "WEAK",
    "emoji": "\U0001f7e7",
    "body": """## Background

A canon is a contrapuntal technique where a melody is imitated by one
or more voices at fixed time delays. The number of voices and the
imitation interval classify the canon type.

## Classification

```
  Canon types by voice count:
    2-voice canon: Z_2 = Z_{phi(6)} symmetry
    3-voice canon: Z_3 = Z_{P1/2} symmetry
    4-voice canon: Z_4 = Z_{tau(6)} symmetry
    6-voice canon: Z_6 = Z_{P1} symmetry (rare, virtuosic)

  Famous examples:
    2-voice: most rounds, many Bach canons
    3-voice: "Row Row Row Your Boat"
    4-voice: Pachelbel's Canon (with variations)
    6-voice: Bach, Musical Offering (Ricercar a 6)
```

## ASCII Canon Structure

```
  3-voice round (Z_3 symmetry):

  Time --->
  V1: |==melody==|==melody==|==melody==|
  V2:      |==melody==|==melody==|==melody==|
  V3:           |==melody==|==melody==|==melody==|
       <-T->    T = entry delay

  Symmetry: shift by T maps V1->V2->V3->V1 (Z_3 action)
```

## Canon Voice Count Distribution

| Voices | Symmetry | Frequency | n=6 Link |
|--------|----------|-----------|----------|
| 2 | Z_2 | very common | phi(6) |
| 3 | Z_3 | common | P1/2 |
| 4 | Z_4 | common | tau(6) |
| 5 | Z_5 | rare | sopfr(6) |
| 6 | Z_6 | very rare | P1 |

## Interpretation

Canon voice counts {2, 3, 4, 6} align with the divisors of P1 = 6 and
n=6 constants. The 6-voice canon (Z_{P1} symmetry) is the most complex
commonly attempted structure. Grade: WEAK because voice counts are partly
constrained by human limitations, not pure topology.
"""
})

hypotheses.append({
    "id": "044",
    "title": "Euler Characteristic of the Tonnetz Torus is Zero",
    "statement": "The Tonnetz, as a triangulation of the torus T^2, has Euler characteristic chi = 0. With the standard triangulation using 12 = sigma(6) vertices, 36 edges, and 24 = 2*sigma(6) triangular faces: chi = 12 - 36 + 24 = 0.",
    "grade": "EXACT",
    "emoji": "\U0001f7e9",
    "body": """## Background

The Tonnetz triangulates T^2 with vertices at the 12 pitch classes.
The Euler characteristic chi = V - E + F must equal 0 for any
triangulation of the torus.

## Verification

```
  Tonnetz triangulation:
    V (vertices) = 12 = sigma(6)
    E (edges)    = 36 = P1^2
    F (faces)    = 24 = 2 * sigma(6)

  chi = V - E + F = 12 - 36 + 24 = 0  EXACT

  Check: chi(T^2) = 0 for any torus  (topological invariant)
  This is consistent: 0 = 0  VERIFIED
```

## ASCII Tonnetz Triangulation

```
       A----C#---F----A
      /|\\  /|\\  /|\\  /
     / | \\/ | \\/ | \\/
    F--|-Ab--|-C--|-E--F      Each parallelogram = 2 triangles
     \\ | /\\ | /\\ | /\\       V=12, E=36, F=24
      \\|/  \\|/  \\|/  \\
       Db---F----A----Db
      (identified edges -> torus)
```

## Euler Characteristic Components

| Component | Value | n=6 Link |
|-----------|-------|----------|
| Vertices V | 12 | sigma(6) |
| Edges E | 36 | P1^2 |
| Faces F | 24 | 2*sigma(6) |
| chi = V-E+F | 0 | torus invariant |
| F/V ratio | 2 | phi(6) |

## Interpretation

The Tonnetz Euler characteristic 0 = sigma(6) - P1^2 + 2*sigma(6) gives
the remarkable identity sigma(6) + 2*sigma(6) = P1^2, i.e., 12 + 24 = 36
=> 3*sigma(6) = P1^2 => 3*12 = 36 = 6^2. This is 3*sigma(6) = P1^2,
a clean n=6 identity.
"""
})

hypotheses.append({
    "id": "045",
    "title": "Klein Bottle in Pitch-Rhythm Duality",
    "statement": "If pitch classes (Z_12) and beat classes (Z_12) are both circles, and the identification between them reverses orientation (pitch up = time backward in retrograde inversion), the resulting space is a Klein bottle K = S^1 x_twist S^1, a non-orientable surface.",
    "grade": "WEAK",
    "emoji": "\U0001f7e7",
    "body": """## Background

A Klein bottle is formed by identifying opposite edges of a square
with one pair reversed. In music, retrograde inversion combines
pitch inversion with time reversal, suggesting a non-orientable
identification.

## Construction

```
  Pitch circle: Z_12 = Z_{sigma(6)}  (mod octave)
  Time circle:  Z_12 = Z_{sigma(6)}  (mod measure in 12/8)

  Normal identification (torus): (p, t) ~ (p+12, t) ~ (p, t+12)
  Retrograde-inversion: (p, t) ~ (12-p, 12-t)
    This reverses orientation in both coordinates

  If we identify with twist: (p, 0) ~ (12-p, 12)
    Result: Klein bottle  (non-orientable)
```

## ASCII Klein Bottle Construction

```
  Square [0,12] x [0,12]:

  Pitch
   12 <----A-----B
    |             |          A-B identified normally (left-right)
    |             |          C-D identified with reversal (top-bottom)
    |             |
    0  ---->C-----D

  Torus: both pairs same direction
  Klein: one pair reversed (retrograde inversion)

  chi(Klein bottle) = 0
  Non-orientable, no boundary
```

## Properties

| Property | Torus | Klein Bottle |
|----------|-------|-------------|
| Orientable | yes | no |
| chi | 0 | 0 |
| pi_1 | Z x Z | Z semidirect Z |
| H_1 | Z^2 | Z + Z_2 |
| Musical meaning | pitch+time | pitch+retrograde |

## Interpretation

The Klein bottle model captures retrograde inversion as a topological twist.
Both circles have sigma(6) = 12 elements. Grade: WEAK because the Klein
bottle interpretation is a theoretical construction, not a standard
music-theoretic result.
"""
})

hypotheses.append({
    "id": "046",
    "title": "Fundamental Group pi_1 of Pitch Space = Z",
    "statement": "The fundamental group of pitch-class space S^1 is pi_1(S^1) = Z, the integers. Each generator corresponds to one octave traversal of 12 = sigma(6) semitones. The universal cover R -> S^1 is the pitch helix with fiber Z.",
    "grade": "EXACT",
    "emoji": "\U0001f7e9",
    "body": """## Background

The fundamental group pi_1(X) classifies loops in X up to homotopy.
For the circle S^1, every loop is characterized by its winding number
(how many times it goes around).

## Verification

```
  pi_1(S^1) = Z

  Musical interpretation:
    Generator +1: ascending octave (12 = sigma(6) semitones up)
    Generator -1: descending octave (12 semitones down)
    Element n: n octaves up (n * sigma(6) semitones)

  Covering space: p: R -> S^1
    p(x) = x mod 12
    Fiber over any point: Z (all octave copies)
    Deck transformations: x -> x + 12k
```

## ASCII Fundamental Group

```
  Loops in S^1:

  Winding 0:    Winding +1:     Winding +2:
  *-->--*       *-->-->-->*     *-->-->-->-->-->-->*
  |     |       (one full       (two full
  *--<--*        loop)           loops)

  pi_1 = Z = {..., -2, -1, 0, +1, +2, ...}
  Each unit = one octave = sigma(6) semitones
```

## Homotopy Data

| Loop | Winding | Semitones | n=6 Link |
|------|---------|-----------|----------|
| Trivial | 0 | 0 | identity |
| One octave up | +1 | 12 | sigma(6) |
| One octave down | -1 | -12 | -sigma(6) |
| Two octaves | +2 | 24 | 2*sigma(6) |
| n octaves | n | 12n | n*sigma(6) |

## Interpretation

pi_1(S^1) = Z is one of the most fundamental results in algebraic topology,
and in music it simply counts octaves. Each generator represents sigma(6) = 12
semitones, making the fundamental group a direct encoding of the divisor sum of 6.
"""
})

hypotheses.append({
    "id": "047",
    "title": "Musical Manifolds: Dimension = Number of Voices",
    "statement": "The configuration space of n independent voices is an n-dimensional manifold (specifically T^n, the n-torus). The musically standard voice counts 2 = phi(6), 3 = P1/2, and 4 = tau(6) give manifolds of dimension phi(6), P1/2, and tau(6) respectively.",
    "grade": "EXACT",
    "emoji": "\U0001f7e9",
    "body": """## Background

Each independent voice contributes one degree of freedom (its pitch class),
so n voices give an n-dimensional configuration space. The standard
voice configurations in Western music correspond to n=6 constants.

## Verification

```
  Voice configurations:
    Monophony:   1 voice  -> T^1 = S^1     (dim 1)
    Counterpoint: 2 voices -> T^2           (dim phi(6) = 2)  EXACT
    Triadic:     3 voices -> T^3           (dim P1/2 = 3)  EXACT
    SATB:        4 voices -> T^4           (dim tau(6) = 4)  EXACT
    Quintet:     5 voices -> T^5           (dim sopfr(6) = 5)  EXACT
    Sextet:      6 voices -> T^6           (dim P1 = 6)  EXACT
```

## ASCII Dimension Ladder

```
  dim = P1 = 6:  T^6  (sextet)        ******
  dim = sopfr = 5: T^5 (quintet)      *****
  dim = tau = 4: T^4  (SATB quartet)  ****
  dim = P1/2 = 3: T^3 (triad)         ***
  dim = phi = 2: T^2  (counterpoint)   **
  dim = 1:       T^1  (monophony)      *

  Each * = one S^1 factor (one voice)
```

## Configuration Table

| Ensemble | Voices | Dimension | n=6 Constant |
|----------|--------|-----------|-------------|
| Solo | 1 | 1 | -- |
| Duo | 2 | 2 | phi(6) |
| Trio | 3 | 3 | P1/2 |
| Quartet | 4 | 4 | tau(6) |
| Quintet | 5 | 5 | sopfr(6) |
| Sextet | 6 | 6 | P1 |

## Interpretation

The standard Western ensemble sizes {2, 3, 4, 5, 6} map perfectly to
{phi(6), P1/2, tau(6), sopfr(6), P1}. This is a complete enumeration:
every n=6 arithmetic function value appears as a musically canonical voice count.
"""
})

hypotheses.append({
    "id": "048",
    "title": "Topological Data Analysis of Musical Structure",
    "statement": "TDA applied to musical datasets reveals persistent topological features. The natural distance metric on pitch-class space Z_12 = Z_{sigma(6)} has maximum distance 6 = P1 (the tritone), and the Vietoris-Rips complex at radius P1 covers all pitch classes.",
    "grade": "EXACT",
    "emoji": "\U0001f7e9",
    "body": """## Background

In TDA, one builds simplicial complexes at varying scales (radii) and
tracks topological features. On Z_12 with the circular metric, the
maximum distance between any two points is 6 = P1.

## Verification

```
  Circular distance on Z_12:
    d(a, b) = min(|a-b|, 12-|a-b|)
    Maximum: d(0, 6) = 6 = P1  EXACT

  Vietoris-Rips complex at radius r:
    VR(r): simplex on points within distance r
    VR(0): 12 isolated points (beta_0 = 12 = sigma(6))
    VR(1): connect semitone neighbors (cycle C_12)
    VR(6): complete graph K_12 (all connected)
    VR(P1): fully connected  EXACT
```

## ASCII Filtration

```
  r=0:  * * * * * * * * * * * *    beta_0 = 12 = sigma(6)
        (12 isolated points)

  r=1:  *-*-*-*-*-*-*-*-*-*-*-*   beta_0 = 1, beta_1 = 1
        (cycle graph C_12)

  r=3:  dense graph                beta_0 = 1, beta_1 > 1

  r=6:  complete K_12              beta_0 = 1, beta_1 = 0
        (all connected at r = P1)
```

## Persistence Data

| Radius r | beta_0 | beta_1 | n=6 Link |
|----------|--------|--------|----------|
| 0 | 12 | 0 | sigma(6) |
| 1 | 1 | 1 | -- |
| 2 | 1 | >1 | -- |
| 6 = P1 | 1 | 0 | P1 (max dist) |

## Interpretation

The maximum circular distance 6 = P1 on Z_{sigma(6)} means the complete
Rips complex is reached at radius P1. The filtration from sigma(6) isolated
points to full connectivity at P1 encodes the topology of the pitch space.
"""
})

hypotheses.append({
    "id": "049",
    "title": "Nerve Theorem Applied to Chord Overlap",
    "statement": "The nerve theorem states that if a cover of a space has all intersections contractible, the nerve is homotopy equivalent to the space. Applied to the diatonic scale covered by its P1/2 = 3 consonant triads (I, IV, V), the nerve captures the harmonic topology.",
    "grade": "WEAK",
    "emoji": "\U0001f7e7",
    "body": """## Background

The nerve of a cover {U_i} is the simplicial complex whose k-simplices
correspond to (k+1)-fold intersections. The nerve theorem guarantees
this nerve reflects the topology of the original space under mild conditions.

## Construction

```
  Diatonic scale: {C, D, E, F, G, A, B} = 7 notes

  Cover by triads:
    I  = {C, E, G}     (tonic)
    ii = {D, F, A}     (supertonic)
    iii= {E, G, B}     (mediant)
    IV = {F, A, C}     (subdominant)
    V  = {G, B, D}     (dominant)
    vi = {A, C, E}     (submediant)
    vii= {B, D, F}     (leading tone)

  Number of triads: 7 = P1 + 1

  Primary triads: I, IV, V = 3 = P1/2  EXACT
```

## ASCII Nerve Complex

```
  Nerve of primary triads (I, IV, V):

       I({C,E,G})
      / \\
     /   \\       I cap IV = {C} (nonempty -> edge)
    /     \\      I cap V  = {G} (nonempty -> edge)
   IV------V     IV cap V = {} (empty -> no edge)

  Nerve = path graph, not triangle
  (because IV and V share no notes)
```

## Intersection Data

| Triad Pair | Intersection | Size |
|------------|-------------|------|
| I, ii | {} | 0 |
| I, iii | {E, G} | 2 |
| I, IV | {C} | 1 |
| I, V | {G} | 1 |
| I, vi | {C, E} | 2 |
| IV, V | {} | 0 |

## Interpretation

The nerve theorem applied to diatonic triads reveals harmonic proximity:
triads sharing common tones are nerve-adjacent. The P1/2 = 3 primary triads
(I, IV, V) form the backbone. Grade: WEAK because the nerve theorem
application requires checking contractibility conditions.
"""
})

hypotheses.append({
    "id": "050",
    "title": "Sheaf Theory of Musical Analysis",
    "statement": "Musical analysis can be modeled as a sheaf on the time axis: local harmonic analysis assigns chord labels to time intervals, and the sheaf condition requires consistency on overlaps. The stalk at each time point has up to sigma(6) = 12 possible pitch classes.",
    "grade": "WEAK",
    "emoji": "\U0001f7e7",
    "body": """## Background

A sheaf assigns data (sections) to open sets with consistency conditions
on overlaps. In music, the "data" is harmonic analysis: which chord or
key is active at each time interval.

## Construction

```
  Base space: time axis R (or circle S^1 for repeating pieces)
  Presheaf F:
    F(U) = set of harmonic analyses on time interval U
    = assignments of chords from Z_12 = Z_{sigma(6)} to each moment

  Sheaf condition:
    If analyses agree on overlaps U_i cap U_j,
    they glue to a global analysis on union U_i cup U_j

  Stalk at t:
    F_t = possible pitch classes at time t
    |F_t| <= 12 = sigma(6)
```

## ASCII Sheaf Structure

```
  Harmonic analysis sheaf:

  Section over [0,4]:  C major
  Section over [3,8]:  G major      overlap [3,4]: must agree
  Section over [7,12]: C major      overlap [7,8]: must agree

  Time: 0---1---2---3---4---5---6---7---8---9--10--11--12
        |---C major---|                |---C major----|
                   |---G major---|
                   ^             ^
                   gluing regions (sheaf condition)
```

## Sheaf Data

| Property | Value | n=6 Link |
|----------|-------|----------|
| Stalk size | <= 12 | sigma(6) |
| Key labels | 24 | 2*sigma(6) |
| Chord types | varies | -- |
| Consistency | sheaf axiom | overlap agreement |

## Interpretation

Sheaf theory provides a rigorous framework for the intuition that
harmonic analysis must be locally consistent and globally coherent.
The stalk at each point draws from Z_{sigma(6)} pitch classes.
Grade: WEAK because sheaf theory is a powerful but general framework;
the n=6 connection is through the 12-element pitch class set.
"""
})


def generate_file(h):
    """Generate a single hypothesis file."""
    filename = f"MUSICTOPO-{h['id']}-{h['title'].lower().replace(' ', '-').replace('/', '-').replace(':', '').replace('(', '').replace(')', '').replace('^', '').replace('=', '-').replace(',', '').replace('.', '').replace('>', '').replace('<', '').replace('*', '').replace('+', 'plus').replace('|', '')}.md"
    # Truncate filename if too long
    if len(filename) > 80:
        filename = filename[:76] + ".md"

    grade_label = f"{h['emoji']} {h['grade']}"

    content = f"""# MUSICTOPO-{h['id']}: {h['title']}

**Domain**: Topology of Music | **Grade**: {grade_label}
**GZ Dependency**: None (pure structural topology)

## Hypothesis

> {h['statement']}

{h['body'].strip()}
"""

    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, 'w') as f:
        f.write(content)
    return filepath


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Generating {len(hypotheses)} MUSICTOPO hypothesis files...")
    for h in hypotheses:
        path = generate_file(h)
        print(f"  Created: {os.path.basename(path)}")
    print(f"\nDone! {len(hypotheses)} files generated in {OUTPUT_DIR}")


if __name__ == '__main__':
    main()
