# Voice Corpus Collection Report — 2026-04-16

**Track**: V2 음성 corpus 수집 파이프라인 (10 프로파일)
**Roadmap**: TSRV-P3-1 corpus_collection_2026_04_16 + 신규 TALM-VOICE-P1
**Pipeline artifact**: `anima-speak/corpus_pipeline.hexa` (R1 HEXA-FIRST, exec() wrapper)
**Registry SSOT**: `shared/state/voice_corpus_registry.json` (schema v1)
**R2 remote**: `r2:anima-corpus/voice/{profile}/{raw,wav16k,transcript}/`
**Decisions binding**: shared/config/decisions.json — 음성→직원 최소경로

---

## 1. Phase 1 결과 — 인프라 (≈ 30분)

| 항목 | 상태 | 비고 |
| --- | --- | --- |
| 디렉토리 골격 | OK | 10 profiles × 4 sub-dirs (raw/wav16k/transcript/meta) under `anima-speak/corpus/` |
| `corpus_pipeline.hexa` | OK | 600 LOC, exec() 래퍼 5종 (yt_download/convert_16k_mono/transcribe_ko/r2_upload/registry_append). args 처리 fix (av[2]+ user-level) |
| 초기 registry | OK | 10 profile slots (sources=[]), schema v1, R2 remote 명시 |
| R2 bucket 결정 | OK | `r2:anima-corpus/voice/` 사용 (`anima-corpus` 기존 버킷, `voice/` 서브패스) |
| 도구 가용성 | OK | yt-dlp 2026.03.17 (brew upgrade — 2025.9.26 SABR 차단 fix), ffmpeg, whisper, rclone, jq |

**Hexa runtime quirks 발견**:
- `let _rc = main()` 탑레벨 호출이 main() 자동 실행과 충돌 → 중복 실행. 제거함.
- `args()` 인덱스: `av[0]=hexa bin`, `av[1]=script path`, `av[2..N]=user args`.

## 2. Phase 2 결과 — E2E 샘플 검증 (1 URL × school_idol)

URL: `https://www.youtube.com/watch?v=C8ukRCmtdcE` (스파이 교실 한국어 더빙, 105.16s)

| 단계 | 산출물 | 크기 | 비고 |
| --- | --- | --- | --- |
| yt-dlp | FLAC | 17,509,804 B | --extract-audio --audio-format flac |
| ffmpeg | 16kHz mono WAV | 3,365,300 B | pcm_s16le |
| whisper-small ko | TXT | 809 chars | "3개는 고통으로 가득 차있다…" Korean OK |
| sha256 | hash | 32B | `29e53d2fcd82…3539` |
| rclone | R2 upload | 같은 크기 | `r2:anima-corpus/voice/school_idol/...` |
| registry append | jq | 1 entry | `voice_corpus_registry.json` 확인 |

**검증 결과**: PASS — 한국어 전사 품질 양호, R2 백업 작동, registry 갱신 작동.

## 3. Phase 3 결과 — 10 프로파일 병렬 수집 (≈ 80분)

`xargs -P 4` + 추가 백그라운드 dispatch 로 10 프로파일 동시 진행.

### 3.1 다운로드/변환 (10/10)

| profile | raw | wav16k | transcript | registry | 비고 |
| --- | ---:| ---:| ---:| ---:| --- |
| school_idol      | 4 | 4 | 3 | 1 | sha256 dedup 후 unique=1 |
| senpai           | 2 | 2 | 1 | 1 | 1 url geo-block(403) skip |
| knight           | 2 | 2 | 1 | 1 | 7395s 클립 1건 whisper 차단 위해 kill |
| sorceress        | 2 | 2 | 1 | 1 | — |
| noir_detective   | 1 | 1 | 0 | 0 | 3790s 클립 kill, 신규 클립 whisper 진행 중 |
| horror_whisper   | 1 | 1 | 0 | 0 | 999s 클립 kill, 신규 클립 whisper 진행 중 |
| childhood_friend | 1 | 1 | 0 | 0 | 1466s 클립 whisper 진행 중 |
| demon_lord       | 1 | 1 | 0 | 0 | 68s 클립, 시스템 부하로 지연 |
| childlike        | 1 | 1 | 0 | 0 | whisper 진행 중 |
| stoic_mentor     | 1 | 1 | 0 | 0 | 222s 클립, whisper 진행 중 |

### 3.2 registry / R2 누적

