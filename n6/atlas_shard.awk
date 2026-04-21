# atlas.n6 → hot/cold sharding
# 사용법:
#   awk -v deg_path=shared/n6/atlas.n6.deg \
#       -v hot_path=shared/n6/atlas.n6.hot \
#       -v cold_path=shared/n6/atlas.n6.cold \
#       -v hot_thresh=50 \
#       -f shared/n6/atlas_shard.awk shared/n6/atlas.n6
#
# 분류 규칙:
#   - 비-JSON 라인 (@P/@L/@R/@C/@F/@X 헤더, indented continuation, 주석, 빈 줄)
#     → HOT (axiom-tier, 항상 우선 로드)
#   - JSON node: id의 deg ≥ hot_thresh → HOT, else COLD
#   - JSON edge: max(from_deg, to_deg) ≥ hot_thresh → HOT, else COLD
#   - 기타 JSON (event 등) → COLD
#
# 불변식: 라인 집합이 보존됨 (lossless). cat hot cold | sort == atlas.n6 | sort.
# 순서 보존: 동일 셔드 내에서는 원본 순서 보존. hot+cold concat 시 원본 순서 깨짐.
#   → 따라서 atlas.n6 자체가 SSOT, hot/cold는 query-only 사이드카.
BEGIN {
  if (hot_thresh+0 == 0) hot_thresh = 50
  while ((getline line < deg_path) > 0) {
    n = split(line, a, "\t")
    if (n>=2) deg[a[1]] = a[2]+0
  }
  close(deg_path)
}
{
  line = $0
  if (length(line)==0) { print > hot_path; next }
  c1 = substr(line,1,1)
  if (c1!="{") {
    print > hot_path; next
  }
  typev=""
  if (match(line, /"type":"[^"]+"/)) typev = substr(line, RSTART+8, RLENGTH-9)
  if (typev=="node") {
    idv=""
    if (match(line, /"id":"[^"]+"/)) idv = substr(line, RSTART+6, RLENGTH-7)
    d = deg[idv]+0
    if (d >= hot_thresh) print > hot_path
    else print > cold_path
    next
  }
  if (typev=="edge") {
    fv=""; tv=""
    if (match(line, /"from":"[^"]+"/)) fv = substr(line, RSTART+8, RLENGTH-9)
    if (match(line, /"to":"[^"]+"/)) tv = substr(line, RSTART+6, RLENGTH-7)
    df = deg[fv]+0; dt = deg[tv]+0
    maxd = (df>dt)?df:dt
    if (maxd >= hot_thresh) print > hot_path
    else print > cold_path
    next
  }
  print > cold_path
}
