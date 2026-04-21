status: deprecated
moved_at: 2026-04-14
moved_from: shared/hooks/
replacement: shared/harness/entry.hexa (dispatcher) + shared/harness/{prompt_scan,pre_tool_guard,post_bash,post_edit,cmd_gate}.hexa
compat_symlink: shared/hooks → shared/archive/hooks-20260414 (하위 호환 — 새 참조 금지)
why: 훅 시스템 완전 제거 refactor — settings.json hooks={} 로 모든 프로젝트 훅 비활성화됨. 실행은 exec_validated + harness entry 자율 호출로 대체.
do_not: 이 폴더 내 파일 수정/추가 금지. 새 규칙은 shared/harness/ 로.
