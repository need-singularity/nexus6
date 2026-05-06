# hexa-resolver subprocess env propagation — opt-in flag spec

- gap-id: `subprocess-resolver-env-propagation` (rank 2, gap catalog)
- date: 2026-05-06
- status: draft (pilot patch applied to Option B variant)
- target file: `~/.hx/bin/hexa` (Mac-side resolver shim, raw 44 docker hard-landing)
- ancillary: `scripts/bin/hexa_remote` (already exports HEXA_LOCAL=1 on remote; not modified)

## 1. problem

`nexus mk2 atlas` self-spawn dispatcher (`mk2_hexa/mk2/src/atlas/mod.hexa::_exec_module`) calls
`exec("hexa run <subcmd>.hexa ...")` from inside a hexa process. The child shell looks up
`hexa` on PATH → `~/.hx/bin/hexa` resolver shim. The child resolver re-runs the entire
routing decision (probe pool / docker daemon / cwd sync-root) on every dispatch.

When the parent was invoked with no env, two failure modes appear in production:

- (M1) parent picked route=docker; container exec passed `HEXA_RESOLVER_NO_REROUTE=1`;
  child mk2 atlas spawn inherits this — fine. But if `HEXA_RESOLVER_NO_REROUTE_STICKY`
  was not set, the resolver `unset`s the var on its own one-hop guard (line 122)
  before exec'ing REAL_HEXA. The grandchild via `exec("hexa run ...")` then
  re-enters resolver fresh → re-probes → hangs 30s+ on stale neg-cache or SSH timeout.
- (M2) parent invoked with `HEXA_RESOLVER_NO_REROUTE=1` alone (operator one-shot
  bypass for known-local script). Same one-hop unset trims the env before exec.
  Grandchild has no env, falls through to full routing, hits SSH probe, 30s hang.

The current operator workaround is to set BOTH `HEXA_LOCAL=1 HEXA_RESOLVER_NO_REROUTE=1`
on every call — the former is NOT unset by the resolver, so it survives across
exec depth. This is fragile (every caller must remember it) and contaminates
unrelated tools that read `HEXA_LOCAL` for their own routing decisions
(e.g., the `nexus` wrapper at `~/.hx/bin/nexus`).

## 2. options

| option | mechanism | scope | size | risk | recovery |
|---|---|---|---|---|---|
| A. whitelist env | new `HEXA_RESOLVER_INHERIT_ENV=HEXA_LOCAL,HEXA_RESOLVER_NO_REROUTE` parsed by resolver, vars are re-exported before each exec branch | opt-in per-caller | ~30 lines | low (only acts when caller sets the var) | unset the new var |
| B. unconditional propagate two vars | always re-export `HEXA_LOCAL` and `HEXA_RESOLVER_NO_REROUTE` if set, even on the docker-exec / hexa_remote / REAL_HEXA exec branches; also drop the one-hop `unset HEXA_RESOLVER_NO_REROUTE` for grandchild visibility under explicit caller request | always-on, opt-out via `HEXA_RESOLVER_STICKY_ENV=0` | ~12 lines | medium — the existing one-hop semantics were intentional (line 105-117 comment): a wrapper that sets `HEXA_RESOLVER_NO_REROUTE=1` then shells out to a hexa script SHOULD have the script's nested hexa calls re-enter the resolver. Flipping default would regress that contract. | opt-out var |
| C. sticky-decision | parent resolver writes its routing verdict (`local` / `docker` / `external`) into a per-pid file (or env) and child resolver reads it via `HIVE_PARENT_SID` linkage; child trusts the parent's decision and skips its own probe | always-on, autonomic | ~80 lines + new file format + GC | high — pid-file race conditions, GC of stale files, security boundary if pid is reused, file in /tmp may be tampered | disable with HEXA_RESOLVER_NO_STICKY_DECISION=1; pid-file gc cron |

### option B refinement (chosen for pilot)

Pilot adopts a **scoped variant** of B: instead of flipping the default, add an
opt-in `HEXA_RESOLVER_INHERIT_ENV=1` that:

