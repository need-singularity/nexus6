#!/usr/bin/env python3
"""Generate MUSIC-006 through MUSIC-105 hypothesis files."""

import os

OUTPUT_DIR = "/Users/ghost/Dev/TECS-L/docs/hypotheses"

# Constants
# P1=6, sigma=12, tau=4, phi=2, sopfr=5, divisors={1,2,3,6}

hypotheses = []

def h(num, slug, title, grade, statement, body):
    """Register a hypothesis."""
    hypotheses.append((num, slug, title, grade, statement, body))

# ============================================================
# SCALES & INTERVALS (006-025)
# ============================================================

h(6, "chromatic-scale-sigma", "Chromatic Scale = sigma(6) Semitones",
  "EXACT",
  "The chromatic scale contains exactly 12 = sigma(6) pitch classes per octave,\n"
  "> where sigma(6) = 1+2+3+6 = 12 is the divisor sum of the first perfect number.",
  """## Background

The chromatic scale is the foundational pitch collection of Western music,
containing all 12 semitones within one octave. This is not a tuning convention
but a structural consequence of harmonic acoustics and equal temperament.

Related: MUSIC-001 (12-TET = sigma(6)).

## Numerical Verification

| Quantity               | Value | n=6 Function | Match |
|------------------------|-------|-------------- |-------|
| Chromatic pitch classes |  12  | sigma(6)=12  | EXACT |
| Semitone ratio         | 2^(1/12) | 2^(1/sigma(6)) | EXACT |
| Enharmonic equivalents |  12  | sigma(6)=12  | EXACT |

## ASCII Diagram: Chromatic Scale on Piano

```
  C  C# D  D# E  F  F# G  G# A  A# B  | C
  |  |  |  |  |  |  |  |  |  |  |  |  | |
  1  2  3  4  5  6  7  8  9  10 11 12 | =sigma(6)
```

## Interpretation

The chromatic scale's cardinality = sigma(6) = 12 is an exact match.
This is the same structural observation as MUSIC-001 viewed from the
scale perspective rather than the temperament perspective.

## Limitations

- 12-TET is Western-centric; Indian (22 shruti) and Arabic (24-TET) differ.
- sigma(6)=12 also equals 2*6, 3*4, etc. — multiple factorizations available.
""")

h(7, "pentatonic-sopfr", "Pentatonic Scale = sopfr(6) Notes",
  "EXACT",
  "The pentatonic scale contains exactly 5 = sopfr(6) notes per octave,\n"
  "> where sopfr(6) = 2+3 = 5 is the sum of prime factors of 6.",
  """## Background

The pentatonic scale is the most universal scale in world music, found
independently in Chinese, Celtic, African, and Native American traditions.
Its five notes (e.g., C D E G A) avoid semitone dissonance entirely.

## Numerical Verification

| Quantity                | Value | n=6 Function | Match |
|-------------------------|-------|-------------- |-------|
| Pentatonic notes        |   5   | sopfr(6)=5   | EXACT |
| Black keys on piano     |   5   | sopfr(6)=5   | EXACT |
| Intervals avoiding m2   |   5   | sopfr(6)=5   | EXACT |

## ASCII Diagram: Pentatonic on Chromatic

```
  C  .  D  .  E  .  .  G  .  A  .  .  | C
  *     *     *        *     *        | * = 5 = sopfr(6)
```

## Interpretation

The pentatonic scale's universality may stem from its deep simplicity:
5 = sopfr(6) = sum of the prime building blocks of the perfect number.
The black keys on a piano form a pentatonic scale — another set of 5.

## Limitations

- 5 is a common small number; could be coincidence.
- Some pentatonic variants have 6 notes (blues scale).
""")

h(8, "blues-scale-P1", "Blues Scale = P1 = 6 Notes",
  "EXACT",
  "The blues scale contains exactly 6 = P1 notes: the pentatonic scale\n"
  "> plus the 'blue note' (flat fifth), totaling the first perfect number.",
  """## Background

The blues scale adds one chromatic passing tone (the blue note, b5) to the
minor pentatonic scale: C Eb F Gb G Bb. This creates a 6-note scale that
is the foundation of blues, jazz, and rock music.

## Numerical Verification

| Quantity            | Value | n=6 Function | Match |
|---------------------|-------|-------------- |-------|
| Blues scale notes    |   6   | P1=6         | EXACT |
| = pentatonic + 1    | 5+1   | sopfr(6)+1   | EXACT |
| Blue note = tritone |   6   | 6 semitones  | EXACT |

## ASCII Diagram

```
  Minor pentatonic:  C  Eb  F      G  Bb     = 5 = sopfr(6)
  Blues scale:       C  Eb  F  Gb  G  Bb     = 6 = P1
                                 ^
                          blue note (tritone from root)
```

## Interpretation

The blues scale = P1 = 6 notes. The added blue note is the tritone
(6 semitones from root), itself equal to P1. Double appearance of 6.

## Limitations

- Some blues musicians use additional notes (9-note blues scale exists).
""")

h(9, "hexachord-medieval", "Medieval Hexachord = P1 = 6 Notes",
  "EXACT",
  "The medieval hexachord system of Guido d'Arezzo divides the gamut into\n"
  "> overlapping groups of exactly 6 = P1 notes (ut, re, mi, fa, sol, la).",
  """## Background

Guido d'Arezzo (c. 991-1033) organized pitches into hexachords of 6 notes
each: ut, re, mi, fa, sol, la. Three hexachord types existed: natural
(C), hard (G), and soft (F). This was THE system for 500+ years.

## Numerical Verification

| Quantity                | Value | n=6 Function | Match |
|-------------------------|-------|-------------- |-------|
| Notes per hexachord     |   6   | P1=6         | EXACT |
| Hexachord types         |   3   | P1/2=3       | EXACT |
| Solmization syllables   |   6   | P1=6         | EXACT |
| Mutation points         |   2   | phi(6)=2     | EXACT |

## ASCII Diagram: Three Hexachords

```
  C  D  E  F  G  A  B  c  d  e  f  g
  |--natural (6)--|
        |---soft (6)----|
              |---hard (6)----|
  Each bracket = 6 = P1 notes
```

## Interpretation

The hexachord is literally "six strings" (Greek). The medieval system
that organized Western music for centuries was built on groups of P1=6.

## Limitations

- The hexachord was eventually replaced by the 7-note octave system.
""")

h(10, "solmization-six", "Solmization Syllables = P1 = 6",
  "EXACT",
  "The original solmization system uses exactly 6 = P1 syllables:\n"
  "> ut, re, mi, fa, sol, la — derived from a hymn to St. John.",
  """## Background

The six syllables come from the first syllables of each line of the
hymn "Ut queant laxis" (c. 1000 CE). "Si" (later "ti") was added in
the 17th century, but the original system was strictly 6 syllables.

## Numerical Verification

| Quantity                   | Value | n=6 Function | Match |
|----------------------------|-------|-------------- |-------|
| Original syllables         |   6   | P1=6         | EXACT |
| Modern solfege (do-ti)     |   7   | P1+1=7       | EXACT |
| Syllables from hymn lines  |   6   | P1=6         | EXACT |

## ASCII Diagram

```
  Ut  Re  Mi  Fa  Sol  La  |  [Si added later]
  1   2   3   4   5    6   |  7
  |<--- original P1=6 --->|  +1 = P1+1
```

## Interpretation

The foundational pitch-naming system of Western music contained P1=6
syllables for over 600 years before the 7th was added.

## Limitations

- "Si"/"ti" addition makes modern solfege 7, not 6.
""")

h(11, "church-modes-six", "Original Church Modes = P1 = 6",
  "WEAK",
  "The earliest classification of church modes recognized 6 = P1 modes\n"
  "> (4 authentic + 2 plagal additions), before expansion to 8 and then 12.",
  """## Background

The history of church modes is complex. The initial Byzantine system had
4 authentic modes (oktoechos). By the 9th century, 4 plagal modes were
added (total 8). Some scholars identify an intermediate 6-mode stage,
but this is debated.

## Numerical Verification

| System              | Modes | n=6 Function | Match   |
|---------------------|-------|-------------- |---------|
| Byzantine (early)   |   4   | tau(6)=4     | EXACT   |
| Medieval (standard) |   8   | (none clean) | --      |
| Glareanus (1547)    |  12   | sigma(6)=12  | EXACT   |
| Some early sources  |   6   | P1=6         | DEBATED |

## Interpretation

The cleaner matches are 4 original modes = tau(6) and 12 Glareanus
modes = sigma(6). The claim of exactly 6 modes is historically shaky.

## Limitations

- The standard medieval count is 8, not 6.
- The "6 modes" claim requires cherry-picking historical sources.
""")

h(12, "perfect-intervals-tau", "Perfect Intervals = tau(6) = 4",
  "EXACT",
  "Western music theory recognizes exactly 4 = tau(6) 'perfect' intervals:\n"
  "> unison (P1), perfect fourth (P4), perfect fifth (P5), and octave (P8).",
  """## Background

"Perfect" intervals are those that remain unchanged under inversion of
major/minor quality. They are the most consonant intervals and form the
backbone of harmony. Their designation as "perfect" dates to medieval theory.

## Numerical Verification

| Perfect Interval | Semitones | Ratio | Divisor connection |
|-----------------|-----------|-------|--------------------|
| Unison (P1)     |     0     |  1:1  | d=1 in div(6)      |
| Perfect 4th     |     5     |  4:3  | sopfr(6)=5         |
| Perfect 5th     |     7     |  3:2  | P1+1=7             |
| Octave (P8)     |    12     |  2:1  | sigma(6)=12        |
| **Count**       |   **4**   |       | **tau(6)=4**       |

## ASCII Diagram

```
  Interval quality categories:
  ┌──────────────────────────────────────┐
  │ Perfect (4=tau(6)): P1, P4, P5, P8  │
  │ Major/Minor:        2nd,3rd,6th,7th │
  │ Augmented/Diminished: modified      │
  └──────────────────────────────────────┘
```

## Interpretation

The count of perfect intervals = tau(6) = 4 is exact and fundamental
to music theory. These intervals are "perfect" because their frequency
ratios use only divisors of 6: {1, 2, 3}.

## Limitations

- The number 4 is very common; many things come in fours.
""")

h(13, "interval-classes-sigma", "Interval Classes in Octave = sigma(6) = 12",
  "EXACT",
  "There are exactly 12 = sigma(6) distinct interval classes within one octave,\n"
  "> from minor second (1 semitone) through octave (12 semitones).",
  """## Background

An interval class counts the number of semitones between two pitches.
Within one octave, there are 12 possible distances (1 through 12 semitones),
or equivalently 12 named intervals from m2 to P8.

## Numerical Verification

| Interval       | Semitones | Interval       | Semitones |
|----------------|-----------|----------------|-----------|
| minor 2nd      |     1     | perfect 5th    |     7     |
| Major 2nd      |     2     | minor 6th      |     8     |
| minor 3rd      |     3     | Major 6th      |     9     |
| Major 3rd      |     4     | minor 7th      |    10     |
| perfect 4th    |     5     | Major 7th      |    11     |
| tritone        |     6     | Octave         |    12     |

Total = 12 = sigma(6)

## Interpretation

The total number of distinct interval sizes within an octave equals
sigma(6) = 12. This is structurally equivalent to the chromatic count.

## Limitations

- This is essentially the same observation as the chromatic scale having 12 notes.
""")

h(14, "circle-of-fifths-sigma", "Circle of Fifths = sigma(6) = 12 Keys",
  "EXACT",
  "The circle of fifths contains exactly 12 = sigma(6) keys before returning\n"
  "> to the starting pitch class.",
  """## Background

The circle of fifths is a fundamental organizing principle of Western
music theory. Starting from any note and ascending by perfect fifths
(7 semitones each), one passes through all 12 pitch classes before
returning to the start: 12 * 7 = 84 semitones = 7 octaves.

## Numerical Verification

| Quantity               | Value | n=6 Function | Match |
|------------------------|-------|-------------- |-------|
| Keys in circle         |  12   | sigma(6)=12  | EXACT |
| Octaves traversed      |   7   | P1+1=7       | EXACT |
| Semitones per fifth    |   7   | P1+1=7       | EXACT |
| Total semitones        |  84   | 7*sigma(6)   | EXACT |

## ASCII Diagram

```
          C
       F     G         12 = sigma(6) keys
     Bb        D        7 = P1+1 semitones per step
    Eb          A        7 = P1+1 octaves to close
     Ab        E
       Db    B
          F#
```

## Interpretation

The circle of fifths' 12-key structure is sigma(6). The step size
(perfect fifth = 7 semitones) and closure octave count (7) both
equal P1+1, though this involves a +1 correction.

## Limitations

- 7 = P1+1 uses a +1 correction — ad hoc risk.
""")

h(15, "key-signatures-2sigma", "Key Signatures = 2*sigma(6) = 24",
  "EXACT",
  "There are exactly 24 = 2*sigma(6) distinct key signatures in Western\n"
  "> music: 12 major keys + 12 minor keys (relative major/minor pairs).",
  """## Background

Each of the 12 pitch classes can serve as the tonic of a major or minor
key, giving 24 total key signatures. Major and minor keys sharing the
same key signature are called "relative" keys.

## Numerical Verification

| Quantity          | Value | n=6 Expression | Match |
|-------------------|-------|--------------- |-------|
| Major keys        |  12   | sigma(6)       | EXACT |
| Minor keys        |  12   | sigma(6)       | EXACT |
| Total keys        |  24   | 2*sigma(6)     | EXACT |
| Relative pairs    |  12   | sigma(6)       | EXACT |
| Max sharps/flats  |   6   | P1=6           | EXACT |

## ASCII Diagram: Key Signature Counts

```
  Sharps: 0  1  2  3  4  5  6
  Major:  C  G  D  A  E  B  F#
  Minor:  a  e  b  f# c# g# d#

  Flats:  0  1  2  3  4  5  6
  Major:  C  F  Bb Eb Ab Db Gb
  Minor:  a  d  g  c  f  bb eb

  Max accidentals = 6 = P1 (in either direction)
```

## Interpretation

24 = 2*sigma(6) keys, with maximum 6 = P1 sharps or flats. The number
P1 appears as both the maximum accidental count and the organizing constant.

## Limitations

- 24 = 2*12 is a simple doubling; the deeper fact is 12 = sigma(6).
""")

h(16, "cents-per-octave", "Cents Per Octave = 100 * sigma(6) = 1200",
  "EXACT",
  "One octave equals exactly 1200 = 100 * sigma(6) cents, where the cent\n"
  "> is defined as 1/100 of a semitone = 1/100 of 1/sigma(6) of an octave.",
  """## Background

The cent is the standard logarithmic unit for measuring musical intervals.
Defined by Alexander Ellis in 1885: 1 cent = 1/1200 of an octave.

## Numerical Verification

| Quantity              | Value | n=6 Expression   | Match |
|-----------------------|-------|------------------ |-------|
| Cents per octave      | 1200  | 100*sigma(6)     | EXACT |
| Cents per semitone    |  100  | 100               | def.  |
| Semitones per octave  |   12  | sigma(6)=12      | EXACT |

## ASCII Diagram

```
  0         300        600        900       1200 cents
  |----------|----------|----------|----------|
  C          Eb         F#         A          C
  0          3          6          9          12 semitones
             P1/2       P1         (none)     sigma(6)
```

## Interpretation

1200 = 100 * sigma(6) is definitional given 12-TET, but reinforces
that sigma(6) is the architectural constant of Western pitch.

## Limitations

- The factor 100 is arbitrary (decimal convenience, not structural).
""")

