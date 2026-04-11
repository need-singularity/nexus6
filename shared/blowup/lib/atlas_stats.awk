# atlas_stats.awk — AI-native shell uplift for graph_stats_single_pass
#
# 발생 원인: hexa의 content.split("\n") + graph_extract_field(line.split("")) 가
#   12MB atlas.n6 처리 시 ~200M small allocs → 126GB OOM (확인됨, dmesg)
#
# 본 awk 는 동등한 nodes/edges/hubs 를 ~1초/100MB 로 산출.
#
# 입력: -v min_deg=N  -v deg_path=/path/to/atlas.n6.deg  atlas.n6
# 출력: stdout = "nodes|edges|hubs"  (graph_stats_single_pass 와 동일 포맷)
# 사이드 효과: deg_path 에 "node_id\tdegree" TSV 작성 (incremental path 활성화)

BEGIN {
    n = 0
    e = 0
    h = 0
    if (min_deg == "" || min_deg+0 == 0) min_deg = 3
}

# node 카운트 (라인에 "type":"node" 가 있으면 1건)
/"type":"node"/ { n++; next }

# edge 카운트 + degree 누적
/"type":"edge"/ {
    e++
    line = $0
    # "from":"X" 추출
    fp = index(line, "\"from\":\"")
    if (fp > 0) {
        tail = substr(line, fp + 8)
        qe = index(tail, "\"")
        if (qe > 1) {
            f = substr(tail, 1, qe - 1)
            d[f]++
        }
    }
    # "to":"X" 추출
    tp = index(line, "\"to\":\"")
    if (tp > 0) {
        tail = substr(line, tp + 6)
        qe = index(tail, "\"")
        if (qe > 1) {
            t = substr(tail, 1, qe - 1)
            d[t]++
        }
    }
}

END {
    # hub_count + deg sidecar 동시 작성
    if (deg_path != "") {
        for (k in d) {
            print k "\t" d[k] > deg_path
            if (d[k] >= min_deg) h++
        }
        close(deg_path)
    } else {
        for (k in d) if (d[k] >= min_deg) h++
    }
    print n "|" e "|" h
}
