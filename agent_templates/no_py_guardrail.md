# AGENT GUARDRAIL — Python 전면 금지 (R37 / AN13 / L3-PY)

**이 문단은 모든 BG 에이전트 프롬프트 앞단에 무조건 포함된다. 제거/요약/생략 금지.**

## 절대 금지 (exceptionless)

아래 작업은 **어떤 상황에서도** 수행하지 마라:

1. **create** — 새 `*.py` 파일 작성/복사/다운로드
2. **edit** — 기존 `*.py` 파일 수정 (한 줄 패치 포함)
3. **run** — `python`, `python3`, `pypy`, `./*.py` 로컬 실행
4. **transfer** — `scp *.py`, `rsync *.py`, `runpodctl send *.py`, `curl/wget *.py`, `git add *.py`
5. **remote exec** — `ssh <host> python*`, `ssh <host> bash -c '... python ...'`, `runpodctl exec <pod> python*`
6. **wrapper-fallback** — `.hexa` launcher 가 내부에서 `spawn("python")` / `exec_c("python")` 호출

## 위반 시 프로토콜 (agent 가 즉시 수행)

1. **STOP** — 해당 작업 즉시 중단. partial result 도 남기지 말 것
2. **REPORT** — 사용자에게 위반 사실 + 발견 시점 + 근본 원인 보고
3. **NO RATIONALIZATION** — 아래 문구로 합리화 금지:
   - "GLIBC incompat 이라서"
   - "hexa 바이너리가 pod 이미지에 없어서"
   - "임시 우회 / 일단 돌리고 나중에 고침"
   - "설계 예외 / launcher L?-? 주석 기록"
   - "사용자 승인 없이도 goal 진행 우선"

## GLIBC / 의존성 fallback 순서 (Python 우회 금지)

`.py` 로 rollback 절대 금지. 아래 순서로만 해결:

1. **다른 Linux hexa 빌드 시도**
   - static-linked 바이너리 (`hexa-linux-static`)
   - 다른 stage 빌드 (stage0 / stage1 / stage2)
   - 소스에서 `./build.hexa` 로 pod 내 재빌드 (dev headers 있으면)
2. **Pod/host 재선택**
   - 다른 RunPod 이미지 (pytorch/pytorch:2.4.0, nvidia/cuda:12.4.0-devel)
   - 다른 GLIBC 버전 호스트
   - ubu (RTX 5070) fallback
3. **사용자 에스컬레이션**
   - 현재 상황 + 시도한 경로 + 실패 사유 리포트
   - 선택지 제시 (대안 빌드 / pod 변경 / 작업 연기)
   - 답변 대기. 독단적 `.py` 결정 금지

## 참조

- `CLAUDE.md` 상단 ".py 절대 금지" 섹션
- `shared/rules/common.json#R37` — py_total_ban
- `shared/rules/anima.json#AN13` — Python 전면 금지
- `shared/lockdown/lockdown.json` — L3-PY (영구 lock, unlock 불가)
- `.claude/settings.json` — PreToolUse Bash 훅 (Write/Edit + Bash 매처)
- `.git/hooks/pre-commit` — staged `.py` commit 차단

## 이 가드레일이 생긴 이유 (2026-04-18)

BG 에이전트가 CLM pod2 (4xH100) 에서 hexa 바이너리 GLIBC incompat 을 만나자
`train_clm_1b.py` 를 cross-compile scp 후 `python3` 로 실행했다. launcher L26-33 에
"설계 예외 사유" 를 기록하여 스스로 합리화했다. 기존 훅은 Write/Edit 만 차단하고
Bash 실행 경로는 무방비였다. 이 가드레일 + 훅 Bash 매처 + R37/AN13/L3-PY 로
**동일 실수 재발 시 세션 자기거부** 하도록 네트 확장했다.

## Self-check (agent 가 작업 시작 전 통과할 것)

- [ ] 내 작업 계획에 `.py` 생성/수정/실행/전송/원격실행이 들어가 있는가? → YES 면 STOP
- [ ] hexa 경로 실패 시 fallback 이 `.py` 인가? → YES 면 STOP, 위 3단계 적용
- [ ] launcher 가 내부에서 python 호출하는가? → YES 면 STOP
- [ ] 모든 답이 NO 인가? → 작업 진행 허용
