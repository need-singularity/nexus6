#!/usr/bin/env bash
# "go" 키워드 감지 → 모든 TODO 병렬 실행 지시
set +e

INPUT=$(cat)

# grep/sed로 직접 추출 (HEXA 우회 — 단순 키워드 매칭에는 불필요)
USER_TEXT=$(echo "$INPUT" | grep -o '"prompt"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"prompt"[[:space:]]*:[[:space:]]*"//;s/".*//')

[ -z "$USER_TEXT" ] && exit 0

TRIMMED=$(echo "$USER_TEXT" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' | tr '[:upper:]' '[:lower:]')

if [ "$TRIMMED" = "go" ] || [ "$TRIMMED" = "모두" ] || [ "$TRIMMED" = "전체실행" ] || [ "$TRIMMED" = "병렬" ]; then
  cat <<'DIRECTIVE'
<user-prompt-submit-hook>
[GO 모드] 사용자가 "go"를 입력했습니다.

필수 행동:
1. 이 프로젝트의 TODO/현황을 빠르게 스캔 (README, 최근 커밋, 미완료 작업)
2. 발견된 모든 작업을 우선순위별로 정리
3. 독립적인 작업들을 최대한 병렬 Agent로 동시 발사 (run_in_background: true)
4. 발사 테이블 출력 후 결과 대기
5. "모두" 와 동일 — 확인 질문 없이 즉시 전체 실행

금지: 확인 질문, 일부만 선택, 순차 실행
</user-prompt-submit-hook>
DIRECTIVE
fi

exit 0