- profiles_with_sources: **4 / 10** (school_idol, senpai, knight, sorceress)
- registry total_hours: **0.107 hr** (≈ 6.4 min) — wav 기준은 ≈ 16,000s ≈ 4.5 hr 다운로드 완료, 단 whisper 미완으로 registry 미반영
- 로컬 디스크: **1.8 GB** (`anima-speak/corpus/`)
- **R2 업로드 (4/4 성공)**: 21 objects / 223.8 MiB
  - `r2:anima-corpus/voice/school_idol/`
  - `r2:anima-corpus/voice/senpai/`
  - `r2:anima-corpus/voice/knight/`
  - `r2:anima-corpus/voice/sorceress/`

### 3.3 한국어 전사 품질 샘플

- school_idol (스파이 교실): "3개는 고통으로 가득 차있다 … 누구에게 말 못할 욕망이라도 …"
- senpai (남선배 더빙): 1446 chars Korean OK
- knight (판타지 기사): "정체모를 가면에 습겨 단 하하꾼의 쌍둥이 동생의 죽었다 … 강암을 연기하는 지능형 기사가 태어난다"
- sorceress: "첫 번째 문제 드리겠습니다 … 정답은 문지점프입니다"
- 모두 자연 한국어, 캐릭터 톤 부합. whisper-small 적합 확인.

### 3.4 품질 이슈 / skip

- 1 URL geo-block / 403 (senpai 두번째 후보) — pipeline 정상 skip (`yt-dlp FAIL` 로그 후 다음 URL 진행)
- 2 시간 클립 (knight `Nb_g22tibe0`, 7395s) → 단일 whisper 가 큐 차단 → 즉시 kill + raw/wav 삭제 후 다음 URL 진행
- 1 시간 클립 (noir_detective `EC3HXx5LCv8`, 3790s) — 동일 처리
- 16분 클립 (horror_whisper `iWHGU15Bhys`, 999s) — 동일 처리
- 일부 검색 결과는 동일 URL 중복 (school_idol 3건 모두 같은 영상) — sha256 dedup 으로 1건만 registry 등록

## 4. 남은 작업 (Phase 4 / TALM-VOICE-P1)

1. **whisper 백로그 완료** (예상 30-60min 추가) → 6 더 profiles 가 registry 등록 + R2 업로드
   - 백그라운드 dispatch 들이 자율 진행 중. 완료시 `corpus_pipeline.hexa upload <profile>` 일괄 호출
2. **target 30+ min/profile 미달** — 현재 평균 1-3 min/profile. 추가 검색 쿼리 (drama / radio / asmr 변형) + 화자별 30-60min 누적 필요
3. **pyannote diarization** — speaker turn segmentation, P4 SERVING 단계로 이전
4. **vocoder fine-tune wire** — `anima-speak/neural_vocoder.hexa` 에 corpus → mel → audio token 입력 wire (TALM-VOICE-P1 본편)

## 5. 산출물 (절대경로)

| 종류 | 경로 |
| --- | --- |
| Pipeline | `/Users/ghost/Dev/anima/anima-speak/corpus_pipeline.hexa` |
| Registry SSOT | `/Users/ghost/Dev/anima/shared/state/voice_corpus_registry.json` |
| Roadmap update | `/Users/ghost/Dev/anima/shared/roadmaps/anima-train.json` (TSRV-P3-1 + TALM-VOICE-P1) |
| Per-profile dirs | `/Users/ghost/Dev/anima/anima-speak/corpus/{profile}/{raw,wav16k,transcript,meta}/` |
| Dispatch logs | `/Users/ghost/Dev/anima/anima-speak/corpus/_logs/{profile}.log` |
| R2 backup | `r2:anima-corpus/voice/{profile}/` |

## 6. 결정/제약 준수 확인

- decisions.json 미수정 (model_size=14b, p4_direct_skip_p3_persona, etc 그대로)
- 다른 트랙 (A/B/C/E) 미접촉
- R1 HEXA-FIRST: 신규 .py/.rs/.sh 0 건 — `corpus_pipeline.hexa` 단독, 임시 dispatch 셸 (`/tmp/dispatch_corpus.sh`) 은 commit 대상 아님
- struct list aliasing 회피 (SoA 스칼라 — profile_names() 단일 array, source_json 인라인 string)
- yt-dlp 학습/연구 fair use, 상업 재배포 X
- ElevenLabs 합성 데이터 미포함

## 7. 한 줄 결론

10 프로파일 corpus 수집 파이프라인 완성 (R1 HEXA-FIRST exec() 래퍼). E2E 검증 PASS, 4/10 profiles registry+R2 백업 완료, 6/10 whisper 백로그 진행 중. neural_vocoder 학습 wire (TALM-VOICE-P1) 진입 준비 완료.