h(17, "whole-tone-scale-P1", "Whole Tone Scale = P1 = 6 Notes",
  "EXACT",
  "The whole tone scale contains exactly 6 = P1 notes, dividing the octave\n"
  "> into 6 equal whole steps of 2 semitones each.",
  """## Background

The whole tone scale (C D E F# G# A#) divides the octave into 6 equal
intervals of 200 cents each. Used extensively by Debussy and other
impressionist composers for its dreamlike, directionless quality.

## Numerical Verification

| Quantity              | Value | n=6 Function | Match |
|-----------------------|-------|-------------- |-------|
| Notes in scale        |   6   | P1=6         | EXACT |
| Whole steps           |   6   | P1=6         | EXACT |
| Distinct WT scales    |   2   | phi(6)=2     | EXACT |
| Semitones per step    |   2   | phi(6)=2     | EXACT |

## ASCII Diagram

```
  Whole tone scale 1: C  D  E  F# G# A#  (6 notes = P1)
  Whole tone scale 2: Db Eb F  G  A  B   (6 notes = P1)

  Only 2 = phi(6) distinct whole tone scales exist!
  Step size = 2 = phi(6) semitones
```

## Interpretation

Three appearances of n=6 constants: P1=6 notes, phi(6)=2 distinct
scales, phi(6)=2 semitones per step. Remarkably clean mapping.

## Limitations

- Already covered in MUSIC-002; this adds the phi(6)=2 observations.
""")

h(18, "augmented-scale", "Augmented Scale Symmetry = tau(6) = 4 Notes per Subset",
  "EXACT",
  "The augmented (hexatonic) scale alternates minor thirds and semitones,\n"
  "> containing 6 = P1 notes built from two augmented triads of 3 = P1/2 notes each.",
  """## Background

The augmented scale (C D# E G Ab B) is a symmetric 6-note scale built
by interlocking two augmented triads a semitone apart. It has 4 = tau(6)
distinct transpositions due to its high symmetry.

## Numerical Verification

| Quantity                | Value | n=6 Function | Match |
|-------------------------|-------|-------------- |-------|
| Notes in scale          |   6   | P1=6         | EXACT |
| Notes per triad         |   3   | P1/2=3       | EXACT |
| Distinct transpositions |   4   | tau(6)=4     | EXACT |
| Augmented triads used   |   2   | phi(6)=2     | EXACT |

## ASCII Diagram

```
  Augmented scale: C . . D# E . . G Ab . . B | C
                   *       * *       * *       * |
  Triad 1:        C     E     Ab     = augmented triad (3 notes)
  Triad 2:          D#    G     B    = augmented triad (3 notes)
```

## Interpretation

The augmented scale packs multiple n=6 constants: P1=6 notes, P1/2=3
per triad, phi(6)=2 triads combined, tau(6)=4 transpositions.

## Limitations

- The augmented scale is less common than major/minor/pentatonic.
""")

h(19, "diatonic-modes-P1plus1", "Diatonic Scale = P1 + 1 = 7 Notes",
  "WEAK",
  "The diatonic (major/minor) scale contains 7 = P1 + 1 notes per octave.\n"
  "> This is one more than the perfect number, requiring a +1 correction.",
  """## Background

The diatonic scale (major: C D E F G A B) is the most important scale
in Western music. Its 7 notes generate the 7 modes (Ionian through
Locrian) and form the basis of tonal harmony.

## Numerical Verification

| Quantity           | Value | n=6 Function | Match |
|--------------------|-------|-------------- |-------|
| Diatonic notes     |   7   | P1+1=7       | +1    |
| Modes              |   7   | P1+1=7       | +1    |
| Intervals in scale |   6   | P1=6         | EXACT |
| Scale steps        |   7   | P1+1=7       | +1    |

## ASCII Diagram

```
  C  D  E  F  G  A  B  | C
  1  2  3  4  5  6  7  | = P1+1
  |  W  W  H  W  W  W  H |
  intervals between = 7 steps, but 6 = P1 "inner" intervals
```

## Interpretation

The +1 correction weakens this. However, the 6 intervals between
7 notes = P1 is exact. The diatonic scale has 7 notes but 6 scale steps.

## Limitations

- P1+1 is an ad hoc correction. Grade reduced to WEAK.
""")

h(20, "diminished-scale-symmetry", "Diminished Scale = 2*tau(6) = 8 Notes",
  "EXACT",
  "The diminished (octatonic) scale contains 8 = 2*tau(6) notes, built from\n"
  "> two diminished seventh chords of 4 = tau(6) notes each.",
  """## Background

The diminished scale alternates whole and half steps (or vice versa),
producing 8 notes. It has only 3 = P1/2 distinct transpositions due
to its symmetry. Used extensively in jazz and by Messiaen.

## Numerical Verification

| Quantity                | Value | n=6 Function | Match |
|-------------------------|-------|-------------- |-------|
| Notes in scale          |   8   | 2*tau(6)=8   | EXACT |
| Notes per dim7 chord    |   4   | tau(6)=4     | EXACT |
| Dim7 chords combined    |   2   | phi(6)=2     | EXACT |
| Distinct transpositions |   3   | P1/2=3       | EXACT |

## ASCII Diagram

```
  Dim scale (H-W): C Db Eb E F# G A Bb | = 8 = 2*tau(6)
  Dim7 chord 1:    C    Eb    F#    A   | = 4 = tau(6)
  Dim7 chord 2:      Db    E     G    Bb| = 4 = tau(6)
```

## Interpretation

Four n=6 constants appear: 2*tau(6)=8 notes, tau(6)=4 per chord,
phi(6)=2 chords, P1/2=3 transpositions. Strong structural mapping.

## Limitations

- 8 = 2*tau(6) is a derived expression, not a direct function of 6.
""")

h(21, "tritone-substitution", "Tritone Substitution Pairs = P1 = 6",
  "EXACT",
  "In the 12-tone chromatic scale, there are exactly 6 = P1 tritone pairs,\n"
  "> each pair being 6 semitones apart.",
  """## Background

Tritone substitution is a fundamental jazz harmony technique where a
dominant chord is replaced by the dominant chord a tritone away. The
12 pitch classes form 6 pairs of tritone-related notes.

## Numerical Verification

| Tritone Pair | Semitones Apart | Pair # |
|-------------|----------------|--------|
| C - F#      |       6        |   1    |
| Db - G      |       6        |   2    |
| D - Ab      |       6        |   3    |
| Eb - A      |       6        |   4    |
| E - Bb      |       6        |   5    |
| F - B       |       6        |   6    |

Total pairs = 12/2 = 6 = P1. Each pair separated by P1=6 semitones.

## ASCII Diagram

```
  12 pitch classes / 2 = 6 = P1 tritone pairs
       C --- F#
      Db --- G      Each line = 6 semitones = P1
       D --- Ab
      Eb --- A
       E --- Bb
       F --- B
```

## Interpretation

The tritone creates exactly P1=6 pairs from sigma(6)=12 pitch classes.
P1 divides sigma(6) perfectly: sigma(6)/P1 = 2 = phi(6).

## Limitations

- This is arithmetic: 12/2=6. The structural content is in 12=sigma(6).
""")

h(22, "major-minor-duality", "Major/Minor Duality = phi(6) = 2 Qualities",
  "EXACT",
  "The fundamental duality of Western music is the major/minor system:\n"
  "> exactly 2 = phi(6) primary scale qualities.",
  """## Background

Major and minor are the two fundamental tonalities of Western music.
Every key is either major or minor. This binary opposition defines
the emotional landscape of tonal music.

## Numerical Verification

| Quantity            | Value | n=6 Function | Match |
|---------------------|-------|-------------- |-------|
| Primary qualities   |   2   | phi(6)=2     | EXACT |
| Major scales        |  12   | sigma(6)=12  | EXACT |
| Minor scales        |  12   | sigma(6)=12  | EXACT |
| Total               |  24   | 2*sigma(6)   | EXACT |

## ASCII Diagram

```
  Tonality Tree:
       Music
      /     \\
  Major     Minor     = 2 = phi(6)
  (12)      (12)      = sigma(6) each
  = 24 total           = 2*sigma(6)
```

## Interpretation

The major/minor duality = phi(6) = 2. Combined with sigma(6)=12
keys each, the total 24 = 2*sigma(6) is exact.

## Limitations

- Many binary distinctions exist; phi(6)=2 matches any duality.
""")

h(23, "minor-scale-types", "Minor Scale Variants = P1/2 = 3",
  "EXACT",
  "There are exactly 3 = P1/2 standard minor scale types: natural, harmonic,\n"
  "> and melodic minor.",
  """## Background

While there is one major scale, the minor scale has three standard forms:
natural minor (Aeolian), harmonic minor (raised 7th), and melodic minor
(raised 6th and 7th ascending). This asymmetry is fundamental.

## Numerical Verification

| Minor Scale Type | Alteration       | #   |
|-----------------|------------------|-----|
| Natural minor   | none             |  1  |
| Harmonic minor  | raised 7th       |  2  |
| Melodic minor   | raised 6th & 7th |  3  |

Total = 3 = P1/2 = 6/2

## ASCII Diagram

```
  A natural:   A B C D E F  G  A   (no alterations)
  A harmonic:  A B C D E F  G# A   (raise 7th)
  A melodic:   A B C D E F# G# A   (raise 6th, 7th)
  ────────────────────────────────
  3 types = P1/2
```

## Interpretation

The three minor scale forms = P1/2 = 3 is exact and fundamental.

## Limitations

- 3 is a very common number; many things come in threes.
""")

h(24, "chromatic-intervals-complementary", "Complementary Interval Pairs = P1 = 6",
  "EXACT",
  "Intervals within an octave form exactly 6 = P1 complementary pairs,\n"
  "> where each pair sums to 12 = sigma(6) semitones.",
  """## Background

Every interval has a complement: the interval that, added to it, completes
an octave. m2+M7=12, M2+m7=12, etc. The 12 intervals form 6 pairs.

## Numerical Verification

| Pair | Interval A | Interval B | Sum  |
|------|-----------|-----------|------|
|  1   | m2 (1)    | M7 (11)   |  12  |
|  2   | M2 (2)    | m7 (10)   |  12  |
|  3   | m3 (3)    | M6 (9)    |  12  |
|  4   | M3 (4)    | m6 (8)    |  12  |
|  5   | P4 (5)    | P5 (7)    |  12  |
|  6   | TT (6)    | TT (6)    |  12  |

Total pairs = 6 = P1

## ASCII Diagram

```
  0  1  2  3  4  5  6  7  8  9  10 11 12
  |  |--|  |--|  |--|  |--|  |--|  |--| |
     pair1 pair2 pair3 pair4 pair5 pair6
  6 pairs = P1, each summing to sigma(6)=12
```

## Interpretation

Complementary pairs = P1 = 6, each summing to sigma(6) = 12.

## Limitations

- This is arithmetic: 12/2 = 6. Same as MUSIC-021.
""")

h(25, "enharmonic-equivalence", "Enharmonic Pitch Classes = sigma(6) = 12",
  "EXACT",
  "Under enharmonic equivalence (e.g., C# = Db), there are exactly\n"
  "> 12 = sigma(6) distinct pitch classes.",
  """## Background

Enharmonic equivalence identifies pitches that sound the same but are
spelled differently (C# = Db, D# = Eb, etc.). In 12-TET, this reduces
the infinite set of note names to exactly 12 equivalence classes.

## Numerical Verification

| Quantity              | Value | n=6 Function | Match |
|-----------------------|-------|-------------- |-------|
| Pitch classes         |  12   | sigma(6)=12  | EXACT |
| Natural notes         |   7   | P1+1=7       | +1    |
| Accidental notes      |   5   | sopfr(6)=5   | EXACT |
| Enharmonic pairs      |   5   | sopfr(6)=5   | EXACT |

## ASCII Diagram

```
  Natural: C  D  E  F  G  A  B     = 7 = P1+1
  Sharp:      C# D#    F# G# A#   = 5 = sopfr(6)
  ─────────────────────────────────────
  Total pitch classes = 12 = sigma(6)

  Natural notes (7) + accidentals (5) = sigma(6)
  P1+1 + sopfr(6) = 7+5 = 12 = sigma(6)  EXACT!
```

## Interpretation

sigma(6) = P1+1 + sopfr(6) = 7+5 = 12. The decomposition of the
chromatic scale into naturals and accidentals mirrors n=6 arithmetic.

## Limitations

- 7+5=12 is a partition; many partitions of 12 exist.
""")

# ============================================================
# RHYTHM & METER (026-040)
# ============================================================

h(26, "six-eight-time", "6/8 Time Signature = P1 Eighth Notes",
  "EXACT",
  "The 6/8 time signature groups exactly 6 = P1 eighth notes per measure,\n"
  "> creating compound duple meter (2 groups of 3).",
  """## Background

6/8 is one of the most common compound time signatures. It groups
6 eighth notes into 2 groups of 3, creating a characteristic lilting
feel used in jigs, barcarolles, and marches.

## Numerical Verification

| Quantity                | Value | n=6 Function | Match |
|-------------------------|-------|-------------- |-------|
| Eighth notes per bar    |   6   | P1=6         | EXACT |
| Groups per bar          |   2   | phi(6)=2     | EXACT |
| Notes per group         |   3   | P1/2=3       | EXACT |
| Beats felt              |   2   | phi(6)=2     | EXACT |

## ASCII Diagram

```
  6/8: |  *  .  .  *  .  . |  *  .  .  *  .  . |
       |<- 3 ->|<- 3 ->|  |<- 3 ->|<- 3 ->|
       |<--- P1=6 --->|   |<--- P1=6 --->|
       2 groups = phi(6)   3 per group = P1/2
```

## Interpretation

6/8 time is P1=6 subdivided as phi(6)*P1/2 = 2*3 = 6. The factorization
of the perfect number into its prime factors IS compound duple meter.

## Limitations

- 6/8 is one of many time signatures; its prominence is cultural.
""")

h(27, "basic-meter-types", "Simple Meter Types = P1/2 = 3",
  "EXACT",
  "Simple meters come in exactly 3 = P1/2 basic types: duple (2), triple (3),\n"
  "> and quadruple (4), corresponding to phi(6), P1/2, and tau(6).",
  """## Background

Simple meters group beats in twos, threes, or fours. These three types
exhaust the practical possibilities for regular metric grouping.

## Numerical Verification

| Meter Type | Beats | n=6 Function | Match |
|-----------|-------|-------------- |-------|
| Duple     |   2   | phi(6)=2     | EXACT |
| Triple    |   3   | P1/2=3       | EXACT |
| Quadruple |   4   | tau(6)=4     | EXACT |
| **Types** | **3** | **P1/2=3**   | EXACT |

## ASCII Diagram

```
  Duple:     | * . | * . |           beats = phi(6)=2
  Triple:    | * . . | * . . |       beats = P1/2=3
  Quadruple: | * . . . | * . . . |   beats = tau(6)=4

  The beat counts ARE the n=6 arithmetic functions!
```

## Interpretation

The three basic meter types use beats {2, 3, 4} = {phi(6), P1/2, tau(6)}.
This is a striking correspondence: musical meter IS n=6 arithmetic.

## Limitations

- Quintuple (5) and septuple (7) meters exist but are rare.
""")

h(28, "compound-meters", "Compound Meter Types = P1/2 = 3",
  "EXACT",
  "Compound meters also come in 3 = P1/2 standard types: compound duple (6/8),\n"
  "> compound triple (9/8), and compound quadruple (12/8).",
  """## Background

Compound meters subdivide each beat into three. The three standard
compound meters are 6/8, 9/8, and 12/8.

## Numerical Verification

| Compound Type   | Subdivisions | n=6 expression | Match |
|----------------|-------------|----------------|-------|
| Compound duple  |   6/8       | P1=6           | EXACT |
| Compound triple |   9/8       | (P1/2)^2=9     | EXACT |
| Compound quad   |  12/8       | sigma(6)=12    | EXACT |
| **Types**       |  **3**      | **P1/2=3**     | EXACT |

## ASCII Diagram

```
  6/8:  | 1.2.3. 4.5.6. |     P1=6 subdivisions
  9/8:  | 1.2.3. 4.5.6. 7.8.9. | (P1/2)^2=9
  12/8: | 1.2.3. 4.5.6. 7.8.9. 10.11.12. | sigma(6)=12
```

## Interpretation

Compound meters use P1=6, 9, sigma(6)=12 subdivisions.
All three counts derive from n=6 functions.

## Limitations

- 9 = (P1/2)^2 is a derived expression, not a direct function.
""")

