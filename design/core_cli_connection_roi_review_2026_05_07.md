# ~/core CLI ↔ nexus 연결 ROI 검토 (2026-05-07)

세션 문서. ~/core/* 산하 프로젝트를 nexus 통합 CLI (`nexus <subcmd>`,
spec=`engine/nexus_cli_spec.json`) 에 추가 노출할 때의 가치 평가.

전제:
- 모든 후보가 자체 CLI 를 *가진다는 가정* 하에 (CLI 부재는 평가 제외 사유로 쓰지 않음)
- 각 프로젝트의 *주제* 한 줄만 보고 평가 (활용도 grep 메트릭 제외)
- 외부 (hive 등) 가 `nexus <subcmd>` 로 호출했을 때 받을 수 있는 가치 = ROI

---

## 1. 현재 상태

### 1.1 이미 연결된 표면

| subcmd | 위치 | 분류 |
|---|---|---|
| qmirror | `cli/qmirror.hexa` (router → ~/core/qmirror) | 외부 standalone shellout |
| sim     | `cli/sim.hexa` (router → ~/core/sim-universe) | 외부 standalone shellout |
| atlas / lens / discovery / drill / smash / gap / meta-closure / hyperarithmetic / thinking / free / absolute / roadmap / status / projects / promote / bus / version | nexus 내부 | nexus 자체 인지·메타 표면 |

`spec.projects` enum (roadmap/atlas 등이 받는 enum):
nexus, anima, CANON, papers, hexa-lang, void, airgenome (7).

### 1.2 라우터는 있는데 spec drift 인 것

| 라우터 | dispatch | spec 등록 |
|---|---|---|
| `cli/bio.hexa`  | `cmd_bio`  | ❌ |
| `cli/mc.hexa`   | `cmd_mc`   | ❌ |
| `cli/qrng.hexa` | `cmd_qrng` | ❌ |

→ 외부 인지 SSOT(spec) 만 채우면 즉시 가시성 회복. `nexus-cli --sync --apply` 후보.

---

## 2. hexa-bio 가 sister CLI 를 활용하는 패턴 (참조 모범)

`~/core/hexa-bio` 가 4 sister repo (qmirror / sim-universe / anima / hexa-brain)
+ runtime-host (hexa-lang) 를 outbound-consume 하는 방식:

1. **subprocess 직접 dispatch** (Python bridge 경유)
   - `_python_bridge/module/quantum_entropy_qmirror.py` → `qmirror` CLI subprocess
     로 quantum bytes → VQE optimizer seed
   - `_python_bridge/module/quantum_simu_multiverse.py` → `sim-universe multiverse
     --m=M --t=T --json` → ribozyme variant 평행 미니월드 매핑
   - `quantum/module/hexabrain_consumer.hexa` → `hexa-brain core --help` →
     RIBOZYME C2-δ senolytic 후보 트리거
2. **pattern absorption** (subprocess 안 부르고 알고리즘만 흡수)
   - `_python_bridge/module/quantum_anima_phi.py` 가 anima 의 IIT 4.0 pyphi pin
     (`feature/iit-4.0` b78d0e3) 만 동일 채택
3. **upstream pulse check** — `quantum/module/upstream_pulse_check.hexa` 가
   sister repo 들 git log 만 읽어 "성능·자원·속도·알고리즘 발견 시 개선"
   루프 (cycle 49 qmirror absorption 패턴 일반화)

핵심 규율: `own 2` (outbound-consumer-only), `own 3` (cross-session port
discipline). in-tree import 금지, subprocess CLI only.

사용자 directive 인용 (2026-05-07):
> "cli 로 연결하여 사용하는 모든것들 서로의 upstream 성능,자원,속도,
>  알고리즘 발견시 개선"

---

## 3. 활용도 메트릭 (참고용 — 메인 판정 아님)

~/core 후보들의 sister-CLI 참조 카운트 (grep, self-ref 포함).

| project | qmirror | qrng | sim | anima | brain | subproc | 등급 |
|---|---|---|---|---|---|---|---|
| forge       | 80  | 27 | 0 | 7   | 0   | 65 | S |
| hexa-brain    | 5   | 0  | 1 | 430 | 344 | 55 | S (anima 의 짝) |
| anima-agent   | 3   | 0  | 3 | 51  | 4   | 22 | A |
| airgenome     | 0   | 0  | 0 | 70  | 0   | 37 | A |
| mc-integrate  | 5   | 2  | 6 | 3   | 0   | 5  | A (sim+qmirror+qrng 트리플 micro-hub) |
| ghost         | 3   | 0  | 0 | 0   | 0   | 11 | B |
| lumiere       | 0   | 0  | 0 | 3   | 0   | 0  | B |
| hexa-cern/cosmos/rtsc/ufo/sscb | 0 | 0 | 0 | 0 | 0 | ≤9 (self) | C — SPEC 단계 |
| convergence   | 0   | 0  | 0 | 0   | 0   | 0  | C |

---

## 4. 주제 단일 기준 ROI (메인 판정)

판정 룰:
- 재현 가능한 *측정·검증·생산* 표면 (수치 verdict 出) → **高**
- *atlas/spec/카탈로그* (read-only 인지) → **中**
- *substrate 메타·유틸·결 다른 도메인* → **低**

| 프로젝트 | 주제 한 줄 | ROI |
|---|---|---|
| qrng           | 양자 RNG 5-backend provider (mock/curby/anu/nist/hardware) | **高** |
| forge        | closure cond 검증 + wraith 암호 handoff 게이트 | **高** |
| anima-agent    | IIT Φ-driven 자율 에이전트 (cli/mcp/channel/autonomy) | **高** |
| hexa-bio       | 리보자임·캡시드·나노봇·VQE 분자 실험 | **高** |
| hexa-brain     | 신경 substrate / EEG 마커 / OpenBCI | **高** |
| mc-integrate   | Monte Carlo 수치 적분 (상수 추정 + RNG 비교) | **高** |
| hexa-cern      | 입자가속기 (mini/parent/classical 100MeV~) | 高 |
| hexa-rtsc      | 상온 초전도 + falsifier preregister | 高 |
| hexa-millennium| Clay 밀레니엄 7난제 | 高 |
| hexa-cosmos    | n=6 ΛCDM 우주론·입자우주·관측소 | 中 |
| hexa-fusion    | 핵융합 / 플라즈마 | 中 |
| hexa-antimatter| 반물질 substrate | 中 |
| hexa-chip      | 칩 substrate | 中 |
| hexa-os        | OS substrate | 中 |
| hexa-codex     | 코드 codex / 분석 | 中 |
| hexa-scope     | 관측·스코프 substrate | 中 |
| hexa-bot       | 봇 substrate | 中 |
| hexa-energy    | 에너지 substrate | 中 |
| hexa-sscb      | 솔리드스테이트 회로 차단기 (좁음) | 中-低 |
| hexa-ufo       | UFO atlas + 7-stage 추진 doc | 中-低 |
| hexa-pet / hexa-fantasy | 펫·판타지 결 | 低 |
| hexa-time / hexa-space / hexa-earth | 추상 substrate (verb 약) | 低 |
| lumiere / pixie / contact | 정체 모호 / 도메인 외 | 低 |
| ghost / browser-harness / mouse_remap / window_magnet / skynet-timer | opsec / 유틸리티 | 低 |
| cake-wallet / wraith-wallet | 암호화폐 지갑 (nexus 결 아님) | 低 |
| gamebox / airgenome-gamebox | 게임 빌드 표면 | 低 |
| convergence    | nexus integration contracts (이미 nexus 내부) | n/a |
| archive-* / cl_archive / legacy | 아카이브 | n/a |

### 4.1 高 등급 ROI 순위 (신규 후보 9 개)

1. **qrng** — 양자 비트, qmirror 의 자매. 외부 항상 가치
2. **forge** — 검증 게이트, qmirror 와 동급
3. **anima-agent** — Φ-driven 의식 측정, 시장 희소 표면
4. **hexa-brain** — 신경 신호 입력, 다운스트림 트리거 풍부
5. **hexa-bio** — 분자 실험 numerical (VQE 0.4 µHa)
6. **mc-integrate** — RNG 다운스트림 numerical
7. **hexa-cern** — 입자물리 실험
8. **hexa-rtsc** — 상온 초전도 falsifier
9. **hexa-millennium** — Clay 7난제

---

## 5. mc-integrate standalone 가치 (사례 분석)

`~/core/mc-integrate` (독립 git repo, v1.0.0 릴리즈, 2026-05-04 nexus 에서
Phase 1 decouple 으로 분리. sim-universe 하드코드 제거).

주제 한 줄: "Productized callable Monte Carlo 수치 적분기 (deterministic LCG 코어)".

CLI 표면:
- `estimate` — catalan / zeta3 / euler_gamma / pi5_times_n6
- `compare`  — 두 RNG backend 사이 Welch-t 구별불가능성
- `self-test`— F2/F3/F4/F5 + G1..G6 falsifier sweep
- `status`   — 모듈 + 4-tier ANU resolution probe

### Standalone 가치 (4 가지)

1. **RNG 다운스트림 검증 표면**
   qrng·qmirror 가 "비트 생산"이라면 mc-integrate 는 그 비트가 numerical
   에서 동등하게 작동하는지 Welch-t 로 검증. 양자 RNG 의 *품질 게이트*.
   3 단(생산→검증→소비) 중 마지막 칸.
2. **nexus 의존성 0 → 다중 소비자 허용**
   nexus 에 묻혀있으면 hive/forge/hexa-bio/anima-agent 가 in-tree import
   해야 함 (own 2 위반). standalone 이라 subprocess CLI 만으로 모두 소비.
3. **결정론적 LCG 코어 → 재현성**
   LCG seed/state 가 mc-integrate 안에서 격리. 외부 소비자들이 자기 RNG
   결을 오염시키지 않음 (own 3 cross-session port discipline 과 직결).
4. **사이즈 작음 + 깊이 있음**
   install 비용 0, 주제 폭은 좁지만(numerical 적분만) catalan/zeta3/
   euler_gamma/pi5×n6, Welch-t, F2~F5 falsifier 까지 깊음.

→ standalone 가치는 *주제 자체의 크기* 가 아니라 **qrng·qmirror 와 한 결의
다운스트림을 외부에 열어주는 마지막 칸이라는 위치**에서 나옴.

---

## 6. 다음 액션 후보 (우선순위)

1. **spec drift 픽스** — `nexus-cli --sync --apply` 로 bio/mc/qrng 를
   `engine/nexus_cli_spec.json` 에 등록. 라우터·dispatch 는 이미 존재.
   (가장 짧고 즉효)
2. **`nexus forge` 라우터 추가** — `cli/sim.hexa` 65 라인 그대로 복사,
   4-tier resolve 만 `FORGE_ROOT` 로 교체. hexa-bio 의
   `SISTER_REPOS` 에 forge 추가 → upstream_pulse_check 5-repo 확장.
3. **`nexus anima-agent` 라우터 추가** — 같은 패턴. MCP 서버 모드까지
   라우팅하면 가치 最高.
4. (선택) **`nexus hexa-brain` 라우터** — anima-agent 와 짝.
5. (선택) **`nexus mc` spec 등록 후, hexa-bio numerical bridge 활용**.

---

## 7. 기록한 판정의 한계 (raw#10 honest C3)

1. ROI 표는 *주제 한 줄* 만 본 평가. 실제 ROI 는 표면 안정성·테스트 커버리지
   ·다운스트림 소비자 수에 좌우되며 본 문서에 미반영.
2. "高/中/低" 3 단계는 균등 간격 아님. 예: forge 의 高 와 hexa-millennium
   의 高 는 다운스트림 결합도가 다름.
3. CLI 부재 후보 (hexa-cern·cosmos·rtsc·ufo 등 SPEC-only) 는 "CLI 가
   있다고 가정" 하에 평가. 구현 비용 미반영.
4. 활용도 메트릭(§3)은 grep 카운트로 self-reference 포함. forge 의
   qmirror=80, anima-agent 의 anima=51 등에는 self-ref 가 일부 섞임.
5. `convergence` 는 nexus 내부 표면이라 "n/a" 처리했으나, 별도 노출
   가치(integration contracts read-only 인지) 는 추가 검토 가능.
