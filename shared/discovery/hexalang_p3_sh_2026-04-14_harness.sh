#!/bin/bash
HEXA_NATIVE="/Users/ghost/Dev/hexa-lang/build/artifacts/hexa_native"
HEXA_RUST="/Users/ghost/Dev/hexa-lang/hexa"
EXAMPLES="/Users/ghost/Dev/hexa-lang/examples"
OUT_JSONL=/tmp/hexa_compare.jsonl
> "$OUT_JSONL"

run_with_timeout() {
  perl -e '
    my $pid = fork();
    if ($pid == 0) { exec(@ARGV); exit 127; }
    $SIG{ALRM} = sub { kill 9, $pid; };
    alarm(3);
    waitpid($pid, 0);
    exit($? >> 8 || ($? & 127 ? 128+($? & 127) : 0));
  ' "$@"
}

native_pass=0
rust_pass=0
both_pass=0
both_match=0
total=0

for f in "$EXAMPLES"/*.hexa; do
  total=$((total+1))
  native_out=$(run_with_timeout "$HEXA_NATIVE" "$f" 2>/dev/null)
  nc=$?
  rust_out=$(run_with_timeout "$HEXA_RUST" run "$f" 2>/dev/null)
  rc=$?
  native_ok=0
  rust_ok=0
  [ $nc -eq 0 ] && [ -n "$native_out" ] && native_ok=1
  [ $rc -eq 0 ] && [ -n "$rust_out" ] && rust_ok=1
  [ $native_ok -eq 1 ] && native_pass=$((native_pass+1))
  [ $rust_ok -eq 1 ] && rust_pass=$((rust_pass+1))
  if [ $native_ok -eq 1 ] && [ $rust_ok -eq 1 ]; then
    both_pass=$((both_pass+1))
    if [ "$native_out" = "$rust_out" ]; then
      both_match=$((both_match+1))
      status="MATCH"
    else
      status="DIFF"
    fi
  elif [ $native_ok -eq 1 ]; then
    status="NATIVE_ONLY"
  elif [ $rust_ok -eq 1 ]; then
    status="RUST_ONLY"
  else
    status="BOTH_FAIL"
  fi
  bn=$(basename "$f")
  echo "{\"file\":\"$bn\",\"nc\":$nc,\"rc\":$rc,\"status\":\"$status\"}" >> "$OUT_JSONL"
done
echo "TOTAL=$total NATIVE_PASS=$native_pass RUST_PASS=$rust_pass BOTH_PASS=$both_pass MATCH=$both_match"