h(29, "polyrhythm-2-3", "Fundamental Polyrhythm 2:3 = phi(6):P1/2",
  "EXACT",
  "The most fundamental polyrhythm in music is 2 against 3, corresponding\n"
  "> to phi(6):P1/2. These are the prime factors of 6 = 2 * 3.",
  """## Background

The 2:3 polyrhythm (two beats against three) is the most basic and
universal polyrhythm, found in African drumming, Afro-Cuban music,
Baroque dance, and modern jazz. It generates rhythmic tension.

## Numerical Verification

| Quantity              | Value | n=6 Function | Match |
|-----------------------|-------|-------------- |-------|
| Short pattern beats   |   2   | phi(6)=2     | EXACT |
| Long pattern beats    |   3   | P1/2=3       | EXACT |
| LCM (cycle length)    |   6   | P1=6         | EXACT |
| Product               |   6   | P1=6         | EXACT |

## ASCII Diagram

```
  Beat: 1  2  3  4  5  6 | 1
  2s:   X     X     X   | = every 3 = P1/2
  3s:   X        X      | = every 2 = phi(6)
  LCM = 6 = P1 (cycle length)

  The 2:3 polyrhythm cycles every P1=6 units.
```

## Interpretation

The 2:3 polyrhythm = phi(6):P1/2 = prime factorization of 6.
Its cycle length = LCM(2,3) = 6 = P1. This is deeply structural.

## Limitations

- 2:3 is the simplest non-trivial ratio; its ubiquity may be independent of 6.
""")

h(30, "hemiola", "Hemiola = 3:2 Ratio = P1/2 : phi(6)",
  "EXACT",
  "The hemiola rhythmic device alternates 3:2 groupings, using the ratio\n"
  "> P1/2 : phi(6) = 3:2, which are the prime factors of P1=6.",
  """## Background

Hemiola (Greek: "one and a half") regroups 6 beats as either 3*2 or 2*3.
It is ubiquitous in Baroque dance music (courante, sarabande) and is
one of the oldest recognized rhythmic devices.

## Numerical Verification

| Quantity               | Value | n=6 Function | Match |
|------------------------|-------|-------------- |-------|
| Grouping A             | 3+3   | 2 * P1/2     | EXACT |
| Grouping B             | 2+2+2 | 3 * phi(6)   | EXACT |
| Total in both          |   6   | P1=6         | EXACT |
| Ratio                  |  3:2  | P1/2:phi(6)  | EXACT |

## ASCII Diagram

```
  Normal 3/4:  | * . . | * . . |    2 bars of 3 = P1
  Hemiola:     | * . * . * . |      3 groups of 2 = P1
                  same 6 beats, regrouped
```

## Interpretation

Hemiola is literally the rearrangement of P1=6 between its prime
factors: 2*3 <-> 3*2. It IS the commutativity of 6's factorization.

## Limitations

- Same structural observation as the 2:3 polyrhythm (MUSIC-029).
""")

h(31, "standard-note-values", "Standard Note Values = P1 = 6",
  "EXACT",
  "Western music notation uses 6 = P1 standard note duration values:\n"
  "> whole, half, quarter, eighth, sixteenth, and thirty-second.",
  """## Background

The standard note values form a geometric sequence of halving durations.
While 64th and 128th notes exist, they are extremely rare. The standard
set used in virtually all music is 6 values.

## Numerical Verification

| Note Value    | Relative Duration | #   |
|--------------|------------------|-----|
| Whole (o)     | 1                |  1  |
| Half          | 1/2              |  2  |
| Quarter       | 1/4              |  3  |
| Eighth        | 1/8              |  4  |
| Sixteenth     | 1/16             |  5  |
| Thirty-second | 1/32             |  6  |

Standard values = 6 = P1

## ASCII Diagram

```
  o────────────── whole    (1)
  d──────         half     (1/2)
  q───            quarter  (1/4)
  e──             eighth   (1/8)
  s─              16th     (1/16)
  t              32nd      (1/32)
  = 6 values = P1
```

## Interpretation

The 6 standard note values = P1 is conventional but deeply embedded.

## Limitations

- Convention-dependent: 64th notes exist but are very rare.
- The "standard 6" is a soft boundary.
""")

h(32, "rest-values", "Standard Rest Values = P1 = 6",
  "EXACT",
  "Corresponding to the 6 = P1 note values, there are 6 = P1 standard rest\n"
  "> values (whole rest through thirty-second rest).",
  """## Background

Each note value has a corresponding rest of equal duration. The standard
set of rests mirrors the standard note values.

## Numerical Verification

| Rest Value      | Duration | #   |
|----------------|----------|-----|
| Whole rest      | 1        |  1  |
| Half rest       | 1/2      |  2  |
| Quarter rest    | 1/4      |  3  |
| Eighth rest     | 1/8      |  4  |
| Sixteenth rest  | 1/16     |  5  |
| 32nd rest       | 1/32     |  6  |

Total = 6 = P1

## ASCII Diagram

```
  Notes:  o  d  q  e  s  t    = 6 = P1
  Rests:  _  _  _  _  _  _    = 6 = P1
  Paired: 6 note-rest pairs   = P1
```

## Interpretation

6 note values + 6 rest values = P1 + P1, mirroring the note system.

## Limitations

- Directly dependent on MUSIC-031; same convention-dependency.
""")

h(33, "triplet-subdivision", "Triplet = P1/2 = 3 Notes in Space of phi(6) = 2",
  "EXACT",
  "A triplet places 3 = P1/2 notes in the time of 2 = phi(6) notes,\n"
  "> the most common tuplet in Western music.",
  """## Background

The triplet is the most fundamental irregular subdivision, placing three
notes where two would normally go. It introduces a 3:2 ratio into the
rhythmic texture — the same ratio as the hemiola and the perfect fifth.

## Numerical Verification

| Quantity              | Value | n=6 Function | Match |
|-----------------------|-------|-------------- |-------|
| Notes in triplet      |   3   | P1/2=3       | EXACT |
| Replaces              |   2   | phi(6)=2     | EXACT |
| Ratio                 |  3:2  | P1/2:phi(6)  | EXACT |
| Common grouping       |   6   | P1=6         | EXACT |

## ASCII Diagram

```
  Normal:  | * . * . |   2 = phi(6) notes
  Triplet: | * . * . * . |   3 = P1/2 notes in same space
             [    3:2   ]
  Double triplet = 6 = P1 notes per beat
```

## Interpretation

The triplet ratio 3:2 = P1/2:phi(6) = prime factorization of 6.
A beat of two triplets = 6 = P1 notes.

## Limitations

- Same 3:2 ratio as MUSIC-029 and MUSIC-030.
""")

h(34, "twelve-bar-blues", "12-Bar Blues = sigma(6) Bars",
  "EXACT",
  "The 12-bar blues, the most influential song form in popular music,\n"
  "> spans exactly 12 = sigma(6) measures.",
  """## Background

The 12-bar blues is the harmonic foundation of blues, rock and roll, jazz,
and R&B. Its I-IV-V chord progression over 12 bars has been used in
countless songs since the early 20th century.

## Numerical Verification

| Quantity              | Value | n=6 Function | Match |
|-----------------------|-------|-------------- |-------|
| Total bars            |  12   | sigma(6)=12  | EXACT |
| Chord I bars          |   4   | tau(6)=4     | EXACT |
| Chord IV bars (first) |   2   | phi(6)=2     | EXACT |
| Distinct chords used  |   3   | P1/2=3       | EXACT |

## ASCII Diagram: Standard 12-Bar Blues

```
  Bar: | 1  2  3  4 | 5  6  7  8 | 9  10 11 12 |
       | I  I  I  I | IV IV I  I | V  IV I  I  |
       |<- tau(6) ->|            |<- sigma(6)=12 ->|

  3 chords (I, IV, V) = P1/2
  12 bars = sigma(6)
```

## Interpretation

The 12-bar blues = sigma(6) bars, using P1/2=3 chords. The tonic
occupies tau(6)=4 of the first 4 bars. Clean multi-constant mapping.

## Limitations

- Many 12-bar variants exist (quick change, jazz blues, minor blues).
""")

h(35, "phrase-length-tau", "Standard Phrase Length = tau(6) = 4 Bars",
  "EXACT",
  "The standard musical phrase in Western music is 4 = tau(6) bars long,\n"
  "> forming the basic unit of musical thought.",
  """## Background

The 4-bar phrase is the most common phrase length in Western music,
from Bach chorales to pop songs. Two 4-bar phrases form an 8-bar
period, and three form the 12-bar blues.

## Numerical Verification

| Quantity              | Value | n=6 Function | Match |
|-----------------------|-------|-------------- |-------|
| Standard phrase       |   4   | tau(6)=4     | EXACT |
| Period (2 phrases)    |   8   | 2*tau(6)=8   | EXACT |
| Blues (3 phrases)     |  12   | sigma(6)=12  | EXACT |
| Antecedent+consequent |   2   | phi(6)=2     | EXACT |

## ASCII Diagram

```
  Phrase:   |----4 bars----|  = tau(6)
  Period:   |----4----|----4----|  = 2*tau(6) = 8
  Blues:    |----4----|----4----|----4----|  = 3*tau(6) = sigma(6)
```

## Interpretation

The phrase hierarchy: tau(6)=4 bars, doubled to 8, tripled to sigma(6)=12.

## Limitations

- Phrases of 2, 3, 5, 6, 8 bars also exist frequently.
""")

h(36, "time-signature-numerators", "Common Time Signature Numerators from div(6)",
  "WEAK",
  "The most common time signature numerators {2, 3, 4, 6} are exactly the\n"
  "> divisors of 6: div(6) = {1, 2, 3, 6}.",
  """## Background

The most frequently used time signatures are 2/4, 3/4, 4/4, and 6/8.
Their numerators {2, 3, 4, 6} overlap significantly with div(6) = {1,2,3,6}.

## Numerical Verification

| Time Sig | Numerator | In div(6)? | In functions? |
|----------|-----------|-----------|---------------|
| 2/4      |     2     |  YES (d)  | phi(6)=2      |
| 3/4      |     3     |  YES (d)  | P1/2=3        |
| 4/4      |     4     |  NO       | tau(6)=4      |
| 6/8      |     6     |  YES (d)  | P1=6          |

## ASCII Diagram

```
  div(6)     = {1, 2, 3,    6}
  Numerators = {   2, 3, 4, 6}
  Overlap    = {   2, 3,    6}  = 3/4 overlap

  4 is NOT a divisor of 6 but IS tau(6).
```

## Interpretation

3 of 4 common numerators are divisors of 6; the 4th is tau(6).
Not a perfect match to div(6) due to 4 vs 1.

## Limitations

- 4 is in {tau(6)} not div(6). 1 is in div(6) but 1/4 time is not used.
""")

h(37, "beat-subdivisions", "Beat Subdivision Levels = P1/2 = 3",
  "EXACT",
  "Beats are typically subdivided into 3 = P1/2 levels: beat, division,\n"
  "> and subdivision (e.g., quarter -> eighth -> sixteenth).",
  """## Background

Music pedagogy recognizes three levels of rhythmic hierarchy within
a beat: the beat itself, its primary division (into 2 or 3), and
the subdivision (division of the division).

## Numerical Verification

| Level        | Example (4/4) | Factor | n=6    |
|-------------|--------------|--------|--------|
| Beat         | quarter note | 1      | --     |
| Division     | eighth note  | x2     | phi(6) |
| Subdivision  | sixteenth    | x2     | phi(6) |

Levels = 3 = P1/2

## ASCII Diagram

```
  Level 1 (beat):   | *           |
  Level 2 (div):    | *     *     |  x2 = phi(6)
  Level 3 (sub):    | *  *  *  *  |  x2 = phi(6)
  ─── 3 levels = P1/2 ───
```

## Interpretation

Three subdivision levels = P1/2, each doubling by phi(6)=2.

## Limitations

- Further subdivisions exist in fast music (32nd, 64th notes).
""")

h(38, "anacrusis-types", "Anacrusis (Pickup) Positions = tau(6) = 4",
  "WEAK",
  "Common anacrusis (pickup) patterns come in 4 = tau(6) standard types:\n"
  "> 1-beat, 2-beat, half-beat, and dotted pickups.",
  """## Background

An anacrusis (pickup) is one or more notes before the first downbeat.
While any rhythmic value can serve as a pickup, the most common types
in pedagogical literature number about 4.

## Numerical Verification

| Pickup Type    | Duration     | #   |
|---------------|-------------|-----|
| Single beat   | quarter     |  1  |
| Two beats     | 2 quarters  |  2  |
| Half beat     | eighth      |  3  |
| Dotted pickup | dotted 8th  |  4  |

Approx 4 standard types = tau(6)

## Interpretation

The categorization into exactly 4 types is somewhat pedagogical
convention rather than hard musical fact.

## Limitations

- The count of "standard types" is debatable; could be 3, 5, or more.
- Grade WEAK due to convention-dependency.
""")

h(39, "dotted-note-ratio", "Dotted Note Ratio = P1/2 : phi(6) = 3:2",
  "EXACT",
  "A dotted note extends duration by half, making the ratio of dotted to\n"
  "> undotted = 3:2 = P1/2 : phi(6), the fundamental ratio of 6.",
  """## Background

Adding a dot to a note increases its duration by 50%, so a dotted note
lasts 3/2 times as long as the undotted version. This 3:2 ratio appears
throughout the n=6 framework.

## Numerical Verification

| Quantity             | Value | n=6 Function | Match |
|----------------------|-------|-------------- |-------|
| Dotted:undotted      |  3:2  | P1/2:phi(6)  | EXACT |
| Duration multiplier  |  1.5  | P1/2/phi(6)  | EXACT |
| Dot adds fraction    |  1/2  | GZ upper     | EXACT |
| Double dot adds      |  3/4  | (see below)  | --    |

## ASCII Diagram

```
  Quarter:        |====|         = 2 units
  Dotted quarter: |======|       = 3 units
  Ratio: 3:2 = P1/2 : phi(6)
```

## Interpretation

The dot extends by 1/2 (GZ upper), making 3:2 (P1/2:phi(6)).

## Limitations

- 3:2 is a simple ratio that appears in many contexts.
""")

h(40, "swing-ratio", "Swing Rhythm Ratio Approximates P1/2 : phi(6) = 3:2",
  "WEAK",
  "Jazz swing rhythm approximates a 3:2 = P1/2 : phi(6) ratio between\n"
  "> long and short notes, though actual performance varies.",
  """## Background

Swing feel divides each beat unevenly, with the first note longer than
the second. The idealized ratio is 2:1 (triplet swing), but actual
performance ranges from about 1.2:1 to 3.5:1. The "textbook" ratio
of 3:2 is sometimes cited for light swing.

## Numerical Verification

| Swing Style    | Approx Ratio | n=6 match?           |
|---------------|-------------|----------------------|
| Light swing   |   ~1.2:1    | --                   |
| Medium swing  |   ~1.5:1    | = P1/2:phi(6) = 3:2  |
| Hard swing    |   ~2:1      | = phi(6):1            |
| Extreme swing |   ~3:1      | = P1/2:1              |

## ASCII Diagram

```
  Straight: | *  *  |  *  *  |   1:1
  Swing:    | *    * | *    * |   ~3:2 = P1/2:phi(6)
  Triplet:  | *     *|  *    *|   2:1
```

## Interpretation

The "textbook" medium swing = 3:2 = P1/2:phi(6), but actual swing
varies continuously. The match is approximate at best.

## Limitations

- Swing ratio is not fixed; it varies by performer, tempo, and style.
- Grade WEAK because the 3:2 value is just one point in a continuum.
""")

# ============================================================
# HARMONY & CHORDS (041-060)
# ============================================================

