#!/usr/bin/env bash
# NEXUS-6 훅 자동 셋업 — 최초 1회 실행하면 전체 환경 구성
# 사용법: bash ~/Dev/nexus6/shared/hooks/setup.sh
set -e

HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG="$HOOK_DIR/hooks-config.json"
DEV_DIR="$HOME/Dev"
SETTINGS="$HOME/.claude/settings.json"

echo "=== NEXUS-6 Hook Setup v3.0-FINAL ==="
echo ""

# 1. hooks-config.json에서 화이트리스트 읽기
PROJECTS=$(python3 -c "import json; print(' '.join(json.load(open('$CONFIG'))['whitelisted_projects']))")
echo "[1] 화이트리스트: $PROJECTS"

# 2. 심링크 생성/복구
echo ""
echo "[2] 심링크 설정"
for proj in $PROJECTS; do
  dir="$DEV_DIR/$proj"
  [ -d "$dir" ] || { echo "  SKIP $proj (디렉토리 없음)"; continue; }
  [ "$proj" = "nexus6" ] && { echo "  SKIP nexus6 (원본)"; continue; }

  target="$dir/.shared"
  # TECS-L은 직접 nexus6/shared, 나머지는 TECS-L/.shared 경유
  if [ "$proj" = "TECS-L" ] || [ "$proj" = "fathom" ]; then
    link_to="../nexus6/shared"
  else
    link_to="../TECS-L/.shared"
  fi

  if [ -L "$target" ]; then
    current=$(readlink "$target")
    if [ "$current" = "$link_to" ]; then
      echo "  OK $proj → $link_to"
    else
      rm "$target"
      ln -s "$link_to" "$target"
      echo "  FIX $proj → $link_to (was: $current)"
    fi
  elif [ -d "$target" ]; then
    echo "  WARN $proj: .shared는 실제 디렉토리 — 수동 확인 필요"
  else
    ln -s "$link_to" "$target"
    echo "  NEW $proj → $link_to"
  fi
done

# 3. 스크립트 실행권한
echo ""
echo "[3] 실행권한 확인"
chmod +x "$HOOK_DIR"/*.sh 2>/dev/null
echo "  OK — *.sh 전체 chmod +x"

# 4. hooks-config.json → ~/.claude/settings.json 동기화
echo ""
echo "[4] settings.json 훅 동기화"

python3 - "$CONFIG" "$SETTINGS" <<'PYEOF'
import json, sys, os, shutil
from datetime import datetime

config_path, settings_path = sys.argv[1], sys.argv[2]
hooks_dir = os.path.dirname(config_path)

config = json.load(open(config_path))

# Build claude hooks format
claude_hooks = {}
for event, entries in config["hooks"].items():
    claude_hooks[event] = []
    for entry in entries:
        script = os.path.join(hooks_dir, entry["script"])
        hook_entry = {
            "hooks": [{"type": "command", "command": f"bash {script}"}]
        }
        if "matcher" in entry:
            hook_entry["matcher"] = entry["matcher"]
        claude_hooks[event].append(hook_entry)

# Backup + update settings
if os.path.exists(settings_path):
    backup = settings_path + f".bak-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    shutil.copy2(settings_path, backup)
    settings = json.load(open(settings_path))
    print(f"  백업: {backup}")
else:
    os.makedirs(os.path.dirname(settings_path), exist_ok=True)
    settings = {}

old_count = sum(len(v) for v in settings.get("hooks", {}).values())
settings["hooks"] = claude_hooks
new_count = sum(len(v) for v in claude_hooks.values())

with open(settings_path, "w") as f:
    json.dump(settings, f, indent=2, ensure_ascii=False)
    f.write("\n")

print(f"  훅: {old_count} → {new_count} entries")
print(f"  이벤트: {', '.join(claude_hooks.keys())}")
PYEOF

# 5. 검증
echo ""
echo "[5] 검증"
# 배너 테스트
BANNER=$(bash "$HOOK_DIR/nexus6-banner.sh" 2>/dev/null)
if echo "$BANNER" | python3 -c "import sys,json; json.load(sys.stdin)" 2>/dev/null; then
  echo "  OK — 배너 정상"
else
  echo "  WARN — 배너 출력 확인 필요: $BANNER"
fi

# settings.json hooks 존재 확인
HOOK_COUNT=$(python3 -c "import json; h=json.load(open('$SETTINGS')).get('hooks',{}); print(sum(len(v) for v in h.values()))")
echo "  OK — settings.json에 $HOOK_COUNT hook entries"

echo ""
echo "=== 셋업 완료 ==="
echo "프로젝트 추가: hooks-config.json의 whitelisted_projects에 추가 후 재실행"