1. preserves the line-122 one-hop unset (default behavior unchanged); BUT
2. when set, the resolver:
   - keeps `HEXA_RESOLVER_NO_REROUTE` set during exec REAL_HEXA (overrides line 122),
   - explicitly passes `HEXA_LOCAL` and `HEXA_RESOLVER_NO_REROUTE` via `-e` to the
     docker exec branch (currently only NO_REROUTE is set there as a hardcoded constant,
     and HEXA_LOCAL is not forwarded at all),
   - explicitly forwards both to hexa_remote child env.

This is essentially "option A with a single-flag activation" — caller flips one
switch and the resolver sticks both routing decisions across the entire exec tree.

## 3. pilot patch (applied)

Change to `~/.hx/bin/hexa`:

- Section 1 (line 119-125 NO_REROUTE one-hop guard): keep one-hop unset, but
  if `HEXA_RESOLVER_INHERIT_ENV=1` then skip the unset (= same as the existing
  `HEXA_RESOLVER_NO_REROUTE_STICKY=1` opt-out). This unifies the new flag with
  the legacy sticky var.
- Section 2 (line 491-502 docker hard-landing exec): when inherit flag set,
  add `-e HEXA_LOCAL` and `-e HEXA_RESOLVER_NO_REROUTE` to the env passthrough.
- Section 3 (line 619-628 docker cache-hit exec branch): same passthrough.
- Section 4 (lines 660-664 / hexa_remote external exec): hexa_remote already
  injects `HEXA_LOCAL=1` on the remote ssh command line, so this hop is OK
  for HEXA_LOCAL. For HEXA_RESOLVER_NO_REROUTE, hexa_remote does NOT
  forward it (and arguably should not — remote does not have a resolver
  shim normally). Out of scope for this pilot.

Effect: caller does `HEXA_RESOLVER_INHERIT_ENV=1 HEXA_RESOLVER_NO_REROUTE=1 hexa run main.hexa atlas lookup foo` once. Every grandchild `hexa run` re-enters
the resolver but sees `HEXA_RESOLVER_NO_REROUTE=1` in its env (never unset)
and short-circuits at line 119 to REAL_HEXA. No SSH probe. No 30s hang.

## 4. cost / effect / risk table

| dimension | option B-pilot |
|---|---|
| LOC delta | +6 lines, 0 deletions |
| caller change | 1 env var per dispatch tree root (instead of 2 per child) |
| backward compat | 100% — flag is opt-in; default behavior unchanged |
| failure mode | none new; if flag mis-set, behavior is "act as if NO_REROUTE/LOCAL is in env" which is exactly the desired effect |
| hexa-lang code change | none |
| hexa_remote change | none |

## 5. verification plan

```sh
# baseline (expected: 30s+ hang or 76 hard-fail before fix)
unset HEXA_LOCAL HEXA_RESOLVER_NO_REROUTE HEXA_RESOLVER_INHERIT_ENV
time hexa run mk2_hexa/mk2/src/main.hexa atlas lookup alpha_inv

# new opt-in (expected: <2s, child resolver short-circuits)
HEXA_RESOLVER_INHERIT_ENV=1 HEXA_RESOLVER_NO_REROUTE=1 \
  time hexa run mk2_hexa/mk2/src/main.hexa atlas lookup alpha_inv
```

## 6. follow-ups

- (FU-1) hexa_remote forwarding of `HEXA_RESOLVER_NO_REROUTE` to remote when the
  remote host has its own resolver shim (some hive-pool hosts do).
- (FU-2) consider promoting Option C (sticky-decision via pid file) once the
  data shows opt-in B-pilot is widely adopted but still leaks under unusual
  spawn patterns (popen + setsid + nohup chains).
- (FU-3) drift lint: emit warning when a hexa-lang `exec("hexa run ...")`
  call is detected in a file lacking `@resolver-pure` / `@resolver-bypass` —
  encourage callers to set `HEXA_RESOLVER_INHERIT_ENV=1` themselves at the
  outermost shell wrapping the dispatcher.