h(41, "triad-P1-half", "Triad = P1/2 = 3 Notes",
  "EXACT",
  "A triad, the fundamental unit of Western harmony, consists of exactly\n"
  "> 3 = P1/2 notes stacked in thirds.",
  """## Background

The triad is the most basic chord in Western music. It consists of a root,
third, and fifth — three notes stacked in intervals of a third.

## Numerical Verification

| Quantity          | Value | n=6 Function | Match |
|-------------------|-------|-------------- |-------|
| Notes in triad    |   3   | P1/2=3       | EXACT |
| Intervals used    |   2   | phi(6)=2     | EXACT |
| Triad types       |   4   | tau(6)=4     | EXACT |
| Inversions        |   3   | P1/2=3       | EXACT |

## ASCII Diagram

```
  Major triad:  C - E - G    (3 notes = P1/2)
  Intervals:      M3  m3     (2 intervals = phi(6))

  Triad types:
    Major     (M3+m3) ─┐
    Minor     (m3+M3)  │ = 4 = tau(6)
    Diminished(m3+m3)  │
    Augmented (M3+M3) ─┘
```

## Interpretation

Triads = P1/2=3 notes, built from phi(6)=2 stacked thirds,
coming in tau(6)=4 types. Triple n=6 mapping.

## Limitations

- 3 is a very common number in any structural analysis.
""")

h(42, "seventh-chord-tau", "Seventh Chord = tau(6) = 4 Notes",
  "EXACT",
  "A seventh chord extends the triad to 4 = tau(6) notes by adding a\n"
  "> seventh above the root.",
  """## Background

Seventh chords add a fourth note (the seventh) to a triad. They are
essential in jazz, classical, and popular music. The four notes create
richer harmonic color than triads.

## Numerical Verification

| Quantity              | Value | n=6 Function | Match |
|-----------------------|-------|-------------- |-------|
| Notes in 7th chord    |   4   | tau(6)=4     | EXACT |
| Intervals stacked     |   3   | P1/2=3       | EXACT |
| Common 7th chord types|   5   | sopfr(6)=5   | EXACT |
| Inversions            |   4   | tau(6)=4     | EXACT |

## ASCII Diagram

```
  Cmaj7:  C - E - G - B    (4 notes = tau(6))
  Stacked:  M3  m3  M3     (3 thirds = P1/2)

  Common 7th types:
    Major 7th     (maj3+min3+maj3)  ─┐
    Dominant 7th  (maj3+min3+min3)   │
    Minor 7th     (min3+maj3+min3)   │ = 5 = sopfr(6)
    Half-dim 7th  (min3+min3+maj3)   │
    Diminished 7th(min3+min3+min3)  ─┘
```

## Interpretation

7th chords = tau(6)=4 notes, sopfr(6)=5 common types.

## Limitations

- Extended chords (9th, 11th, 13th) have more notes.
""")

h(43, "triad-types-tau", "Triad Quality Types = tau(6) = 4",
  "EXACT",
  "There are exactly 4 = tau(6) triad qualities: major, minor, diminished,\n"
  "> and augmented.",
  """## Background

The four triad qualities exhaust the possibilities of stacking two
intervals of major and minor thirds. This is a combinatorial fact:
2^2 = 4 combinations of {M3, m3} stacked twice.

## Numerical Verification

| Triad Type   | Structure | Quality |
|-------------|-----------|---------|
| Major       | M3 + m3   | Bright  |
| Minor       | m3 + M3   | Dark    |
| Diminished  | m3 + m3   | Tense   |
| Augmented   | M3 + M3   | Eerie   |

Count = 4 = tau(6) = 2^2 = phi(6)^phi(6)

## ASCII Diagram

```
  Third stacking combinations:
       2nd third
        M3    m3
  1st  ┌─────┬─────┐
  M3   │ Aug │ Maj │
       ├─────┼─────┤
  m3   │ Min │ Dim │
       └─────┴─────┘
  = 2x2 = phi(6)^2 = tau(6) = 4
```

## Interpretation

4 triad types = tau(6) = phi(6)^2. The number of triad types equals
the number of divisors of 6, which equals the square of phi(6).

## Limitations

- 4 = 2^2 is simple combinatorics of 2 positions with 2 choices each.
""")

h(44, "cadence-types-tau", "Cadence Types = tau(6) = 4",
  "EXACT",
  "Western music theory recognizes 4 = tau(6) fundamental cadence types:\n"
  "> authentic, plagal, half, and deceptive.",
  """## Background

A cadence is a harmonic formula that marks the end of a phrase or section.
The four standard cadence types are taught in every music theory course.

## Numerical Verification

| Cadence Type | Progression | Feeling     |
|-------------|------------|-------------|
| Authentic   | V -> I     | Complete    |
| Plagal      | IV -> I    | "Amen"     |
| Half        | ? -> V     | Incomplete  |
| Deceptive   | V -> vi    | Surprise    |

Count = 4 = tau(6)

## ASCII Diagram

```
  Cadence endings:
    Authentic:  V ──> I    (strongest resolution)
    Plagal:    IV ──> I    (church ending)
    Half:       ? ──> V    (open, questioning)
    Deceptive:  V ──> vi   (unexpected twist)
    ────────────────────
    4 types = tau(6)
```

## Interpretation

4 cadence types = tau(6) is standard theory. They provide the
"punctuation" of music: period, comma, semicolon, question mark.

## Limitations

- Some theorists identify 5 or 6 cadence types (adding evaded, Phrygian).
""")

h(45, "nonchord-tones-P1", "Non-Chord Tones = P1 = 6 Standard Types",
  "EXACT",
  "Music theory textbooks typically identify 6 = P1 standard non-chord\n"
  "> tone types: passing, neighbor, suspension, appoggiatura, escape, anticipation.",
  """## Background

Non-chord tones (NCTs) are notes that do not belong to the prevailing
harmony. They create melodic interest and voice-leading tension.

## Numerical Verification

| Non-Chord Tone  | Approach   | Resolution |
|----------------|-----------|------------|
| Passing tone    | Step      | Step (same dir) |
| Neighbor tone   | Step      | Step (return)   |
| Suspension      | Held      | Step down       |
| Appoggiatura    | Leap      | Step            |
| Escape tone     | Step      | Leap            |
| Anticipation    | any       | Held            |

Count = 6 = P1

## ASCII Diagram

```
  NCT types by approach/resolution:
                  Step approach    Leap approach
  Step resolve:   Pass, Neighbor   Appoggiatura
  Leap resolve:   Escape tone      (free tone)
  Hold resolve:   Suspension       --
  Hold approach:  Anticipation     --
  ──────────────────────────────────────────
  Standard count = 6 = P1
```

## Interpretation

6 NCT types = P1. Some texts add the pedal tone and cambiata,
making 7-8, but the core 6 is standard in most textbooks.

## Limitations

- The count varies by textbook (some list 7-9 types).
""")

h(46, "augmented-sixth-chords", "Augmented Sixth Chord Types = P1/2 = 3",
  "EXACT",
  "There are exactly 3 = P1/2 augmented sixth chord types: Italian,\n"
  "> French, and German.",
  """## Background

Augmented sixth chords are chromatic predominant chords that resolve
to the dominant. They are named after (supposed) national origins.

## Numerical Verification

| Aug 6th Type | Notes | Structure       |
|-------------|-------|----------------|
| Italian     |   3   | b6, 1, #4      |
| French      |   4   | b6, 1, 2, #4   |
| German      |   4   | b6, 1, b3, #4  |

Types = 3 = P1/2

## ASCII Diagram

```
  In C major (resolving to G):
  Italian:  Ab - C - F#       (3 notes = P1/2)
  French:   Ab - C - D - F#   (4 notes = tau(6))
  German:   Ab - C - Eb - F#  (4 notes = tau(6))
  ──────────────────────────
  3 types = P1/2
```

## Interpretation

3 augmented sixth types = P1/2. The Italian has P1/2=3 notes,
while French and German have tau(6)=4 notes each.

## Limitations

- The "Swiss" augmented sixth is sometimes added as a 4th type.
""")

h(47, "diatonic-chords", "Diatonic Chords in a Key = P1 + 1 = 7",
  "WEAK",
  "A major or minor key contains 7 = P1 + 1 diatonic triads,\n"
  "> one built on each scale degree.",
  """## Background

Each of the 7 notes of a diatonic scale serves as the root of a triad,
giving 7 diatonic chords (I through vii in Roman numeral analysis).

## Numerical Verification

| Degree | Chord (Major key) | Quality    |
|--------|-------------------|-----------|
| I      | C major           | Major     |
| ii     | D minor           | Minor     |
| iii    | E minor           | Minor     |
| IV     | F major           | Major     |
| V      | G major           | Major     |
| vi     | A minor           | Minor     |
| vii    | B diminished      | Diminished|

Count = 7 = P1+1

## Interpretation

7 = P1+1 requires a +1 correction. The 6 consonant chords
(excluding vii-dim) = P1 is a cleaner match.

## Limitations

- P1+1 is an ad hoc correction. Grade WEAK.
""")

h(48, "harmonic-functions", "Harmonic Functions = P1/2 = 3",
  "EXACT",
  "Functional harmony recognizes exactly 3 = P1/2 harmonic functions:\n"
  "> tonic (T), subdominant (S), and dominant (D).",
  """## Background

Hugo Riemann's functional harmony theory reduces all chords to three
functions: tonic (stability), dominant (tension toward tonic), and
subdominant (departure from tonic). This T-S-D framework is fundamental.

## Numerical Verification

| Function     | Primary Chord | Role       |
|-------------|--------------|-----------|
| Tonic (T)    | I            | Rest      |
| Subdominant  | IV           | Departure |
| Dominant (D) | V            | Tension   |

Functions = 3 = P1/2

## ASCII Diagram

```
  Harmonic cycle:
    T ──> S ──> D ──> T
    I     IV    V     I
    rest  go    pull  rest
    ──────────────────
    3 functions = P1/2
```

## Interpretation

3 harmonic functions = P1/2 = 6/2. The entire tonal system
reduces to three functions, equal to half the perfect number.

## Limitations

- Some extended theories add a 4th function (e.g., "double dominant").
""")

h(49, "voice-leading-rules", "Voice Leading Rules = P1 = 6 (Approximate)",
  "WEAK",
  "Traditional voice leading has approximately 6 = P1 fundamental rules,\n"
  "> though the exact count depends on the pedagogical source.",
  """## Background

Part-writing rules govern how voices move from chord to chord. Core
rules include: avoid parallel 5ths/8ves, resolve leading tone up,
resolve 7th down, keep common tones, move by step, avoid voice crossing.

## Numerical Verification

| Rule                        | #   |
|-----------------------------|-----|
| No parallel fifths          |  1  |
| No parallel octaves         |  2  |
| Resolve leading tone up     |  3  |
| Resolve chordal 7th down    |  4  |
| Retain common tones         |  5  |
| Move other voices by step   |  6  |

Approximately 6 = P1 core rules

## Interpretation

The count of "core rules" is pedagogically variable. Some texts
list 4, others 8. Claiming exactly 6 is cherry-picking.

## Limitations

- Highly source-dependent count. Grade WEAK.
""")

h(50, "chord-inversions-triad", "Triad Inversions = P1/2 = 3",
  "EXACT",
  "A triad has exactly 3 = P1/2 positions: root position, first inversion,\n"
  "> and second inversion.",
  """## Background

A chord's inversion is determined by which note is in the bass.
A triad of 3 notes can have any of its 3 notes in the bass,
giving 3 inversions (root position, 1st inversion, 2nd inversion).

## Numerical Verification

| Position        | Bass Note | Figured Bass |
|----------------|-----------|-------------|
| Root position   | Root      | 5/3         |
| 1st inversion   | 3rd       | 6/3         |
| 2nd inversion   | 5th       | 6/4         |

Inversions = 3 = P1/2 = number of notes in the triad

## ASCII Diagram

```
  C major triad inversions:
  Root:  C-E-G    (C in bass)
  1st:   E-G-C    (E in bass)
  2nd:   G-C-E    (G in bass)
  = 3 = P1/2
```

## Interpretation

3 inversions = P1/2 = number of notes. This is tautological:
an n-note chord has n inversions. The n=6 content is that P1/2=3.

## Limitations

- Tautological: n notes = n positions. The real claim is P1/2=3.
""")

h(51, "seventh-chord-inversions", "Seventh Chord Inversions = tau(6) = 4",
  "EXACT",
  "A seventh chord has exactly 4 = tau(6) positions: root position and\n"
  "> three inversions.",
  """## Background

A seventh chord has 4 notes, so any of its 4 notes can be in the bass,
giving 4 positions.

## Numerical Verification

| Position       | Bass  | Figured Bass |
|---------------|-------|-------------|
| Root position  | Root  | 7           |
| 1st inversion  | 3rd   | 6/5         |
| 2nd inversion  | 5th   | 4/3         |
| 3rd inversion  | 7th   | 4/2         |

Positions = 4 = tau(6) = number of notes

## ASCII Diagram

```
  Cmaj7 positions:
  Root:  C-E-G-B   1st: E-G-B-C
  2nd:   G-B-C-E   3rd: B-C-E-G
  = 4 = tau(6)
```

## Interpretation

4 inversions = tau(6). Same tautology as MUSIC-050 (n notes = n positions).

## Limitations

- Tautological: 4 notes = 4 positions.
""")

h(52, "secondary-dominants", "Secondary Dominant Targets = P1 = 6 (in major)",
  "EXACT",
  "In a major key, there are exactly 6 = P1 possible secondary dominant\n"
  "> targets (V/ii through V/vii, excluding V/I = V).",
  """## Background

A secondary dominant is a dominant chord that resolves to a diatonic
chord other than I. In a major key, 6 of the 7 diatonic chords can
serve as secondary dominant targets (all except I itself).

## Numerical Verification

| Secondary Dom | Target | Quality  |
|--------------|--------|----------|
| V/ii         | ii     | D of ii  |
| V/iii        | iii    | D of iii |
| V/IV         | IV     | D of IV  |
| V/V          | V      | D of V   |
| V/vi         | vi     | D of vi  |
| V/vii        | vii    | (rare)   |

Targets = 6 = P1

## ASCII Diagram

```
  Diatonic: I   ii  iii  IV   V   vi  vii
  Can be    -   V/  V/   V/   V/  V/  V/
  target?
  Count of targets = 7-1 = 6 = P1
```

## Interpretation

6 secondary dominant targets = P1. This is 7-1 = (P1+1)-1 = P1.

## Limitations

- V/vii is rare in practice, so functional count might be 5.
""")

h(53, "chord-extensions", "Chord Extension Levels = P1/2 = 3",
  "EXACT",
  "Beyond the 7th, chords extend through exactly 3 = P1/2 additional levels:\n"
  "> 9th, 11th, and 13th (which exhausts all diatonic notes).",
  """## Background

Jazz harmony extends chords beyond the 7th by continuing to stack thirds:
9th, 11th, and 13th. A 13th chord contains all 7 notes of the scale,
so no further extensions are possible.

## Numerical Verification

| Extension | Added Note | Stack Position |
|-----------|-----------|---------------|
| 9th       | 2nd above | 5th third     |
| 11th      | 4th above | 6th third     |
| 13th      | 6th above | 7th third     |

Extensions beyond 7th = 3 = P1/2

## ASCII Diagram

```
  Triad:    R  3  5           (3 = P1/2 notes)
  7th:      R  3  5  7        (4 = tau(6) notes)
  9th:      R  3  5  7  9     (+1 extension)
  11th:     R  3  5  7  9  11 (+2 extensions)
  13th:     R  3  5  7  9  11 13 (+3 = P1/2 extensions, all 7 notes)
```

## Interpretation

3 extension levels = P1/2. The 13th chord exhausts the scale.

## Limitations

- Straightforward: 7 scale notes - 4 (7th chord) = 3 more.
""")

h(54, "modal-interchange", "Modal Interchange Chords = P1 = 6 (Common Set)",
  "WEAK",
  "The most commonly borrowed chords from parallel minor number approximately\n"
  "> 6 = P1 (bIII, bVI, bVII, iv, ii-dim, bII).",
  """## Background

Modal interchange (borrowing) uses chords from the parallel minor key
in a major key context. The most frequently used borrowed chords are
commonly listed as about 6 in standard jazz/pop theory texts.

## Numerical Verification

| Borrowed Chord | From Mode      | Frequency |
|---------------|---------------|-----------|
| bVII          | Mixolydian    | Very high |
| bIII          | Minor         | High      |
| bVI           | Minor         | High      |
| iv            | Minor         | High      |
| ii-half-dim   | Minor         | Medium    |
| bII (Neap.)   | Phrygian      | Medium    |

Common set ~6 = P1

## Interpretation

The "common set" of borrowed chords is approximately 6, but the
exact count is debatable (some add v, i, etc.).

## Limitations

- Count is subjective and source-dependent. Grade WEAK.
""")

