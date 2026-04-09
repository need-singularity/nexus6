#!/usr/bin/env bash
# Quick integration test: run 1 full cycle and verify state changes
set -euo pipefail

TECS_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CONFIG="$TECS_ROOT/config"

echo "=== TECS-L Discovery Loop Integration Test ==="

# 1. Measure
echo "1. Testing measure..."
/usr/bin/python3 "$TECS_ROOT/scripts/tecs_measure.py" || { echo "FAIL: measure"; exit 1; }
echo "   PASS"

# 2. Act
echo "2. Testing act..."
/usr/bin/python3 "$TECS_ROOT/scripts/tecs_act.py" N dfs || { echo "FAIL: act"; exit 1; }
echo "   PASS"

# 3. Validate
echo "3. Testing validate..."
/usr/bin/python3 "$TECS_ROOT/scripts/tecs_validate.py" || { echo "FAIL: validate"; exit 1; }
echo "   PASS"

# 4. Record
echo "4. Testing record..."
/usr/bin/python3 "$TECS_ROOT/scripts/tecs_record.py" || { echo "FAIL: record"; exit 1; }
echo "   PASS"

# 5. Publish (dry-run)
echo "5. Testing publish (dry-run)..."
/usr/bin/python3 "$TECS_ROOT/scripts/tecs_publish.py" --dry-run || { echo "FAIL: publish"; exit 1; }
echo "   PASS"

# 6. Verify state files exist and are valid JSON
echo "6. Checking state files..."
/usr/bin/python3 -c "import json; json.load(open('$CONFIG/domain_registry.json'))" || { echo "FAIL: registry JSON"; exit 1; }
/usr/bin/python3 -c "import json; json.load(open('$CONFIG/loop_state.json'))" || { echo "FAIL: loop_state JSON"; exit 1; }
echo "   PASS"

# 7. Daemon dry-run
echo "7. Testing daemon (1 cycle, dry-run)..."
bash "$TECS_ROOT/scripts/tecs_discovery_loop.sh" --max-cycles 1 --interval 1 --dry-run || { echo "FAIL: daemon"; exit 1; }
echo "   PASS"

echo ""
echo "=== ALL 7 TESTS PASSED ==="
