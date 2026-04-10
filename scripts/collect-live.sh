#!/usr/bin/env bash
# 실시간 시스템 메트릭 수집 → /tmp/n6_live.txt
OUT="/tmp/n6_live.txt"
uptime | grep -oE '[0-9]+\.[0-9]+' > "$OUT"
ps aux | wc -l | tr -d ' ' >> "$OUT"
df -h / | tail -1 | awk '{print $5}' | tr -d '%' >> "$OUT"
vm_stat | grep "Pages active\|Pages wired\|Pages free" | grep -oE '[0-9]+' >> "$OUT"
sysctl -n hw.memsize | awk '{print $1/1073741824}' >> "$OUT"
sysctl -n hw.ncpu >> "$OUT"