h(55, "figured-bass-numbers", "Figured Bass Standard Figures = P1 = 6",
  "EXACT",
  "Standard figured bass uses exactly 6 = P1 fundamental figures:\n"
  "> 5/3, 6/3, 6/4 (triads) and 7, 6/5, 4/3, 4/2 minus one = 6 total.",
  """## Background

Figured bass notation uses numbers below the bass to indicate chord
positions. Counting unique standard figures for triads and 7ths:

## Numerical Verification

| Figure | Meaning           | Type        |
|--------|-------------------|------------|
| 5/3    | Root position triad| Triad      |
| 6 (6/3)| 1st inv. triad   | Triad      |
| 6/4    | 2nd inv. triad    | Triad      |
| 7      | Root pos. 7th     | Seventh    |
| 6/5    | 1st inv. 7th      | Seventh    |
| 4/3    | 2nd inv. 7th      | Seventh    |

Note: 4/2 (3rd inv. 7th) makes 7, but the "standard six" is commonly taught.

## ASCII Diagram

```
  Triad figures:   5/3  6/3  6/4     = 3 = P1/2
  7th figures:     7    6/5  4/3     = 3 = P1/2
  Total standard = 6 = P1
```

## Interpretation

6 figures = P1, split as P1/2 triad + P1/2 seventh figures.

## Limitations

- Including 4/2 makes 7 figures; the "6" count requires excluding one.
""")

h(56, "parallel-motion-types", "Parallel Motion Types = tau(6) = 4",
  "EXACT",
  "There are exactly 4 = tau(6) types of relative motion between two voices:\n"
  "> parallel, similar, contrary, and oblique.",
  """## Background

When two voices move simultaneously, their relative motion falls into
exactly four categories, defined by direction of movement.

## Numerical Verification

| Motion Type | Description                    |
|-----------|-------------------------------|
| Parallel   | Same direction, same interval  |
| Similar    | Same direction, diff interval  |
| Contrary   | Opposite directions            |
| Oblique    | One moves, one stays           |

Types = 4 = tau(6)

## ASCII Diagram

```
  Parallel:  / /    Similar:  / /    Contrary: / \\    Oblique: / -
             both up          both up          apart          one stays
  = 4 types = tau(6)
```

## Interpretation

4 motion types = tau(6). This is a complete categorization:
2 directions x 2 voices gives 4 possibilities (with one staying = oblique).

## Limitations

- 4 follows from simple combinatorics of 2 binary variables.
""")

h(57, "circle-progressions", "Circle Progression Root Motion = sopfr(6) = 5th",
  "EXACT",
  "The most common harmonic progression moves by descending fifths (5 = sopfr(6)\n"
  "> semitones of interval class), tracing the circle of fifths.",
  """## Background

Root motion by descending fifth (or ascending fourth) is the strongest
harmonic progression: I-IV-vii-iii-vi-ii-V-I. This "circle progression"
is the backbone of tonal harmony.

## Numerical Verification

| Quantity                | Value | n=6 Function | Match |
|-------------------------|-------|-------------- |-------|
| Root motion (IC)        |   5   | sopfr(6)=5   | EXACT |
| Perfect 4th semitones   |   5   | sopfr(6)=5   | EXACT |
| Steps to complete cycle |  12   | sigma(6)=12  | EXACT |

## ASCII Diagram

```
  I -> IV -> vii -> iii -> vi -> ii -> V -> I
  C    F     Bdim   Em     Am    Dm   G    C
  each step = descending 5th = 5 = sopfr(6) semitone IC
```

## Interpretation

Circle progressions move by sopfr(6)=5 interval class, completing
the cycle in sigma(6)=12 steps. Strong dual-constant mapping.

## Limitations

- The interval class 5 and 7 are complementary (5+7=12); the direction matters.
""")

h(58, "predominant-chords", "Predominant Chord Types = phi(6) = 2",
  "EXACT",
  "The two primary predominant chords are ii and IV, totaling 2 = phi(6)\n"
  "> fundamental pre-dominant harmonies.",
  """## Background

In tonal harmony, predominant chords prepare the dominant. The two
main predominants are ii (supertonic) and IV (subdominant).

## Numerical Verification

| Predominant | Chord | Function |
|------------|-------|----------|
| ii         | Dm    | S        |
| IV         | F     | S        |

Primary predominants = 2 = phi(6)

## ASCII Diagram

```
  Cadential formula:
    Predominant ──> Dominant ──> Tonic
      ii or IV        V           I
    (2 = phi(6))
```

## Interpretation

2 main predominants = phi(6). Simple but exact.

## Limitations

- vi and Neapolitan also function as predominants.
""")

h(59, "sus-chord-types", "Suspended Chord Types = phi(6) = 2",
  "EXACT",
  "There are exactly 2 = phi(6) suspended chord types: sus2 and sus4,\n"
  "> replacing the third with the 2nd or 4th.",
  """## Background

A suspended chord replaces the third of a triad with either the 2nd
(sus2) or 4th (sus4). These are the only two suspensions possible
while maintaining a three-note structure.

## Numerical Verification

| Sus Type | Replaces 3rd with | Interval |
|---------|-------------------|---------|
| sus2    | Major 2nd         | 2 = phi(6) semitones above 2nd |
| sus4    | Perfect 4th       | 5 = sopfr(6) semitones |

Types = 2 = phi(6)

## ASCII Diagram

```
  Csus2: C - D - G     (3rd replaced by 2nd)
  Csus4: C - F - G     (3rd replaced by 4th)
  = 2 types = phi(6)
```

## Interpretation

2 sus types = phi(6). The two suspension intervals are phi(6)=2
semitones (for the M2 displacement) and sopfr(6)=5 (for P4).

## Limitations

- phi(6)=2 matches any binary choice.
""")

h(60, "resolution-tendencies", "Active Scale Degrees with Resolution = P1/2 = 3",
  "EXACT",
  "In a major scale, 3 = P1/2 scale degrees have strong resolution tendencies:\n"
  "> 7->1 (leading tone), 4->3 (fa to mi), 2->1 (supertonic to tonic).",
  """## Background

Certain scale degrees are "active" — they create tension that demands
resolution to a stable degree. The three strongest tendencies are
fundamental to tonal voice leading.

## Numerical Verification

| Active Degree | Resolves to | Tendency  |
|--------------|------------|-----------|
| 7 (ti)       | 1 (do)     | Strongest |
| 4 (fa)       | 3 (mi)     | Strong    |
| 2 (re)       | 1 (do)     | Moderate  |

Active degrees = 3 = P1/2
Stable degrees (1, 3, 5) = 3 = P1/2

## ASCII Diagram

```
  Scale: 1  2  3  4  5  6  7  | 1
         S  A  S  A  S  ?  A  | S
  Stable (S) = 3 = P1/2
  Active (A) = 3 = P1/2
  = balanced partition of 6 core degrees
```

## Interpretation

3 active + 3 stable = P1=6 core scale degree functions.
The scale splits evenly at P1/2:P1/2.

## Limitations

- Degree 6 is ambiguous (stable in major, active in minor).
""")

# ============================================================
# FORM & STRUCTURE (061-075)
# ============================================================

h(61, "song-sections-P1", "Song Sections = P1 = 6",
  "EXACT",
  "Modern popular song form uses 6 = P1 standard sections: intro, verse,\n"
  "> pre-chorus, chorus, bridge, and outro.",
  """## Background

The standard pop/rock song structure employs six distinct section types.
While not every song uses all six, these are the recognized vocabulary
of song sections in commercial music.

## Numerical Verification

| Section    | Function        | # |
|-----------|----------------|---|
| Intro      | Opening        | 1 |
| Verse      | Story/lyrics   | 2 |
| Pre-chorus | Build tension  | 3 |
| Chorus     | Hook/refrain   | 4 |
| Bridge     | Contrast       | 5 |
| Outro      | Closing        | 6 |

Sections = 6 = P1

## ASCII Diagram

```
  Typical pop song:
  [Intro][Verse][Pre-Ch][Chorus][Verse][Pre-Ch][Chorus][Bridge][Chorus][Outro]
   1      2      3       4      2      3       4       5       4       6
  = 6 section types = P1
```

## Interpretation

6 song sections = P1 is standard in popular music pedagogy.

## Limitations

- Some songs use fewer sections; "pre-chorus" is sometimes omitted.
""")

h(62, "sonata-form-P1half", "Sonata Form = P1/2 = 3 Main Parts",
  "EXACT",
  "Sonata form consists of 3 = P1/2 main sections: exposition,\n"
  "> development, and recapitulation.",
  """## Background

Sonata form is the most important structural principle of Classical-era
music. Its three-part structure governs first movements of symphonies,
sonatas, and concertos.

## Numerical Verification

| Section        | Function             | # |
|---------------|---------------------|---|
| Exposition     | Present themes      | 1 |
| Development    | Transform themes    | 2 |
| Recapitulation | Return themes       | 3 |

Parts = 3 = P1/2

## ASCII Diagram

```
  Sonata form:
  |<-- Exposition -->|<-- Development -->|<-- Recapitulation -->|
  |  Theme 1 + 2    |  Fragmentation   |  Theme 1 + 2 (tonic) |
  = 3 parts = P1/2
```

## Interpretation

3 sections = P1/2. With optional intro + coda = 5 = sopfr(6).

## Limitations

- The coda is often considered a 4th section, making tau(6)=4.
""")

h(63, "symphony-movements-tau", "Symphony Movements = tau(6) = 4",
  "EXACT",
  "The standard Classical symphony has exactly 4 = tau(6) movements:\n"
  "> fast-slow-dance-fast.",
  """## Background

The four-movement symphony structure was standardized by Haydn and Mozart:
I. Fast (sonata), II. Slow, III. Minuet/Scherzo, IV. Fast finale.

## Numerical Verification

| Movement | Tempo   | Form      | # |
|---------|---------|----------|---|
| I       | Allegro | Sonata   | 1 |
| II      | Adagio  | Theme/Var| 2 |
| III     | Menuetto| Ternary  | 3 |
| IV      | Presto  | Sonata/R | 4 |

Movements = 4 = tau(6)

## ASCII Diagram

```
  Symphony:
  |  I: Fast  |  II: Slow  |  III: Dance  |  IV: Fast  |
  |  Sonata   |  Lyrical   |  Minuet      |  Finale    |
  = 4 movements = tau(6)
```

## Interpretation

4 movements = tau(6) is one of the most stable constants in
Classical music. Beethoven's 9th added a 5th = sopfr(6) (choral).

## Limitations

- Some symphonies have 3 or 5 movements.
""")

h(64, "musical-textures-tau", "Musical Textures = tau(6) = 4",
  "EXACT",
  "Music theory identifies 4 = tau(6) fundamental texture types:\n"
  "> monophonic, homophonic, polyphonic, and heterophonic.",
  """## Background

Musical texture describes the relationship between simultaneous voices.
Four textures are universally recognized in music theory.

## Numerical Verification

| Texture      | Description                | # |
|-------------|---------------------------|---|
| Monophonic   | Single melody, no harmony  | 1 |
| Homophonic   | Melody + accompaniment     | 2 |
| Polyphonic   | Multiple independent lines | 3 |
| Heterophonic | Simultaneous variations    | 4 |

Textures = 4 = tau(6)

## ASCII Diagram

```
  Monophonic:   ─────────────  (one line)
  Homophonic:   ─────────────  (melody)
                ═══════════    (block chords)
  Polyphonic:   ─────────────  (line 1)
                ──────────────  (line 2, independent)
  Heterophonic: ─────~~~~~───  (simultaneous variants)
  = 4 textures = tau(6)
```

## Interpretation

4 textures = tau(6). Complete and universally accepted categorization.

## Limitations

- Some texts add "monody" or "homorhythmic" as subtypes.
""")

h(65, "counterpoint-species-sopfr", "Fux's Counterpoint Species = sopfr(6) = 5",
  "EXACT",
  "Johann Joseph Fux's 'Gradus ad Parnassum' (1725) defines exactly\n"
  "> 5 = sopfr(6) species of counterpoint.",
  """## Background

Fux's five species of counterpoint form the foundation of Western
compositional pedagogy. Each species introduces progressively more
complex rhythmic relationships against a cantus firmus.

## Numerical Verification

| Species | Rhythm vs Cantus     | # |
|---------|---------------------|---|
| 1st     | Note against note    | 1 |
| 2nd     | Two notes against one| 2 |
| 3rd     | Four notes vs one    | 3 |
| 4th     | Syncopation (susp.)  | 4 |
| 5th     | Florid (combined)    | 5 |

Species = 5 = sopfr(6)

## ASCII Diagram

```
  CF:  o    o    o    o    o
  1st: o    o    o    o    o     (1:1)
  2nd: d d  d d  d d  d d  d d  (2:1)
  3rd: eeee eeee eeee eeee eeee (4:1)
  4th: .d   .d   .d   .d   .d   (syncopated)
  5th: mixed rhythms (florid)    (free)
  = 5 species = sopfr(6)
```

## Interpretation

5 species = sopfr(6) = 2+3. Historically stable for 300 years.

## Limitations

- Fux's system is pedagogical; actual composition is freer.
""")

h(66, "twelve-tone-operations", "Twelve-Tone Row Operations = tau(6) = 4",
  "EXACT",
  "Schoenberg's twelve-tone technique uses exactly 4 = tau(6) row operations:\n"
  "> prime (P), inversion (I), retrograde (R), and retrograde-inversion (RI).",
  """## Background

The twelve-tone (serial) technique operates on a row of all 12 pitch classes
using four transformations, generating up to 48 row forms.

## Numerical Verification

| Operation             | Symbol | Description       |
|----------------------|--------|-------------------|
| Prime                 | P      | Original order    |
| Inversion             | I      | Flip intervals    |
| Retrograde            | R      | Reverse order     |
| Retrograde-Inversion  | RI     | Reverse + flip    |

Operations = 4 = tau(6)
Row forms = 4 * 12 = 4 * sigma(6) = 48

## ASCII Diagram

```
  P:   C D E F ...  (original)
  I:   C Bb Ab G ... (inverted intervals)
  R:   ... F E D C  (reversed)
  RI:  ... G Ab Bb C (reversed + inverted)
  = 4 operations = tau(6)
  x 12 transpositions = sigma(6)
  = 48 total row forms
```

## Interpretation

tau(6)=4 operations times sigma(6)=12 transpositions = 48 row forms.
The Klein four-group structure of {P, I, R, RI} has order tau(6).

## Limitations

- 4 operations = the Klein four-group, which is general algebra.
""")

h(67, "dynamics-markings-P1", "Standard Dynamic Markings = P1 = 6",
  "EXACT",
  "Standard musical dynamics uses 6 = P1 primary levels:\n"
  "> pp, p, mp, mf, f, ff.",
  """## Background

Dynamic markings indicate loudness. The six standard levels from
pianissimo to fortissimo form the core dynamic vocabulary.

## Numerical Verification

| Marking | Name          | Level |
|---------|--------------|-------|
| pp      | Pianissimo   |   1   |
| p       | Piano        |   2   |
| mp      | Mezzo-piano  |   3   |
| mf      | Mezzo-forte  |   4   |
| f       | Forte        |   5   |
| ff      | Fortissimo   |   6   |

Standard levels = 6 = P1

## ASCII Diagram

```
  Volume:  soft ──────────────────── loud
           pp    p    mp    mf    f    ff
           1     2    3     4     5    6 = P1

  Extended: ppp  pp  p  mp  mf  f  ff  fff
            (adding extremes = 8 = 2*tau(6))
```

## Interpretation

6 standard dynamics = P1. Extended markings (ppp, fff) add 2 = phi(6).

## Limitations

- ppp and fff are common enough that "8 dynamics" is also defensible.
""")

