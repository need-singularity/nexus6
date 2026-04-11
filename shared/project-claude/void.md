# void — hexa-only AI-native 터미널

> SSoT: `state.json`. 참조 기준: **macOS Terminal.app**. iTerm2/kitty/Warp/Ghostty/Alacritty 참조 제외 (VD1).

## state (모든 진행/결정은 JSON/JSONL에만)

| 파일 | 역할 |
|------|------|
| `state.json`         | 레이어·바이너리·블로커·next steps SSoT |
| `breakthroughs.jsonl` | 증명된 능력 append-only (현재 10건) |
| `pitfalls.jsonl`     | 발견된 함정 append-only |
| `convergence.json`   | 골화 (ossified) 결정 |
| `rules.json`         | VD1~VD5 프로젝트 규칙 |
| `hooks.json`         | hook DSL — smoke-pass/fail/codegen-slow/iterm2-ref/discovery-emit |
| `manifest.json`      | 소스 파일 ↔ 레이어 ↔ 의존 |
| `hexa.toml`          | 패키지 매니페스트 (hexa-lang 기준) |

## layers

| L | 역할 | 소스 접두 |
|---|------|-----------|
| L1_sys  | OS 브릿지 (PTY/termios/poll/Cocoa) | `src/sys_*.c,.m` |
| L2_term | VT 파서/스크린 버퍼/UTF-8 (순수 hexa) | `src/smoke_*.hexa` (모듈 임포트 미구현으로 임베딩) |
| L3_app  | 엔트리 + 이벤트 루프 + 렌더 | 미착수 |

## build / run

| 방법 | 명령 |
|------|------|
| 설치 | `hx install void` (hexa-lang pkg 레지스트리 경유) |
| 실행 | `./void` (현재 MVP: AppKit smoke — 800x600 NSWindow) |
| 통합 | `./void --term-v1` (PTY → VT → 80x24 grid 증명) |
| 전체 빌드 | `./void --build` (9 smoke 병렬 빌드) |
| 상태 | `./void --status` (state.json 요약) |
| 단건 | `scripts/build.sh src/smoke_<name>.hexa src/sys_<dep>.{c,m}` |

## 현재 블로커

```
VB1 native build_c        high    interpreted ./hexa 7.7KB→170s
VB2 hexa 모듈 임포트 부재    medium  VT parser/screen 공통화 불가
VB3 extern param 추론 한계  low    s.chars() 우회
```

## 아카이브

이전 Metal/Vulkan 6-layer (core/ui/plugin/ai/platform) 설계 65 commits:
`~/archive/void_20260411_pre_terminalapp/`

## ref

```
rules        shared/rules/common.json       R0~R27
project      rules.json                     VD1~VD5
lockdown     shared/rules/lockdown.json     L0/L1/L2
design       docs/design.md
manifest     manifest.json
package      hexa.toml
compiler     ~/Dev/hexa-lang/hexa
build_c      ~/Dev/hexa-lang/self/build_c.hexa
registry     ~/Dev/hexa-lang/pkg/registry.tsv
archived     ~/archive/void_20260411_pre_terminalapp/
discovery    shared/discovery/growth_bus.jsonl
```
