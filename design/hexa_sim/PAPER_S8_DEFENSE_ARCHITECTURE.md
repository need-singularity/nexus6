---
section: §8
title: "Defense system architecture"
parent: "n=6 as foundational invariant: a multi-domain falsifier-grounded framework"
target_words: 600-700
status: draft v1
generated: 2026-04-26
---

# §8 Defense system architecture

## 8.1 Threat model

The framework's evidentiary value is contingent on registry integrity:
a single silent mutation to `falsifiers.jsonl`, to a bridge `.hexa`,
or to an atlas shard would invalidate every claim that cites it. We
enumerate four adversaries of escalating capability: (i) the
*single-actor mistake* (typos, copy-paste errors, regex bugs);
(ii) the *external attacker with write access* assuming git-remote
compromise but no signing key; (iii) the *compromised CI pipeline*
mutating artefacts after review; (iv) the *insider with intentional
drift* holding full repository write access and capable of coordinated
mutation across registry, baseline, and ledger.

## 8.2 Five-layer defense overview

The chain composes five complementary layers indexed R1--R5
(SECURITY\_AUDIT.md §2). **R1 byte-level**: every falsifier carries a
16-hex prefix `cmd_sha256` and every bridge has an entry in
`state/bridge_sha256.tsv` (per-file SHA256), giving cryptographic
byte-level integrity at template and implementation granularity.
**R2 anti-spoof regex lint** rejects literal-only commands such as
`echo TOKEN` whose sentinel emission is decoupled from the claim.
**R3-lite `--strict` baseline** computes a whole-registry SHA256
(`state/falsifier_registry.sha256`) and emits an advisory drift warning
under `tool/falsifier_quick.sh --strict`. **R4 forensic ledger**
appends every rotation as a JSONL record, gitignored and local-only,
guaranteeing post-hoc traceability without polluting history.
**R5 hash-chained ledger + SSH signature** binds each ledger entry to
its predecessor by SHA256 prev\_hash and pins each baseline to a key
rather than to a self-referential digest.

## 8.3 The 9-cell defense matrix

R5 was generalised from the falsifier registry to the bridge and atlas
domains over three Ω-cycles (`2026-04-26_R5_detached_signature`,
`...R5_bridge_chain_extension`, `...atlas_R5_tracking`). The result is
a 3 (R5 sub-layer) $\times$ 3 (domain) coverage grid:

```
                       | Falsifier | Bridge | Atlas |
R1 file SHA            |   LIVE    |  LIVE  |  LIVE |
R5 chain ledger        |   LIVE    |  LIVE  |  LIVE |
R5 SSH PREVENTIVE      |   LIVE    |  LIVE  |  LIVE |
```

Every cell is operational: cumulative chain entries stand at 0
falsifier (the registry is signed in lieu of rotation) + 2 bridge + 3
atlas = 5, with corresponding signature artefacts
`design/hexa_sim/falsifiers.jsonl.sig`, `state/bridge_sha256.tsv.sig`,
and `state/atlas_sha256.tsv.sig`.

## 8.4 R3-full intentional retirement

R3-full was initially shipped as a `.githooks/pre-commit` hook
performing baseline auto-rotation on staged registry changes (commit
`1836dd20`). The user retired it across `e3137be2` (hook removal +
`core.hooksPath` unset), `fa1de8e2` (OS-level `chflags uchg`), and
`582f791e` (AI-native deny-rule codification). The rationale is a
deliberate trade: commit-time hook friction was disproportionate once
R4 forensic coverage and R5 SSH preventive coverage were both
operational. Rotation is therefore manual via `tool/registry_sign.sh`,
`tool/bridge_sha256_rotate.sh`, and `tool/atlas_sha256_rotate.sh`,
invokable interactively or by cron.

## 8.5 R5 hash-chained ledger (OPT-D)

Each ledger line records
`{"ts","old_sha","new_sha","trigger","prev_hash"}` with
`prev_hash = SHA256(prev_line)`, or the literal `"genesis"` for chain
roots. Forward propagation is the security property: rewriting any
mid-chain entry forces re-hashing every subsequent entry, so
single-line forgery is detectable in O(N) by `tool/ledger_verify.sh`,
which walks the chain and emits
`__LEDGER_VERIFY__ <PASS|FAIL|EMPTY|PRE_R5> entries=N broken_at=<line|none>`.
Four verification tests passed: empty baseline, two-rotation chain
integrity, mid-injection forgery (`broken_at=2`), and SSH stub.

## 8.6 R5 SSH signature (OPT-B): STUB to PREVENTIVE

`registry_sign.sh` originally skipped with rc=0 until `SIGNING_KEY`
was configured. On 2026-04-26 the user authorised activation under
*Path A* (reuse of `~/.ssh/id_ed25519`) via
`git config user.signingkey + gpg.format=ssh` and `ssh-keygen -Y
sign|verify` against `~/.ssh/allowed_signers`. Three detached
signatures were minted, one per domain (§8.3). The layer status
transitioned from STUB to PREVENTIVE, elevating overall confidence
from *high multi-vector forensic* to *high multi-vector preventive*.
The remaining attack surface is compromise of the signing key itself
(`~/.ssh/id_ed25519`, mode 0600 under macOS Keychain encryption).

## 8.7 End-to-end audit and residual gap

The chain was validated end-to-end in commit `b99adc95`: seven stages
covering baseline capture, R1 silent corruption, R2 anti-spoof
reachability, R1 bridge mutation, R3-full pre-commit auto-rotation,
R3-lite advisory warning, and R4 ledger persistence all PASSed. The
audit surfaced a layer-order finding of independent interest:
**R1 fires before R2** because cmd-hash mismatch precedes pattern
inspection, so R2 is reachable only against an adversary who preserves
the cmd hash exactly while injecting a spoof pattern. Pre-activation
the most concerning gap was *coordinated registry + baseline mutation*;
post R5 SSH activation that gap is closed and only signing-key
compromise remains.

## 8.8 Performance

Health checks were parallelised over `ProcessPoolExecutor` with
per-domain Amdahl floors honoured. `falsifier_health.sh` improved
from 16.94 s sequential to 4.71 s parallel (3.6$\times$);
`bridge_health.sh` from 36 s to 15.6 s (2.43$\times$, bounded by a
12 s `uniprot` probe); the aggregate `health_check_all.sh` from 93 s
to 30 s (3$\times$). The system therefore sustains
sub-minute full-defense verification, suitable for cron
or pre-push contexts.