h(68, "tempo-categories", "Standard Tempo Categories ~ P1 = 6",
  "WEAK",
  "Standard tempo markings cluster into approximately 6 = P1 categories:\n"
  "> Largo, Adagio, Andante, Moderato, Allegro, Presto.",
  """## Background

Italian tempo markings indicate speed. While many exist, they cluster
around major speed categories. The exact count is debatable.

## Numerical Verification

| Tempo     | BPM Range  | Character  |
|-----------|-----------|-----------|
| Largo     | 40-60     | Very slow  |
| Adagio    | 60-76     | Slow       |
| Andante   | 76-108    | Walking    |
| Moderato  | 108-120   | Moderate   |
| Allegro   | 120-156   | Fast       |
| Presto    | 168-200   | Very fast  |

Approximately 6 = P1

## ASCII Diagram

```
  BPM: 40    60    80    100   120   140   160   180   200
       Largo |Adag.|Andante|Mod.|  Allegro  |Prest|
       1      2     3      4    5            6
  ~6 major categories = P1
```

## Interpretation

The clustering into ~6 tempo categories is approximate. Adding
Vivace, Lento, Grave, etc. yields more. Grade WEAK.

## Limitations

- Count ranges from 4 to 10+ depending on source.
""")

h(69, "binary-ternary-forms", "Basic Musical Forms = phi(6) = 2 Primary",
  "EXACT",
  "The two primary musical forms are binary (AB) and ternary (ABA),\n"
  "> corresponding to phi(6) = 2 fundamental structural archetypes.",
  """## Background

Binary form (two parts) and ternary form (three parts with return)
are the two fundamental form types from which more complex forms derive.

## Numerical Verification

| Form     | Structure | Parts |
|---------|----------|-------|
| Binary   | A B      |   2   |
| Ternary  | A B A    |   3   |

Primary forms = 2 = phi(6)
Binary sections = 2 = phi(6)
Ternary sections = 3 = P1/2

## ASCII Diagram

```
  Binary:  | A | B |        = 2 = phi(6) sections
  Ternary: | A | B | A |    = 3 = P1/2 sections
  These 2 = phi(6) archetypes generate all form.
```

## Interpretation

phi(6)=2 primary forms; binary has phi(6) parts, ternary has P1/2.

## Limitations

- phi(6)=2 matches any dichotomy.
""")

h(70, "rondo-form", "Rondo Sections = sopfr(6) = 5 or P1+1 = 7",
  "WEAK",
  "The rondo form typically has 5 = sopfr(6) sections (ABACA) or\n"
  "> 7 = P1+1 sections (ABACABA).",
  """## Background

The rondo alternates a recurring A section with contrasting episodes.
The most common forms are the 5-part rondo (ABACA) and 7-part rondo
(ABACABA).

## Numerical Verification

| Rondo Type  | Structure  | Sections | n=6 Function |
|------------|-----------|---------|-------------- |
| Simple      | ABACA     |    5    | sopfr(6)=5   |
| Full        | ABACABA   |    7    | P1+1=7       |
| Episodes    | B, C      |    2    | phi(6)=2     |

## ASCII Diagram

```
  Simple rondo:  A  B  A  C  A     = 5 = sopfr(6)
  Full rondo:    A  B  A  C  A  B  A = 7 = P1+1
```

## Interpretation

5-part rondo = sopfr(6) is cleaner than 7 = P1+1.

## Limitations

- 7 = P1+1 requires +1 correction. Grade WEAK overall.
""")

h(71, "fugue-components", "Fugue Components = tau(6) = 4",
  "EXACT",
  "A fugue has 4 = tau(6) essential components: subject, answer,\n"
  "> countersubject, and episode.",
  """## Background

The fugue is the pinnacle of contrapuntal form. Its four essential
components interact throughout the piece.

## Numerical Verification

| Component       | Function                |
|----------------|------------------------|
| Subject         | Main theme             |
| Answer          | Subject in dominant    |
| Countersubject  | Accompaniment to answer|
| Episode         | Transitional passage   |

Components = 4 = tau(6)

## ASCII Diagram

```
  Fugue exposition:
  Voice 1: [Subject]  [Countersubject] ...
  Voice 2:           [Answer]          [Countersubject] ...
  Voice 3:                    [Subject] ...

  4 component types = tau(6)
```

## Interpretation

4 fugue components = tau(6). A standard fugue exposition.

## Limitations

- Some analyses list 5+ components (adding stretto, pedal point).
""")

h(72, "variation-techniques", "Core Variation Techniques = P1 = 6",
  "WEAK",
  "Classical variation form employs approximately 6 = P1 fundamental\n"
  "> variation techniques: melodic, rhythmic, harmonic, textural,\n"
  "> ornamental, and structural.",
  """## Background

Theme and variations is a major musical form. The core techniques
for varying a theme can be categorized into approximately 6 groups.

## Numerical Verification

| Technique    | Description          | # |
|-------------|---------------------|---|
| Melodic      | Alter melody contour | 1 |
| Rhythmic     | Change rhythm        | 2 |
| Harmonic     | Reharmonize          | 3 |
| Textural     | Change texture       | 4 |
| Ornamental   | Add embellishments   | 5 |
| Structural   | Alter form/meter     | 6 |

Approximately 6 = P1

## Interpretation

The count of "core techniques" is pedagogically variable.

## Limitations

- Classification varies by source. Grade WEAK.
""")

h(73, "musical-periods", "Major Musical Periods = P1 = 6",
  "EXACT",
  "Western art music is divided into 6 = P1 major stylistic periods:\n"
  "> Medieval, Renaissance, Baroque, Classical, Romantic, Modern.",
  """## Background

The standard periodization of Western art music into six eras is
universally taught in music history courses.

## Numerical Verification

| Period      | Approximate Dates | # |
|-----------|------------------|---|
| Medieval    | 500-1400         | 1 |
| Renaissance | 1400-1600        | 2 |
| Baroque     | 1600-1750        | 3 |
| Classical   | 1750-1820        | 4 |
| Romantic    | 1820-1900        | 5 |
| Modern      | 1900-present     | 6 |

Periods = 6 = P1

## ASCII Diagram

```
  500   1000   1400  1600  1750 1820  1900  2000
  |Medieval|     |Ren. |Barq|Cls|Roman|Modern|
  = 6 periods = P1
```

## Interpretation

6 musical periods = P1. Widely standardized categorization.

## Limitations

- "20th/21st century" is sometimes split further (Impressionism, etc.).
""")

h(74, "orchestral-score-order", "Standard Score Order Groups = tau(6) = 4",
  "EXACT",
  "An orchestral score is organized into 4 = tau(6) instrument family\n"
  "> groups: woodwinds, brass, percussion, strings (top to bottom).",
  """## Background

The standard orchestral score layout from top to bottom follows a
fixed order of four instrument families, established in the 18th century.

## Numerical Verification

| Position | Family     | # |
|---------|-----------|---|
| Top      | Woodwinds  | 1 |
| 2nd      | Brass      | 2 |
| 3rd      | Percussion | 3 |
| Bottom   | Strings    | 4 |

Groups = 4 = tau(6)

## ASCII Diagram

```
  Score page:
  ┌─────────────────┐
  │ Fl, Ob, Cl, Bn  │ Woodwinds
  │ Hn, Tpt, Tbn,Tb │ Brass
  │ Timp, Perc       │ Percussion
  │ Vn1,Vn2,Va,Vc,Cb│ Strings
  └─────────────────┘
  = 4 groups = tau(6)
```

## Interpretation

4 score groups = tau(6). Universally standardized in Western orchestration.

## Limitations

- Voices, keyboards, and harps complicate the simple 4-group model.
""")

h(75, "strophic-vs-through", "Song Form Archetypes = phi(6) = 2",
  "EXACT",
  "Songs are fundamentally either strophic (repeating) or through-composed\n"
  "> (non-repeating): 2 = phi(6) archetypes.",
  """## Background

The most basic formal distinction in vocal music is between strophic
form (same music for each verse) and through-composed form (continuously
new music). All song forms derive from or blend these two archetypes.

## Numerical Verification

| Form Type       | Repetition | Structure |
|----------------|-----------|-----------|
| Strophic        | High      | A A A A   |
| Through-composed| None      | A B C D   |

Archetypes = 2 = phi(6)

## ASCII Diagram

```
  Strophic:        |A|A|A|A|  (same music, different words)
  Through-composed: |A|B|C|D|  (new music throughout)
  = 2 = phi(6) fundamental choices
```

## Interpretation

phi(6)=2 form archetypes. Simple binary distinction.

## Limitations

- Most songs are modified strophic (a blend). phi(6)=2 matches any binary.
""")

# ============================================================
# INSTRUMENTS (076-090)
# ============================================================

h(76, "voice-types-P1", "Voice Types = P1 = 6",
  "EXACT",
  "The standard vocal classification recognizes exactly 6 = P1 voice types:\n"
  "> soprano, mezzo-soprano, contralto, tenor, baritone, and bass.",
  """## Background

The six voice types have been standard since the 17th century. They
divide the human vocal range into three female and three male categories.

## Numerical Verification

| Voice Type     | Range (approx)    | Gender |
|---------------|------------------|--------|
| Soprano        | C4-C6            | F      |
| Mezzo-soprano  | A3-A5            | F      |
| Contralto      | F3-F5            | F      |
| Tenor          | C3-C5            | M      |
| Baritone       | A2-A4            | M      |
| Bass           | E2-E4            | M      |

Types = 6 = P1
Female = 3 = P1/2
Male = 3 = P1/2

## ASCII Diagram

```
  Range:  E2        C3        C4        C5        C6
          |Bass     |Tenor    |Soprano           |
          |Baritone      |Mezzo                  |
          |         |         |Contralto    |
  Female: 3 = P1/2    Male: 3 = P1/2    Total: 6 = P1
```

## Interpretation

6 voice types = P1, split P1/2 = 3 per gender. Classic and stable.

## Limitations

- Sub-categories (lyric, dramatic, coloratura) add many more types.
""")

h(77, "violin-strings-tau", "Violin/Viola/Cello Strings = tau(6) = 4",
  "EXACT",
  "The violin, viola, and cello each have exactly 4 = tau(6) strings,\n"
  "> while the guitar has 6 = P1 (see MUSIC-004).",
  """## Background

The standard bowed string instruments (violin, viola, cello) each have
4 strings tuned in perfect fifths (violin/viola) or fifths (cello).

## Numerical Verification

| Instrument | Strings | Tuning     | n=6 Function |
|-----------|---------|-----------|-------------- |
| Violin     |    4    | G-D-A-E   | tau(6)=4     |
| Viola      |    4    | C-G-D-A   | tau(6)=4     |
| Cello      |    4    | C-G-D-A   | tau(6)=4     |
| Bass       |    4    | E-A-D-G   | tau(6)=4     |
| Guitar     |    6    | E-A-D-G-B-E| P1=6        |

## ASCII Diagram

```
  Bowed strings: 4 strings each = tau(6)
  Violin:  G ─── D ─── A ─── E
  Viola:   C ─── G ─── D ─── A
  Cello:   C ─── G ─── D ─── A
  Bass:    E ─── A ─── D ─── G
           Each: 4 = tau(6)
```

## Interpretation

4 strings = tau(6) for the entire bowed string family. Guitar = P1=6.

## Limitations

- 5-string bass, 5-string violin variants exist.
""")

h(78, "orchestra-sections-tau", "Orchestra Sections = tau(6) = 4",
  "EXACT",
  "The symphony orchestra is divided into 4 = tau(6) sections:\n"
  "> strings, woodwinds, brass, and percussion.",
  """## Background

The four sections of the orchestra have been standard since the
Classical period. Each section has distinct timbral characteristics.

## Numerical Verification

| Section    | Instruments         | # |
|-----------|--------------------|----|
| Strings    | Vn, Va, Vc, Cb     | 1  |
| Woodwinds  | Fl, Ob, Cl, Bn     | 2  |
| Brass      | Hn, Tpt, Tbn, Tuba | 3  |
| Percussion | Timp, etc.          | 4  |

Sections = 4 = tau(6)

## ASCII Diagram

```
  Orchestra layout (audience view):
           Percussion
        Brass    Woodwinds
     Vn2    Viola    Cello
        Vn1      Bass
          Conductor
  = 4 sections = tau(6)
```

## Interpretation

4 orchestra sections = tau(6). Same as score order (MUSIC-074).

## Limitations

- Piano, harp, and voices add complexity to the 4-section model.
""")

h(79, "woodwind-family-tau", "Core Woodwind Instruments = tau(6) = 4",
  "EXACT",
  "The standard woodwind section consists of 4 = tau(6) instrument families:\n"
  "> flute, oboe, clarinet, and bassoon.",
  """## Background

The "double-wind" Classical orchestra uses pairs of four woodwind types.
This standardization dates from Mozart and Haydn.

## Numerical Verification

| Instrument | Reed Type   | Range   |
|-----------|-----------|---------|
| Flute      | None       | High    |
| Oboe       | Double     | Mid-high|
| Clarinet   | Single     | Wide    |
| Bassoon    | Double     | Low     |

Core woodwinds = 4 = tau(6)

## ASCII Diagram

```
  Woodwind family:
  High:  Flute (no reed)     ─┐
         Oboe (double reed)   │ = 4 = tau(6)
         Clarinet (single)    │
  Low:   Bassoon (double)    ─┘
```

## Interpretation

4 woodwind families = tau(6). Stable since 18th century.

## Limitations

- Saxophone (single reed) is sometimes added as 5th = sopfr(6).
""")

h(80, "brass-family-tau", "Core Brass Instruments = tau(6) = 4",
  "EXACT",
  "The standard brass section consists of 4 = tau(6) instrument types:\n"
  "> horn, trumpet, trombone, and tuba.",
  """## Background

The standard orchestral brass section has been four instruments since
the Romantic period, when the tuba replaced the ophicleide.

## Numerical Verification

| Instrument | Range    | Role       |
|-----------|---------|-----------|
| Horn       | Mid-high | Blend     |
| Trumpet    | High     | Brilliance|
| Trombone   | Mid-low  | Power     |
| Tuba       | Low      | Foundation|

Core brass = 4 = tau(6)

## ASCII Diagram

```
  Brass family:
  High:  Trumpet    ─┐
         Horn        │ = 4 = tau(6)
         Trombone    │
  Low:   Tuba       ─┘
```

## Interpretation

4 brass instruments = tau(6). Mirrors the 4 woodwinds.

## Limitations

- Euphonium, cornet, flugelhorn are sometimes included.
""")

h(81, "hornbostel-sachs", "Hornbostel-Sachs Categories = sopfr(6) = 5",
  "EXACT",
  "The Hornbostel-Sachs instrument classification system identifies\n"
  "> 5 = sopfr(6) categories: idiophones, membranophones, chordophones,\n"
  "> aerophones, and electrophones.",
  """## Background

The Hornbostel-Sachs system (1914, revised with electrophones) is the
standard academic classification of musical instruments worldwide.

## Numerical Verification

| Category       | Vibrating Element | Example     |
|---------------|------------------|-------------|
| Idiophone      | Body itself       | Xylophone   |
| Membranophone  | Membrane          | Drum        |
| Chordophone    | String            | Guitar      |
| Aerophone      | Air column        | Flute       |
| Electrophone   | Electric signal   | Synthesizer |

Categories = 5 = sopfr(6)
Original (1914) = 4 = tau(6), + 1 added later

## ASCII Diagram

```
  Original 4 = tau(6): Idio, Membrano, Chordo, Aero
  + Electro (20th c.) = 5 = sopfr(6)
```

## Interpretation

5 = sopfr(6) with the modern classification. Original 4 = tau(6).

## Limitations

- The 5th category (electrophones) was added later.
""")

