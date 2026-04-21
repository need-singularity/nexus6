# annot_rules.json prospective → active 채택 보고서

ts: 2026-04-19
session: annot adoption migration (autonomous)
ssot: shared/config/annot_rules.json (v0.2 → v0.3)

## 결정

annot_rules.json status `prospective` → `active`. kind=alias 19 룰 채택 정식화 + lint warn gate 자동 활성.

## 검증 (재확인)

전 .hexa 파일 (`.claude/worktrees/`, `build/` 제외) — 2504 파일 — 19 alias from-marker 전수 grep:

| marker | hits | marker | hits |
|---|---|---|---|
| @phi_engine | 0 | @anima_runtime | 0 |
| @phi_ready | 0 | @schedule_wakeup | 0 |
| @phi_big | 0 | @feedback_loop | 0 |
| @consciousness_probe | 0 | @causal_power | 0 |
| @consciousness_engine | 0 | @degrees_of_freedom | 0 |
| @conscious_chip | 0 | @theory_of_mind | 0 |
| @classical_chip | 0 | @self_determined | 0 |
| @iit_chip | 0 | @memory_hierarchy | 0 |
| @autonomy_loop | 0 | @cache_kv | 0 |
|  |  | @eeg_channel | 0 |

총 alias 사용: 0건. 메모리 `p-annot-rules-prospective` (2026-04-16 작성) 결과 재확인 — 변동 없음.

비-.hexa 잔존 참조 (정보용, 채택에 영향 없음):
- `shared/config/annot_rules.json` (자체)
- `shared/bin/hexa-rule` (alias 정의 처리기 — comment)
- `shared/bin/hexa-meta-map` (`@theory_of_mind` 메타-인지 kind, alias 와 충돌 가능성 — known_clash 등재)
- `shared/state/annot_system_build_20260416.json` (마이그레이션 이력)
- `shared/tool/lint_annot.hexa` (검사 엔진)
- `shared/tool/thinking_log.jsonl` (로그)

## 변경 산출물

1. **shared/config/annot_rules.json** v0.2→v0.3
   - `status: "active"` 추가
   - `adoption{}` 블록 추가 (verification + enforcement + known_clashes)

2. **shared/tool/entry.hexa**
   - `lint_annot` 모드 추가 (dispatch_file → lint_annot.hexa)
   - 사용법 docstring + unknown-mode REJECT msg 갱신

3. **shared/tool/post_edit.hexa**
   - `auto_lint_annot()` 추가 — .hexa Write/Edit 후 자동 lint_annot scan 호출
   - 우회: `NEXUS_NOAUTOLINT=1` 또는 `NEXUS_ANNOT_OK=1`
   - 자기참조 회피: `lint_annot.hexa`, `pre_tool_guard.hexa`, `post_edit.hexa`

## 강제 매트릭스

| kind | layer | action | bypass |
|---|---|---|---|
| name (forbid) | pre_tool_guard.check_annot_rules | block (Write/Edit) | NEXUS_ANNOT_OK=1, @allow-annot |
| enforce (block) | pre_tool_guard.check_annot_rules | block (Write/Edit) | NEXUS_ANNOT_OK=1, @allow-annot |
| alias (deprecated) | post_edit.auto_lint_annot + lint_annot.hexa | warn + lint_log.jsonl | NEXUS_NOAUTOLINT=1, NEXUS_ANNOT_OK=1 |

## 검증 통과

- `hexa parse shared/tool/entry.hexa` → OK
- `hexa parse shared/tool/post_edit.hexa` → OK
- `hexa parse shared/tool/lint_annot.hexa` → OK
- `hexa run shared/tool/lint_annot.hexa scan shared/tool/` → exit 0, 0 violations
- `jq . shared/config/annot_rules.json` → JSON OK, .rules length=33

## 알려진 충돌

- `@theory_of_mind` (alias from): hexa-meta-map 메타-인지 kind 와 명칭 동일. 현 시점 .hexa 사용 0건이므로 보류. 첫 사용자 등장 시 disambiguator 또는 alias 폐기 결정 필요 (annot_rules.json adoption.known_clashes 등재).

## 후속

- 신규 .hexa 작성 시 alias from-marker 사용하면 lint_log.jsonl 에 warn append + stderr 출력
- pre-commit 단계 차단은 의도적으로 하지 않음 (warn-only) — 실 사용 패턴 누적 후 enforce로 승격 여부 결정
- alias to-marker (@phi/@chip/@anima 등) 의 discriminator 사용 패턴 정착 시 alias 룰 자체 제거 검토
