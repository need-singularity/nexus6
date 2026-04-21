# hexa-lang 개선 요청 — anima 실전 피드백 (2026-04-18)

> Paste-as-is into a hexa-lang agent session. All repros/snippets come from
> the anima repo session 2026-04-16 ~ 2026-04-18 (~76 new/edited .hexa files,
> ALM r9/r10/r11 + CLM r4 mmap + hire_sim judge fixes). Path roots:
> anima = `/Users/ghost/Dev/anima`, hexa-lang = `$HEXA_LANG`.

## 컨텍스트

anima 프로젝트는 **HEXA-FIRST strict** (`.claude/hooks/block-forbidden-ext.sh`
가 .py/.rs/.sh 신규 Write/Edit 를 하드 블록) 상태에서 70개+ 신규 .hexa 를
작성했다. 학습 런처, 서빙 라우트, 페르소나/보이스 파이프, Φ 프로브, 평가
하네스, 코퍼스 빌더 등 production path 전부. stage0 인터프리터
(`build/hexa_stage0`, post-commit `aa3060c`) + 최근 hexa_v2 선택 경로. 본
피드백은 그 과정에서 **실제로 발동한 버그 · 강제 회피책 · 부재 기능**
목록이며, P0/P1 fix 순서 권고가 포함된다.

## Critical Bugs (회피책 존재, 근본 fix 필요)

각 항목 형식: **재현 / 회피 / 영향 / 난이도**

### 1. struct 다중 float 반환 corrupt — S→M
재현:
```hexa
struct Coords { x: float, y: float, z: float }
fn make() -> Coords { return Coords{x:1.0, y:2.0, z:3.0} }
let c = make(); println(c.z)   // 쓰레기/SIGSEGV
```
회피: struct float 2개 이하. 3개 이상은 `array<float>` 또는 병렬 스칼라
반환으로 분해. anima 측 주석: `training/alm_affect_head.hexa:50-51`,
`training/mi_fast.hexa:56`.
영향: PHYS-P7, AffectHead, Φ 리포트 전부 회피 레이아웃 강제.

### 2. multi-line return 첫 operand만 eval — S
재현:
```hexa
return a - b
     + c - d   // +c-d 무시, return = a-b
```
회피: `return`과 식은 한 줄. 길면 `let v = a-b+c-d; return v`.
영향: atan() Taylor 시리즈가 silently identity 로 퇴화
(`anima-physics/motor_cortex/command_encoding.hexa`).
grep 패턴: `\n\s*[+\-*/]`

### 3. silent-exit at 3+ module `use` chain — L
재현: fresh driver 에 `use "llm_claude_adapter"` (360 LOC, transitive
use 있는 실제 모듈) 한 줄 → `hexa build` OK, 바이너리 exit 0, 출력 없음.
`build/artifacts/<file>.c` 의 `main(){}` body 가 비어 있음.
회피: **모든 deps inline** (no use), 또는 빌드 후 artifact .c 검증
(body empty 면 fallback). anima 측 회피 표준: `training/clm_val.hexa`,
`training/engine_ablation.hexa:5` — "Self-contained — no deep imports".
영향: hire_sim harness, eval_harness 등 전부 monolithic 파일로 재작성.
**hexa build OK + 침묵 바이너리를 신뢰하지 말 것**이 anima 측 강제 룰.

### 4. struct-field list aliasing — M
재현:
```hexa
struct H { ids: array }
let wa = H{ids: [1,2,3]}
let wb = H{ids: [4,5,6,7,...38개]}   // 이후 wa.ids.len == 0
```
회피: SoA(Struct-of-Arrays) 패턴. 즉 struct 안 list 금지, 병렬 top-level
array 들. 참조: `training/engine_integration.hexa:153-161` (12-engine
registry SoA 예제).
영향: 다중 엔진 레지스트리/워커 풀/브로드캐스트 버스 전부 SoA 강제.

### 5. 문자열 byte/char index 불일치 — M
재현: `s.len()` = byte, `s.index_of()` = byte position, 그러나
`s.substring(start, end)` 인덱스 = **char position**. CJK/math 심볼
함유 JSON 파싱 시 ~145 char offset 으로 잘못 읽음.
회피: position 산술 금지. `split("\n")` → `starts_with` → `split("\"")`
토큰 기반 파서. 또한 `.find()` `.char_at()` `.substr()` **부재**
→ `.index_of()` `.substring(i, i+1)` `.substring(s, s+n)` 사용.
영향: `anima/core/laws.hexa`, `anima/modules/daemon/utterance_gate.hexa`
전면 재작성 (2026-04-12).