## 7. Rollout (Track 2 — applied 2026-05-06)

Track 1 의 후속 권장 사항 — **dispatcher 가 자체적으로 sticky env 부착**
— 을 `mk2_hexa/mk2/src/atlas/mod.hexa::_exec_module` 에 적용했다.

### 7.1 변경 라인 (mod.hexa)

`_exec_module` 함수 (라인 102 부근) 가 빌드하던 shell command 의 prefix 에
세 env 를 부착:

```hexa
cmd.push("HEXA_LOCAL=${HEXA_LOCAL:-1} ")
cmd.push("HEXA_RESOLVER_NO_REROUTE=${HEXA_RESOLVER_NO_REROUTE:-1} ")
cmd.push("HEXA_RESOLVER_INHERIT_ENV=${HEXA_RESOLVER_INHERIT_ENV:-1} ")
cmd.push("hexa run ")
// ... (이하 기존 동일)
```

`exec()` 라인 끝에 `// @allow-bare-exec @resolver-bypass(reason="…")` 부착 —
FU-3 lint 가 도입될 때 이 marker 가 dispatcher 의 명시적 자가-bypass 선언
역할을 한다. 추가 LOC: +3 cmd.push lines + 어노테이션 확장 + 헤더 docstring
~14 줄 (총 +17 lines, 0 deletion).

### 7.2 `${VAR:-1}` 패턴 선택 근거

호출자가 명시적으로 `HEXA_LOCAL=0` (또는 `HEXA_RESOLVER_NO_REROUTE=0` /
`HEXA_RESOLVER_INHERIT_ENV=0`) 으로 끄려 하면 그 값을 우선. 기본은 1 (sticky).
회귀 0 — caller 가 모두 미설정인 경우, parent 가 이미 라우팅을 끝낸 상태이므로
child 가 동일 결정을 재사용하는 것이 의미상 안전. caller 가 `HEXA_LOCAL=0` 을
명시하는 시나리오는 "강제 docker" 운영 모드 (CI matrix 등) 한정이며 그 의도가
명확히 보존된다.

### 7.3 검증 (2026-05-06)

| 시나리오 | duration | rc | output | 비고 |
|---|---|---|---|---|
| env 없이 `lookup alpha_inv` (이전 baseline) | 2.218s | 0 | 정상 | Track 1 가 이미 적용된 상태 |
| env 없이 `lookup alpha_inv` (Track 2 후) | 2.057s | 0 | 정상 (동일) | 회귀 0, parent route=docker 그대로 |
| env 모두 set (`HEXA_LOCAL=1 …=1`) — `lookup` | 2.791s | 0 | 정상 | 회귀 0 |
| 6/6 smoke (env set, lookup/recall/dist/hypo/--help/none) | 1.03–2.79s | all 0/2 | 모두 정상 | 출력 라인 형식 100% 보존 (`name:`, `value:`, `total:`, `usage:`, NDJSON meta 등) |

duration 동일 — Track 1 만으로 이미 child resolver 가 short-circuit 되고
있었으므로, Track 2 의 진정한 가치는 **호출자 fingerprint 0** (env 인자
명시 없이도 sticky) + **dispatcher 자가-선언** (resolver-bypass marker
가 spec 의 의도를 인-소스로 표현). 30s+ hang 시나리오는 Track 1 기준
사라진 상태이며, Track 2 는 그 보장의 *전파* 를 자동화한다.

### 7.4 후속 권장 (FU-4)

다른 self-spawn dispatcher (`mk2_hexa/mk2/src/main.hexa::_exec_module`,
`scripts/atlas_sync_remote.hexa`, `n6/atlas_query.hexa` 등) 도 동일 sticky
prefix 패턴 적용. main.hexa 는 본 패치와 직접 동형 (3-line cmd.push prefix
+ marker 확장) 으로 ~5 분 작업. 단, 본 트랙은 atlas dispatch tree 만 범위로
제한 (다른 영역 충돌 회피).
