# atlas_phase6_crossscale

Agent 25 (2026-04-11) Phase 6 cross-scale `@X` proposal emitter. Reads
`shared/n6/atlas.n6` read-only and writes proposed bridge edges between
intermediate-scale domains (material/music/particle/atom/molecule/bio/genetic)
and large-scale domains (bt/celestial/galactic/cosmological) where the two
nodes share an n6 algebraic source token (phi/tau/n/sigma/sopfr/mu/J2/M3)
or an identical literal RHS expression. Output is top-200 by score
(grade_a_exact + grade_b_exact + same_src_label + diversity + 0.5 base) as
JSONL to `shared/n6/atlas_phase6_crossscale.jsonl`. Does not modify atlas.n6
or any blowup engine. Regenerable via
`/usr/bin/python3 shared/n6/scripts/atlas_phase6_crossscale.py > shared/n6/atlas_phase6_crossscale.jsonl`.
A hexa port (`atlas_phase6_crossscale.hexa`) exists but times out on 44k-line
atlas; python is the active implementation. All 200 emitted edges tie at
max score 4.0, so sort breaks ties by `(from, to)` alphabetically — this
means some equally-scored Agent 25 picks (e.g. `MUS-octave-ratio` ↔
`L7-kepler-3rd-exponent`) sit just below the cut but remain in the raw
2480-edge pool inside the script.