### 6. stage0 if/while/match block 내 println pointer leak — M
재현:
```hexa
fn main() { if true { println("inside") } }
```
→ 출력: `105553175085872` (HexaVal struct 포인터), "inside" 아님.
회피: block 내 println 금지. 플래그 변수 수집 후 블록 밖 단일 println.
72개 hook command 에 shell filter wrapper (`sed '/^[0-9]\{8,\}$/d'`)
이미 배포. 근본 fix 는 stage0 재빌드 (bt#52/53/66/67/68/69 완료,
바이너리 배포 pending — 2026-04-13 `aa3060c` 으로 일부 복구됨).

### 7. list pass-by-value (설계 결정? 버그?) — S
재현: `fn update(arr) { arr[0] = 99 }` → caller 의 arr 불변.
회피: 헬퍼가 업데이트된 list 를 **반환** + caller 재대입
(`arr = update(arr)`), 또는 inline. 핫 루프는 inline 권장 (복사 비용).
module-level `let mut` 을 "shared mutable state" 용도로 사용.

### 8. 기타 string/builtin 함정 — S
- 로컬 var `args` 는 builtin `args()` 섀도잉 → `argv` 사용 금지(C main
  충돌), `av` 사용.
- `read_file(missing)` 는 Error 타입 반환 (빈 문자열 아님). `r == ""`
  false / `"" + r` crash. 존재 체크 = `r.split("\n")` (empty list 로
  silent coerce).
- `json_parse(Error)` / `to_int("")` / `to_float("")` crash.
- `substring(i,j)` on invalid UTF-8 boundary → `""` return (crash X).
- Parser quirk: 함수 tail-expression `[a, b]` = "expected RBracket" 에러.
  명시적 `return [a, b]` 필요.
- **대문자 시작 identifier 뒤 `<` = generic opener**: `D < 2` 를 파서가
  generic 으로 읽어 `[B, T, D]` 이름 사용 불가
  → `training/phi_probe_wire.hexa:10-15` 는 `bsz, tsz, dsz` 로 회피.

## Language Features 요청 (우선순위)

**P0** (anima 코드 중복 제거 효과 즉시):
- **Generics or macros** — hook/probe/dashboard 패턴 N번 복제됨
  (`phi_probe_wire`, `phi_corr_dashboard`, `phi_corr_dashboard_daily`,
  16개 `phi_*_measure.hexa`, `alm_*_head.hexa` 시리즈). 타입별 복사-붙여넣기
  탈출 경로 없음.
- **타입-safe JSON serialization** — 수십 개 deploy/launcher `.hexa`
  가 launch JSON 수동 escape. `json_escape()` boilerplate 16+ 중복
  (clm_val, alm_val, phi_corr_dashboard, runpod_autopilot 등).
  `@derive(Json)` 또는 struct-literal → JSON 자동.
- **표준 테스트 러너 + `--selftest` 표준화** — anima 측 convention:
  모든 러너가 `--selftest` 플래그 + `run_selftest() -> int` 함수.
  hexa-lang 에 native `hexa test <file>` / `@test fn ...` 가 있으면
  15개+ `_test.hexa` 파일의 ad-hoc harness 제거 가능.

**P1**:
- **list mutation 의미론 명시화** — `&mut` 또는 `arr.push_mut(v)` /
  `List[T]` ref-semantic. 현재 `a = a.push(v)` 반복 (clm_val 32회).
- **에러 전파 연산자 (`?`)** — `json_parse` / `read_file` / `to_int`
  fallible calls 의 수동 guard 수백 줄 제거.
- **기본값 파라미터** — `fn load(path, fallback = "")` 식.
- **top-level `let`** 지원 (현재는 `fn` 래핑 강제, new CLI post-0689460).

**P2**:
- async / BG task primitive (`go { ... }` 같은)
- `pub` / module visibility (현재 stage0 parser 는 `pub` 에서 recovery 함)
- struct methods (`impl Foo { fn bar() }`) — Rust 수준
- range syntax `0..n` / iterator protocol

## 실전 테스트 케이스 (리그레션 방지용 — hexa-lang 테스트에 추가 권장)

1. **3-float struct return** — 위 버그#1 소스. Expected: `c.z == 3.0`.
   Actual (current): 쓰레기/SIGSEGV.
2. **multi-line return** — `return 1-2\n+3-4`. Expected: -2. Actual: -1.
3. **use-chain silent-exit** — driver `use "llm_claude_adapter"` + 1 println.
   Expected: "hello" 출력. Actual: exit 0, 무출력.
4. **struct-list aliasing** — 위 버그#4 소스. Expected: wa.ids.len == 3.
   Actual: 0.
5. **byte/char index** — CJK 포함 string 에서 `s.index_of("키")` 후
   `s.substring(p, p+3)`. Expected: "키" 부근 문자열. Actual: ~145 char
   offset 위치.