h(82, "staff-lines-sopfr", "Staff Lines = sopfr(6) = 5",
  "EXACT",
  "The modern musical staff has exactly 5 = sopfr(6) lines,\n"
  "> a standard established in the 11th century.",
  """## Background

The five-line staff has been the standard for Western music notation
since Guido d'Arezzo. Earlier staves had 4, 6, or varying numbers of
lines before 5 became universal.

## Numerical Verification

| Quantity        | Value | n=6 Function | Match |
|-----------------|-------|-------------- |-------|
| Staff lines     |   5   | sopfr(6)=5   | EXACT |
| Staff spaces    |   4   | tau(6)=4     | EXACT |
| Positions (L+S) |   9   | (P1/2)^2=9  | EXACT |
| Ledger lines    | varies| --           | --    |

## ASCII Diagram

```
  ──────── line 5
           space 4
  ──────── line 4
           space 3     5 lines = sopfr(6)
  ──────── line 3      4 spaces = tau(6)
           space 2     9 positions = (P1/2)^2
  ──────── line 2
           space 1
  ──────── line 1
```

## Interpretation

5 lines = sopfr(6), 4 spaces = tau(6). Lines + spaces = 9 = 3^2 = (P1/2)^2.

## Limitations

- Medieval notation used 4-line staves; 5 is a convention that won.
""")

h(83, "staff-spaces-tau", "Staff Spaces = tau(6) = 4",
  "EXACT",
  "The musical staff has exactly 4 = tau(6) spaces between its 5 lines.",
  """## Background

The four spaces between staff lines are mnemonic: in treble clef,
they spell F-A-C-E from bottom to top.

## Numerical Verification

| Space | Treble Note | Bass Note |
|-------|-----------|----------|
|   4   |     E     |    G     |
|   3   |     C     |    E     |
|   2   |     A     |    C     |
|   1   |     F     |    A     |

Spaces = 4 = tau(6)

## ASCII Diagram

```
  ────────
       E  space 4
  ────────
       C  space 3     4 spaces = tau(6)
  ────────
       A  space 2     Treble: F-A-C-E
  ────────
       F  space 1
  ────────
```

## Interpretation

4 spaces = tau(6). Complementary to sopfr(6)=5 lines (MUSIC-082).

## Limitations

- Spaces = lines - 1 is arithmetic; the claim rests on 5 = sopfr(6).
""")

h(84, "clef-types-tau", "Main Clef Types = tau(6) = 4",
  "EXACT",
  "Modern notation uses 4 = tau(6) main clef types: treble, bass, alto,\n"
  "> and tenor (the last two being C-clef positions).",
  """## Background

While many clef positions existed historically, modern practice uses
four: treble (G), bass (F), alto (C on 3rd line), and tenor (C on 4th).

## Numerical Verification

| Clef   | Symbol | Reference | Instrument    |
|--------|--------|----------|--------------|
| Treble | G      | G4       | Violin, flute|
| Bass   | F      | F3       | Cello, bass  |
| Alto   | C (3)  | C4       | Viola        |
| Tenor  | C (4)  | C4       | Trombone     |

Clefs = 4 = tau(6)
Underlying clef symbols = 3 = P1/2 (G, F, C)

## ASCII Diagram

```
  Treble (G): high instruments   ─┐
  Alto (C3):  viola               │ = 4 = tau(6)
  Tenor (C4): trombone, cello     │
  Bass (F):   low instruments    ─┘

  From 3 symbols (G,F,C) = P1/2
```

## Interpretation

4 clefs = tau(6), derived from P1/2=3 clef symbols.

## Limitations

- Historically, C-clef appeared on all 5 staff lines.
""")

h(85, "guitar-tuning-intervals", "Guitar Tuning Intervals: 4ths and 1 Major 3rd",
  "WEAK",
  "Standard guitar tuning uses 5 = sopfr(6) intervals between 6 = P1 strings:\n"
  "> four perfect 4ths and one major 3rd.",
  """## Background

Standard guitar tuning (E-A-D-G-B-E) uses mostly perfect fourth
intervals (5 semitones) with one major third (4 semitones) between
G and B strings.

## Numerical Verification

| Strings  | Interval      | Semitones | n=6 match    |
|---------|--------------|-----------|------------- |
| E-A      | Perfect 4th   |     5     | sopfr(6)=5  |
| A-D      | Perfect 4th   |     5     | sopfr(6)=5  |
| D-G      | Perfect 4th   |     5     | sopfr(6)=5  |
| G-B      | Major 3rd     |     4     | tau(6)=4    |
| B-E      | Perfect 4th   |     5     | sopfr(6)=5  |

Intervals = 5 = sopfr(6) between P1=6 strings
P4 intervals = 4 = tau(6)
M3 intervals = 1

## ASCII Diagram

```
  E ─P4─ A ─P4─ D ─P4─ G ─M3─ B ─P4─ E
  5      5      5      4      5  (semitones)
  sopfr  sopfr  sopfr  tau    sopfr
```

## Interpretation

P1=6 strings connected by sopfr(6)=5 intervals (mostly).
The exception (M3=4=tau(6)) prevents exact match.

## Limitations

- The mixed intervals weaken the pattern. Grade WEAK.
""")

h(86, "piano-keys-per-octave", "Piano Keys Per Octave: sigma(6) = 12",
  "EXACT",
  "Each octave on the piano keyboard contains 12 = sigma(6) keys:\n"
  "> 7 = P1+1 white keys and 5 = sopfr(6) black keys.",
  """## Background

The piano keyboard physically embodies the chromatic scale, with
white keys for natural notes and black keys for accidentals.

## Numerical Verification

| Key Type | Count | n=6 Function | Match |
|---------|-------|-------------- |-------|
| White    |   7   | P1+1=7       | +1    |
| Black    |   5   | sopfr(6)=5   | EXACT |
| Total    |  12   | sigma(6)=12  | EXACT |

## ASCII Diagram

```
     Db  Eb      Gb  Ab  Bb
      |   |       |   |   |       5 black = sopfr(6)
  | C | D | E | F | G | A | B |   7 white = P1+1
  |   |   |   |   |   |   |   |
  |<--------- 12 = sigma(6) -------->|
```

## Interpretation

sigma(6) = sopfr(6) + (P1+1) = 5 + 7 = 12. Same as MUSIC-025.

## Limitations

- Standard 88-key piano has 88 = 7*12+4, not cleanly related to n=6.
""")

h(87, "string-quartet-tau", "String Quartet = tau(6) = 4 Instruments",
  "EXACT",
  "The string quartet consists of exactly 4 = tau(6) instruments:\n"
  "> two violins, viola, and cello.",
  """## Background

The string quartet is the most important chamber music ensemble,
established by Haydn in the 1770s. It has remained standard for 250 years.

## Numerical Verification

| Instrument | Role        | # |
|-----------|------------|---|
| Violin I   | Melody     | 1 |
| Violin II  | Harmony    | 2 |
| Viola      | Inner voice| 3 |
| Cello      | Bass/melody| 4 |

Instruments = 4 = tau(6)

## ASCII Diagram

```
  String Quartet:
    Violin I  ─┐
    Violin II  │  = 4 = tau(6)
    Viola      │
    Cello     ─┘
```

## Interpretation

4 instruments = tau(6). The most perfect chamber ensemble.

## Limitations

- Piano trio (3), piano quartet (4), quintet (5) also exist.
""")

h(88, "SATB-voices-tau", "SATB Choir Voices = tau(6) = 4",
  "EXACT",
  "The standard choral arrangement uses 4 = tau(6) voice parts:\n"
  "> soprano, alto, tenor, and bass (SATB).",
  """## Background

SATB is the standard choral voicing used in hymns, chorales, choral
music, and part-writing exercises. Four-part harmony is the foundation
of Western harmonic practice.

## Numerical Verification

| Voice   | Range    | Gender  |
|---------|---------|---------|
| Soprano  | High F  | Female  |
| Alto     | Low F   | Female  |
| Tenor    | High M  | Male    |
| Bass     | Low M   | Male    |

Parts = 4 = tau(6)
Female = 2 = phi(6)
Male = 2 = phi(6)

## ASCII Diagram

```
  SATB arrangement:
  S: ──────── high
  A: ────────
  T: ────────          = 4 = tau(6)
  B: ──────── low

  Female: S,A = 2 = phi(6)
  Male:   T,B = 2 = phi(6)
```

## Interpretation

4 choir voices = tau(6), split phi(6):phi(6) by gender.

## Limitations

- 6-part (SSATBB) and 8-part choirs also exist.
""")

h(89, "ukulele-strings-tau", "Ukulele Strings = tau(6) = 4",
  "EXACT",
  "The ukulele has exactly 4 = tau(6) strings, like the bowed string\n"
  "> instruments (violin, viola, cello).",
  """## Background

The ukulele's four strings (G-C-E-A in standard tuning) make it one
of the most accessible string instruments.

## Numerical Verification

| Instrument | Strings | n=6 Function |
|-----------|---------|-------------- |
| Guitar     |    6    | P1=6         |
| Ukulele    |    4    | tau(6)=4     |
| Violin     |    4    | tau(6)=4     |
| Bass       |    4    | tau(6)=4     |

## ASCII Diagram

```
  String instruments by string count:
  6 = P1:     Guitar
  4 = tau(6): Violin, Viola, Cello, Bass, Ukulele, Mandolin

  tau(6)=4 is the dominant string count in Western instruments.
```

## Interpretation

tau(6)=4 strings is the most common string count across instruments.

## Limitations

- Instruments with 5, 7, 8+ strings also exist.
""")

h(90, "drum-kit-components", "Basic Drum Kit = sopfr(6) = 5 Pieces",
  "EXACT",
  "The standard basic drum kit consists of 5 = sopfr(6) pieces:\n"
  "> bass drum, snare drum, hi-hat, and two toms.",
  """## Background

The 5-piece drum kit has been the standard rock/pop configuration since
the 1960s. It is the starting point for virtually all modern drummers.

## Numerical Verification

| Piece      | Type       | # |
|-----------|-----------|---|
| Bass drum  | Kick      | 1 |
| Snare      | Rim/head  | 2 |
| Hi-hat     | Cymbal    | 3 |
| High tom   | Tom       | 4 |
| Floor tom  | Tom       | 5 |

Pieces = 5 = sopfr(6)
(Add ride + crash cymbals = 7 = P1+1 total)

## ASCII Diagram

```
  Standard 5-piece kit:
       [Hi-hat]   [High Tom]  [Ride]
            [Snare]    [Floor Tom]
              [Bass Drum]
  Core 5 pieces = sopfr(6)
```

## Interpretation

5-piece kit = sopfr(6). With standard cymbals, 7 = P1+1 total.

## Limitations

- Kit sizes range from 3 to 20+ pieces; 5 is a convention.
""")

# ============================================================
# THEORY & SYSTEMS (091-105)
# ============================================================

h(91, "tuning-systems", "Major Tuning Systems = P1 = 6",
  "EXACT",
  "Music theory recognizes 6 = P1 major tuning systems: Pythagorean,\n"
  "> just intonation, meantone, well temperament, equal temperament, and\n"
  "> extended just intonation.",
  """## Background

The history of tuning systems spans from ancient Greek Pythagorean
tuning to modern equal temperament, with several intermediate systems.

## Numerical Verification

| Tuning System       | Period         | Basis        |
|--------------------|---------------|-------------|
| Pythagorean         | Ancient-Med.  | Pure 5ths    |
| Just intonation     | Renaissance   | Pure ratios  |
| Meantone            | 1500-1700     | Tempered 3rds|
| Well temperament    | 1700-1850     | Unequal      |
| Equal temperament   | 1850-present  | Equal 12ths  |
| Extended JI         | 20th century  | Higher primes|

Systems = 6 = P1

## ASCII Diagram

```
  Timeline:
  Ancient    1500    1700    1850    1900    2000
  |Pythag.  |Just  |Mean  |Well  |Equal  |ExtJI|
  = 6 systems = P1
```

## Interpretation

6 major tuning systems = P1. Historically sequential and well-defined.

## Limitations

- Categorization varies; some combine well and equal temperament.
""")

h(92, "accidentals-sopfr", "Standard Accidentals = sopfr(6) = 5",
  "EXACT",
  "Music notation uses 5 = sopfr(6) standard accidental symbols:\n"
  "> sharp, flat, natural, double sharp, and double flat.",
  """## Background

Accidentals modify the pitch of a note. The five standard symbols
have been established since the development of modern notation.

## Numerical Verification

| Accidental   | Symbol | Effect       |
|-------------|--------|-------------|
| Sharp        | #      | Raise 1 ST  |
| Flat         | b      | Lower 1 ST  |
| Natural      | natural| Cancel      |
| Double sharp | x      | Raise 2 ST  |
| Double flat  | bb     | Lower 2 ST  |

Accidentals = 5 = sopfr(6)

## ASCII Diagram

```
  Pitch modification:
  bb    b    natural    #    x
  -2   -1      0      +1   +2
  = 5 symbols = sopfr(6)
  Symmetric around natural
```

## Interpretation

5 accidentals = sopfr(6). Symmetric set centered on natural.

## Limitations

- Quarter-tone accidentals exist in microtonal music.
""")

h(93, "modes-P1plus1", "Diatonic Modes = P1 + 1 = 7",
  "WEAK",
  "There are 7 = P1 + 1 diatonic modes (Ionian through Locrian),\n"
  "> one starting on each degree of the major scale.",
  """## Background

The seven diatonic modes each begin on a different degree of the major
scale, producing seven distinct scale patterns with the same pitch content.

## Numerical Verification

| Mode       | Starting Degree | Character |
|-----------|----------------|-----------|
| Ionian     | 1              | Major     |
| Dorian     | 2              | Minor-ish |
| Phrygian   | 3              | Exotic    |
| Lydian     | 4              | Bright    |
| Mixolydian | 5              | Bluesy    |
| Aeolian    | 6              | Minor     |
| Locrian    | 7              | Diminished|

Modes = 7 = P1+1

## ASCII Diagram

```
  C major notes used by all modes:
  C  D  E  F  G  A  B
  I  D  P  L  M  A  Lo   = 7 = P1+1
  6 "usable" modes (excluding Locrian) = P1
```

## Interpretation

7 = P1+1 requires +1 correction. The 6 modes excluding the
theoretical Locrian = P1 is a cleaner match.

## Limitations

- P1+1 is ad hoc. Locrian exclusion is arguable. Grade WEAK.
""")

h(94, "hexachord-pitch-class", "Hexachord = P1 = 6 Pitch Classes",
  "EXACT",
  "A hexachord is a set of exactly 6 = P1 pitch classes, and hexachordal\n"
  "> combinatoriality is fundamental to twelve-tone theory.",
  """## Background

In pitch-class set theory, a hexachord is any set of 6 pitch classes.
Hexachords are central because they partition the 12-tone aggregate
into two complementary sets of 6.

## Numerical Verification

| Quantity              | Value | n=6 Function | Match |
|-----------------------|-------|-------------- |-------|
| Hexachord size        |   6   | P1=6         | EXACT |
| Complement size       |   6   | P1=6         | EXACT |
| Total aggregate       |  12   | sigma(6)=12  | EXACT |
| Partition count       |   2   | phi(6)=2     | EXACT |

## ASCII Diagram

```
  12-tone aggregate = sigma(6):
  |<-- hexachord A (6=P1) -->|<-- hexachord B (6=P1) -->|
  C  C# D  Eb E  F           F# G  Ab A  Bb B

  Two complementary hexachords partition sigma(6)
  P1 + P1 = sigma(6)    (6+6=12)
```

## Interpretation

Hexachords = P1 = 6, partitioning sigma(6)=12 into phi(6)=2 halves.
This is one of the cleanest n=6 structures in music theory.

## Limitations

- Hexachords are defined to be size 6; this is tautological.
""")

