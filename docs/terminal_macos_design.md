# macOS Terminal.app 설계 — 왜 iTerm2보다 가벼워 보이는가

> 2026-04-11 작성. 요점: Terminal.app은 부하가 "없는" 게 아니라 **부하 낼 기능이 없다**.

## 한 줄 요약

**단일 프로세스 + AppKit 네이티브 렌더링** — 이게 전부다.

## Terminal.app vs iTerm2 구조 비교

| 영역 | Terminal.app | iTerm2 |
|------|--------------|--------|
| 렌더러 | `NSTextView` + Core Text (CPU, CoreAnimation이 합성) | 자체 Metal GPU 파이프라인 (셰이더/폰트 아틀라스/프레임타이머) |
| 프로세스 모델 | 한 프로세스에 모든 탭/윈도우 (`NSWindowController`) | 윈도우별 Python API 서버 + MainProfileChange 브로드캐스트 |
| 스크롤백 | `NSAttributedString` 기반 단순 버퍼 | 자체 LineBuffer + 검색 인덱스 + mark/annotation 메타 |
| 파서 | 내부 TermKit (Apple private) — xterm-256color, VT100 핵심만 | 완전 재작성 파서 + truecolor/SGR 확장/Sixel-like/tmux integration |
| 확장 | AppleScript only | Python API, shell integration (OSC 1337), trigger 정규식 엔진 |
| 설정 | 프로파일 ~30개 필드 | ~500+ 필드, 프로파일 상속, dynamic profiles |

## 왜 Terminal.app이 가벼워 보이는가

1. **렌더 경로가 "공짜"**
   Core Text는 이미 시스템이 로드해 놓은 거라서 별도 GPU 자원 점유가 안 잡힌다. iTerm2는 Metal 디바이스를 따로 잡고 60Hz로 프레임을 밀어낸다 (유휴에도 갱신 존재).

2. **기능 자체가 적음**
   split, hotkey window, broadcast input, instant replay, tmux control mode, password manager, AI, minimap… 이 전부 없다. 코드 경로가 없으니 CPU가 돌 일도 없다.

3. **shell integration 없음**
   iTerm2는 OSC 133/1337 시퀀스를 모든 프롬프트마다 파싱해서 command boundary/exit status/cwd를 추적. 출력량 많을수록 누적 비용.

4. **Scrollback 처리 단순**
   `NSAttributedString` run-based라 메모리는 좀 더 먹지만 검색/mark가 없어서 append 비용만 발생. iTerm2는 검색 인덱스 + highlight rebalancing.

5. **단일 파서 경로**
   VT100/xterm-256color 딱 그만큼만. 24bit truecolor는 Monterey 이후 제한적 지원. Sixel/Kitty graphics/hyperlink(OSC 8) 일부만. 파서 분기가 적다.

## 눈에 띄는 제한

- truecolor 완전 지원 X (최근까지도 문제)
- ligature/powerline 글리프 렌더 품질 iTerm2보다 떨어짐
- split pane 없음 (tmux로 대체)
- shell integration 없음 (cwd 추적, 이전 명령 점프 등 불가)
- 검색이 선형

## iTerm2의 무게 원인

대부분 다음 네 가지에서 온다:

1. Metal 렌더러
2. Python API 서버
3. shell integration 파이프라인
4. 검색 인덱스

## 참고: 다른 터미널 포지셔닝

- **Ghostty / WezTerm / Alacritty** — GPU 렌더러를 쓰지만 기능셋을 칼같이 쳐내서 Terminal.app보다도 가벼운 느낌을 낸다.
- **Warp** — Electron 기반이라 베이스라인 메모리부터 무겁다. 대신 블록 UI/AI가 차별점.
- **kitty** — OpenGL 렌더러 + Python 플러그인. iTerm2와 유사한 부하 프로파일이지만 더 가볍다.

---

# 우리의 방향 — hexa-only AI-native 터미널

> 결정 2026-04-11: **Terminal.app 미니멀리즘을 철학으로 채택. 단, 구현은 전부 hexa-only AI-native.**

## 설계 원칙

1. **기능 삭제가 최적화다**
   Terminal.app이 가벼운 이유 = "부하 낼 기능이 없어서". 우리도 같은 방침. split/minimap/Python API/tmux integration 전부 안 넣는다. 정말 필요한 것만.

2. **단일 프로세스 + 단순 파서**
   xterm-256color subset만 파싱. truecolor/OSC 8(hyperlink)/OSC 133(shell integration) 세 개까지만 허용. Sixel/Kitty graphics는 의도적으로 배제.

3. **hexa-only 구현**
   - 파서, 상태머신, 스크롤백 버퍼, 이벤트 루프 — 전부 `.hexa`
   - PTY/termios 시스템콜만 `self/runtime.c`에 위임 (`.hexanoport` 정당화)
   - 렌더링은 일단 CPU glyph cache (GPU는 나중 판단)

4. **AI-native는 기능이 아니라 구조다**
   - 출력 스트림에 singularity/gap detector 내장 — iTerm2의 trigger 정규식과 달리 hook DSL로 표현
   - 프로젝트 감지 (project-aware) 기본 탑재 — `CLAUDE.md`/`shared/rules`/`infra_state.json` 자동 로드
   - 에이전트가 직접 입출력을 읽고 쓰는 PTY-level API를 내장 (iTerm2 Python API 대체)
   - discovery 허브(`shared/discovery/growth_bus.jsonl`)로 터미널 세션 이벤트 자동 방출

5. **버릴 것 (의도적 미지원)**
   - Metal/GPU 렌더러
   - 탭/스플릿 (tmux가 더 잘함)
   - 패스워드 매니저, 북마크, 프로파일 상속
   - 플러그인 시스템 (hook DSL 하나로 충분)
   - instant replay / 세션 저장

## 벤치마크 목표 (vs Terminal.app)

| 항목 | 목표 |
|------|------|
| cold start | ≤ Terminal.app (~200ms) |
| idle CPU | 0% (프레임타이머 없음) |
| 100k lines scrollback 메모리 | ≤ 2x Terminal.app |
| paste 100k chars 처리 | ≤ 50ms |
| binary size | ≤ 5MB (hexa runtime 포함) |

## 필요 hexa-lang 선행 작업

1. PTY 바인딩 (`openpty`, `forkpty`) — `self/runtime.c` 확장 + `.hexa` wrapper
2. termios struct 바인딩
3. NSView/AppKit 최소 바인딩 (또는 framebuffer 경로 검토)
4. UTF-8 grapheme cluster iterator (hexa string lib)
5. 비동기 이벤트 루프 — 현재 async_runtime.hexa 재사용 가능성 평가