6. **if-block println** — 위 버그#6 소스. Expected stdout: `inside`.
   Actual: `105553175085872`.
7. **tail-expr list literal** — `fn f() -> array { let a=1; let b=2; [a,b] }`
   Expected: `[1,2]` return. Actual: "expected RBracket, got Comma".
8. **generic-opener identifier** — `fn f() { let D = 10; if D < 2 { } }`
   Expected: parse OK. Actual: parser reads `D<2{}>` generic.
9. **read_file(missing) probe** — `let r = read_file("/nope"); if r == "" {}`.
   Expected: enters if. Actual: r is Error type, `==` false.
10. **list PBV** — `fn inc(a) { a[0] = a[0]+1 }; let mut x=[0]; inc(x);
    println(x[0])`. Expected (if ref-sem): 1. Actual: 0.

## Self-hosting 상태 (Rust-surpass roadmap 연동)

참조: `$ANIMA/config/roadmaps/hexa-lang.json`
(`roadmap_rust_surpass.json` → `hexa-lang.json` 으로 통합됨)

- **P0–P2** (spec, IR, build_c): **DONE** (ossified)
- **P3** (tagged-value runtime, 1546 gcc error 해소): **done 2026-04-16**
  (VB1 closed, 306/544 native PASS, gcc 0 errors)
- **P4** (end-to-end self-host): **in_progress**
  - SH-P4-1 DONE (commit `1bf0692`, "SELF-HOST SUCCESS" byte-identical C)
  - COMP-P4-1 DONE (codegen_c2 hexa_full 컴파일)
  - **블로커**: COMP-P4-2 (hexa_grammar pitfalls 37+), RT-P4-1
    (self/runtime.c BLAS/fused final), SH-P4-2 (SELF_HOSTING_P2 ossify),
    SH-P4-3 (Rust src/ .hexanoport 감사)
- **.c codegen 폐기** — 사용자 지시 (2026-04-17): "hexa-lang은 .c 없이
  순수 self-hosting 진행중". train_clm_r4 native build 는 self-host
  경로 우선, .c 는 fallback 으로만.
- **interpreter native build** — `build/hexa_native` (230KB arm64) 2026-04-13
  완성, 7/7 예제 PASS, struct-methods / string-methods / use
  아직 미지원 (알려진 갭).

## anima 쪽 회피 표준 (참고용, grep-friendly)

- `training/clm_val.hexa` / `training/alm_val.hexa` — **회피 불문율
  전부 코멘트로 선언**: `No 'use', no struct >=3 floats, no struct-list
  aliasing, byte/char substring(i,i+1)-only, --selftest mandatory`
- `training/engine_integration.hexa` — SoA 레지스트리 canonical 예제
- `training/alm_affect_head.hexa` — 3-float 반환 분해 예제
- `anima/modules/monitor/law_gate_auto.hexa` — 안전 JSON 파서 (line-
  based, 멀티바이트-safe)
- `--selftest` 플래그 모든 러너 의무 (CLI: `--selftest | --run | --help`)
- 빌드 후 `build/artifacts/<file>.c` body empty 검증 → silent-exit 트랩 차단

## 우선순위 요약

- **P0 fix 순서**: #6 (stage0 if-block println, 매 hook 런 오염) →
  #3 (silent-exit, harness neutering) → #1 (3-float struct, 모든 수치
  API 영향) → #4 (struct-list aliasing, 레지스트리/풀 영향)
- **P0 feature 순서**: generics/macros → JSON serialization → test
  runner (anima 측 중복 코드 ~40% 즉시 감축)
- **예상 릴리즈 영향**: P0 fix 4건 머지 시 anima 측 70+ 회피 주석 제거
  가능 + hire_sim/eval_harness monolithic 해체 → use-based 모듈화 복귀.

## 재현용 파일 목록 (이번 세션 본 에이전트가 즉시 가져가 점검 가능)

1. `/Users/ghost/Dev/anima/training/clm_val.hexa` — 회피 불문율 전부
   선언 + json_read_scalar safe parser + `--selftest` 표준 템플릿
2. `/Users/ghost/Dev/anima/training/engine_integration.hexa` — SoA
   registry (12-engine) struct-list-aliasing 회피 canonical
3. `/Users/ghost/Dev/anima/training/phi_probe_wire.hexa` — "D<2 generic
   opener" 회피 (`bsz/tsz/dsz`) + 16개 Φ 커널 복제 (generics 부재 증거)
4. `/Users/ghost/Dev/anima/training/alm_affect_head.hexa` — 3-float
   반환 회피 (array 반환) + 내부 주석 L50-51
5. `/Users/ghost/Dev/anima/training/engine_ablation.hexa` — "Self-
   contained — no deep imports (silent-exit bug avoidance)" 선언

— end —