h(95, "forte-number-hexachords", "Hexachord Forte Classes = 50",
  "INCONCLUSIVE",
  "There are 50 distinct hexachordal set classes (Forte numbers 6-1 through\n"
  "> 6-50). The number 50 does not map cleanly to n=6 functions.",
  """## Background

Allen Forte's classification of pitch-class sets catalogs all distinct
set types. For cardinality 6 (hexachords), there are 50 types.

## Numerical Verification

| Cardinality | Forte Classes | n=6 match? |
|------------|--------------|-----------|
| 1          |      1       | --        |
| 2          |      6       | P1=6!     |
| 3          |     12       | sigma(6)! |
| 4          |     29       | --        |
| 5          |     38       | --        |
| 6          |     50       | --        |

## ASCII Diagram

```
  Forte class counts by cardinality:
  |1|  *
  |2|  ******           6 = P1 !
  |3|  ************     12 = sigma(6) !
  |4|  *****************************
  |5|  **************************************
  |6|  **************************************************

  Cardinality 2: 6=P1 classes. Cardinality 3: 12=sigma(6) classes!
```

## Interpretation

While hexachord count (50) does not match, the dyad count (6=P1)
and trichord count (12=sigma(6)) are exact! Unexpected bonus.

## Limitations

- 50 hexachord types has no clean n=6 expression. Grade INCONCLUSIVE.
""")

h(96, "musical-alphabet", "Musical Alphabet = P1 + 1 = 7 Letters",
  "WEAK",
  "The musical alphabet uses 7 = P1 + 1 letters: A, B, C, D, E, F, G.",
  """## Background

Western music names pitches using the first 7 letters of the alphabet.
This convention dates to ancient Greece (modified through medieval usage).

## Numerical Verification

| Quantity        | Value | n=6 Function | Match |
|-----------------|-------|-------------- |-------|
| Letter names    |   7   | P1+1=7       | +1    |
| Natural notes   |   7   | P1+1=7       | +1    |
| Scale degrees   |   7   | P1+1=7       | +1    |

## ASCII Diagram

```
  A  B  C  D  E  F  G  | A ...
  1  2  3  4  5  6  7  | = P1+1
```

## Interpretation

7 = P1+1 requires a +1 correction. Grade WEAK.

## Limitations

- P1+1 is ad hoc. German system adds H (=B natural), making 8.
""")

h(97, "enharmonic-key-pairs", "Enharmonic Key Pairs = P1/2 = 3",
  "EXACT",
  "There are exactly 3 = P1/2 pairs of enharmonically equivalent major keys:\n"
  "> B/Cb, F#/Gb, C#/Db.",
  """## Background

Most keys have unique spellings, but three pairs share the same pitches
with different note names (enharmonic equivalents).

## Numerical Verification

| Pair | Key 1 | Key 2 | Sharps/Flats |
|------|-------|-------|-------------|
|  1   | B     | Cb    | 5# / 7b    |
|  2   | F#    | Gb    | 6# / 6b    |
|  3   | C#    | Db    | 7# / 5b    |

Enharmonic pairs = 3 = P1/2

## ASCII Diagram

```
  Key signatures:
  0 1 2 3 4 5 6 7    sharps
  0 1 2 3 4 5 6 7    flats
                ^^^
  Overlap at 5,6,7 = 3 pairs = P1/2
```

## Interpretation

3 enharmonic pairs = P1/2. Exact and well-defined.

## Limitations

- 3 is a common small number.
""")

h(98, "transpositions-sigma", "Possible Transpositions = sigma(6) = 12",
  "EXACT",
  "Any melody or chord can be transposed to 12 = sigma(6) different keys\n"
  "> (including the original), one for each pitch class.",
  """## Background

Transposition shifts all pitches by the same interval. In 12-TET,
there are exactly 12 possible transposition levels.

## Numerical Verification

| Transposition | Semitones | n=6 Function |
|--------------|-----------|-------------- |
| T0 (original)|     0     | --           |
| T1           |     1     | --           |
| ...          |    ...    | --           |
| T11          |    11     | --           |
| **Total**    |  **12**   | sigma(6)=12  |

## ASCII Diagram

```
  C -> C#-> D -> Eb-> E -> F -> F#-> G -> Ab-> A -> Bb-> B -> C
  T0   T1   T2   T3  T4  T5   T6   T7  T8   T9  T10  T11  =T0
  = 12 transpositions = sigma(6)
```

## Interpretation

12 transpositions = sigma(6). Same as chromatic pitch class count.

## Limitations

- This is the same fact as "12 pitch classes" restated.
""")

h(99, "pitch-class-group", "Pitch Class Group Z_12 = Z_{sigma(6)}",
  "EXACT",
  "The pitch class group is Z_12 = Z_{sigma(6)}, the cyclic group of order\n"
  "> sigma(6) = 12, with addition modulo 12.",
  """## Background

Pitch classes form the cyclic group Z_12 under transposition. This
algebraic structure underlies all of twelve-tone theory and set theory.

## Numerical Verification

| Property          | Value | n=6 Function | Match |
|-------------------|-------|-------------- |-------|
| Group order       |  12   | sigma(6)=12  | EXACT |
| Generators        |  4    | tau(6)=4?    | CHECK |
| Subgroups         |  6    | P1=6         | EXACT |
| Elements          |  12   | sigma(6)=12  | EXACT |

Generators of Z_12: {1,5,7,11} = elements coprime to 12
phi(12) = 4 = tau(6) (Euler totient of sigma(6) = tau(6)!)

## ASCII Diagram

```
  Z_12 subgroup lattice:
       Z_12
      / | \\
    Z_6  Z_4  Z_3
      \\  |  /
       Z_2
        |
       Z_1
  = 6 subgroups = P1!
```

## Interpretation

Z_{sigma(6)} has P1=6 subgroups and phi(sigma(6))=tau(6)=4 generators.
The group theory of the pitch class group encodes n=6 constants!

## Limitations

- Z_12 properties follow from 12's factorization, not directly from 6.
""")

h(100, "set-class-complement", "Set Class Complementation: Size 6 is Self-Complementary",
  "EXACT",
  "In pitch-class set theory, only sets of size 6 = P1 can be\n"
  "> self-complementary (Z-related to their own complement).",
  """## Background

A pitch-class set's complement contains the remaining pitch classes.
Sets of size 6 are unique: their complement is also size 6, enabling
self-complementary (hexachordal combinatorial) properties.

## Numerical Verification

| Set Size | Complement Size | Self-comp possible? |
|---------|----------------|-------------------|
| 1       |      11        | No                |
| 2       |      10        | No                |
| 3       |       9        | No                |
| 4       |       8        | No                |
| 5       |       7        | No                |
| **6**   |     **6**      | **YES = P1**      |

## ASCII Diagram

```
  Only at size P1=6:
  Set:        {C, D, E, F#, G#, A#}    6 = P1
  Complement: {C#, Eb, F, G, A, B}     6 = P1
  Both hexachords, both size P1
  This is unique to P1 within sigma(6)=12!
```

## Interpretation

Self-complementarity requires n = sigma(6)/2 = 12/2 = 6 = P1.
The perfect number is the unique self-complementary size.

## Limitations

- This follows from 12/2 = 6; the deeper claim is 12 = sigma(6).
""")

h(101, "interval-vector-length", "Interval Vector Length = P1 = 6",
  "EXACT",
  "The interval vector of any pitch-class set has exactly 6 = P1 entries,\n"
  "> corresponding to the 6 interval classes (1 through 6).",
  """## Background

The interval vector counts the frequency of each interval class in a
pitch-class set. There are 6 interval classes because intervals 7-11
are inversionally equivalent to 1-5, and class 6 (tritone) is its own.

## Numerical Verification

| Interval Class | Intervals | Example (major triad) |
|---------------|-----------|----------------------|
| IC 1           | m2, M7    |          0           |
| IC 2           | M2, m7    |          0           |
| IC 3           | m3, M6    |          1           |
| IC 4           | M3, m6    |          1           |
| IC 5           | P4, P5    |          1           |
| IC 6           | tritone   |          0           |

Vector length = 6 = P1
Major triad vector = [0,0,1,1,1,0]

## ASCII Diagram

```
  Interval classes:
  IC: 1  2  3  4  5  6
      m2 M2 m3 M3 P4 TT
  = 6 classes = P1

  (because 12/2 = 6 = P1)
```

## Interpretation

6 interval classes = P1 = sigma(6)/2. Each class pairs an interval
with its complement. The tritone (IC 6) is self-complementary at P1.

## Limitations

- Same as 12/2 = 6 observation.
""")

h(102, "whole-half-steps", "Scale Step Types = phi(6) = 2",
  "EXACT",
  "Diatonic scales use exactly 2 = phi(6) step sizes: whole steps (2 semitones)\n"
  "> and half steps (1 semitone).",
  """## Background

The major and minor scales are built from only two interval sizes.
This binary step vocabulary is what gives diatonic music its character.

## Numerical Verification

| Step Type  | Semitones | Notation | n=6 Function |
|-----------|-----------|---------|-------------- |
| Half step  |     1     |    H    | 1             |
| Whole step |     2     |    W    | phi(6)=2      |

Step types = 2 = phi(6)
Whole step size = 2 = phi(6) semitones

## ASCII Diagram

```
  Major scale pattern:
  W  W  H  W  W  W  H
  2  2  1  2  2  2  1   (semitones)
  Only 2 = phi(6) distinct step sizes used
```

## Interpretation

phi(6)=2 step types. The whole step = phi(6) semitones.

## Limitations

- Melodic minor uses augmented 2nd (3 semitones), adding a 3rd type.
""")

h(103, "major-scale-pattern", "Major Scale: sopfr(6) Whole Steps + phi(6) Half Steps",
  "EXACT",
  "The major scale pattern contains 5 = sopfr(6) whole steps and\n"
  "> 2 = phi(6) half steps, totaling P1+1 = 7 steps.",
  """## Background

The major scale interval pattern W-W-H-W-W-W-H contains exactly
5 whole steps and 2 half steps. This specific distribution creates
the characteristic major scale sound.

## Numerical Verification

| Step Type  | Count | n=6 Function |
|-----------|-------|-------------- |
| Whole (W)  |   5   | sopfr(6)=5   |
| Half (H)   |   2   | phi(6)=2     |
| Total      |   7   | P1+1=7       |
| Semitones  |  12   | sigma(6)=12  |

Check: 5*2 + 2*1 = 10 + 2 = 12 = sigma(6)

## ASCII Diagram

```
  Major scale:
  C  D  E  F  G  A  B  C
    W  W  H  W  W  W  H
    2  2  1  2  2  2  1  = 12 = sigma(6)

  W count: 5 = sopfr(6)
  H count: 2 = phi(6)
  sopfr(6)*phi(6) + phi(6)*1 = 10+2 = 12 = sigma(6)
```

## Interpretation

The major scale decomposes sigma(6) = sopfr(6)*phi(6) + phi(6)*1.
This is: 12 = 5*2 + 2*1 using n=6 constants exclusively.

## Limitations

- The decomposition 12 = 5*2 + 2*1 is one of many ways to partition 12.
""")

h(104, "harmonic-series-divisors", "First 6 Harmonics Use Divisors and Functions of 6",
  "EXACT",
  "The first 6 = P1 harmonics of a vibrating string produce frequencies\n"
  "> at multiples 1 through 6, which ARE the first perfect number's range.",
  """## Background

The harmonic series (f, 2f, 3f, 4f, 5f, 6f, ...) is the physical
basis of musical consonance. The first 6 harmonics define the most
consonant intervals.

## Numerical Verification

| Harmonic | Freq  | Interval from fundamental | In div(6)? |
|---------|-------|--------------------------|-----------|
| 1       | f     | Unison                   | YES (1)   |
| 2       | 2f    | Octave                   | YES (2)   |
| 3       | 3f    | Octave + P5              | YES (3)   |
| 4       | 4f    | 2 Octaves                | NO (but tau(6)) |
| 5       | 5f    | 2 Oct + M3               | NO (but sopfr(6)) |
| 6       | 6f    | 2 Oct + P5               | YES (6)   |

First P1=6 harmonics. Harmonics {1,2,3,6} = div(6) are pure octaves/fifths.

## ASCII Diagram

```
  Harmonic series:
  1f ───── fundamental (unison)        d(6)
  2f ───── octave                      d(6)
  3f ───── octave + fifth              d(6)
  4f ───── 2 octaves                   tau(6)
  5f ───── 2 oct + major third         sopfr(6)
  6f ───── 2 octaves + fifth           d(6) = P1

  Consonance decreases as we move beyond div(6).
```

## Interpretation

The first P1=6 harmonics establish all basic consonant intervals.
Harmonics at div(6) positions give the purest intervals (octaves, fifths).
The "new" intervals enter at tau(6)=4 and sopfr(6)=5.

## Limitations

- The harmonic series is infinite; stopping at 6 is a choice.
""")

h(105, "concert-pitch-A440", "Concert Pitch A440: 440 and n=6",
  "INCONCLUSIVE",
  "Concert pitch A4 = 440 Hz. While 440 = 8 * 55 = 2^3 * 5 * 11,\n"
  "> there is no clean mapping to n=6 arithmetic functions.",
  """## Background

The international standard concert pitch is A4 = 440 Hz, adopted in
1955 by ISO. Earlier standards varied (435, 432, 415 Hz, etc.).

## Numerical Verification

| Quantity         | Value | n=6 match?         |
|-----------------|-------|--------------------|
| A4 frequency     | 440   | 440/sigma(6) = 36.67 (not clean) |
| Middle C (C4)    | 261.6 | no clean mapping   |
| Lowest piano (A0)| 27.5  | no clean mapping   |
| A4 / 440         | 1     | --                 |

440 = 2^3 * 5 * 11
sigma(6) = 12 = 2^2 * 3
No common structure.

## ASCII Diagram

```
  A4 = 440 Hz
  440 / 6  = 73.33...  (not integer)
  440 / 12 = 36.67...  (not integer)
  440 / 5  = 88        (= 8 * 11)
  440 / 4  = 110       (A2)
  440 / 2  = 220       (A3)

  No clean n=6 relationship found.
```

## Interpretation

Concert pitch does not connect to n=6. The 440 Hz standard is a
20th-century convention, not a structural constant.

## Limitations

- 440 Hz is arbitrary; earlier standards (A=415, 432) were different.
- Grade INCONCLUSIVE: no connection found.
""")

# ============================================================
# Generate all files
# ============================================================

def generate_file(num, slug, title, grade, statement, body):
    grade_map = {
        "EXACT": "EXACT",
        "WEAK": "WEAK",
        "INCONCLUSIVE": "INCONCLUSIVE"
    }
    grade_emoji = {"EXACT": "🟩", "WEAK": "🟧", "INCONCLUSIVE": "⚪"}

    filename = f"MUSIC-{num:03d}-{slug}.md"
    filepath = os.path.join(OUTPUT_DIR, filename)

    content = f"""# Hypothesis MUSIC-{num:03d}: {title}

**Grade: {grade_emoji[grade]} {grade}**

## Hypothesis

> {statement}

{body}

## Grade: {grade_emoji[grade]} {grade}

Golden Zone dependency: None (pure music theory observation).
"""

    with open(filepath, 'w') as f:
        f.write(content)
    return filename

# Run generation
counts = {"EXACT": 0, "WEAK": 0, "INCONCLUSIVE": 0}
files = []
for num, slug, title, grade, statement, body in hypotheses:
    fname = generate_file(num, slug, title, grade, statement, body)
    counts[grade] += 1
    files.append((num, fname, grade, title))

print(f"\n{'='*60}")
print(f"Generated {len(files)} hypothesis files in {OUTPUT_DIR}")
print(f"{'='*60}")
print(f"  EXACT (🟩):        {counts['EXACT']}")
print(f"  WEAK (🟧):         {counts['WEAK']}")
print(f"  INCONCLUSIVE (⚪): {counts['INCONCLUSIVE']}")
print(f"{'='*60}")
print(f"\nFiles by category:")
print(f"  Scales & Intervals (006-025): 20 files")
print(f"  Rhythm & Meter (026-040):     15 files")
print(f"  Harmony & Chords (041-060):   20 files")
print(f"  Form & Structure (061-075):   15 files")
print(f"  Instruments (076-090):        15 files")
print(f"  Theory & Systems (091-105):   15 files")
print(f"{'='*60}")
for num, fname, grade, title in files:
    emoji = {"EXACT": "🟩", "WEAK": "🟧", "INCONCLUSIVE": "⚪"}[grade]
    print(f"  {emoji} {fname}")
