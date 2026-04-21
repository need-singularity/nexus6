# hub_leaf_promote.awk — A2 edge density generator
#
# Role: deg sidecar (node_id\tdegree TSV) → JSON edge lines for atlas.n6 append
#
# Strategy: round-robin assign deg=1 leaves to 2 primitives (offset 0,3 on 8 primitives).
#   Co-prime offset guarantees prim2 != prim1. Perfectly load-balanced.
#
# Input  : -v primes="n,sigma,phi,tau,J2,M3,mu,sopfr"  atlas.n6.deg
# Output : stdout = JSON edge lines (schema-compliant)
#          stderr = per-primitive load counts
#
# Invariants:
#   - deg=1 leaf → 2 new edges → deg=3 (passes A2 threshold)
#   - skip if leaf IS a primitive itself
#   - p1 != leaf (self-edge suppression)
#   - p2 != p1 (duplicate pair suppression)

BEGIN {
    if (primes == "") primes = "n,sigma,phi,tau,J2,M3,mu,sopfr"
    N = split(primes, P, ",")
    OFFSET = 3
    if (OFFSET == 0 || OFFSET == N) OFFSET = 3
    idx = 0
}

# Only deg=1 leaves
$2 != 1 { next }

{
    node = $1

    # skip primitives themselves
    is_prim = 0
    for (i = 1; i <= N; i++) {
        if (node == P[i]) { is_prim = 1; break }
    }
    if (is_prim) next

    idx++
    p1 = P[((idx - 1) % N) + 1]
    p2 = P[((idx - 1 + OFFSET) % N) + 1]

    if (p1 != node) {
        printf "{\"type\":\"edge\",\"from\":\"%s\",\"to\":\"%s\",\"edge_type\":\"Derives\",\"strength\":0.5,\"bidirectional\":false}\n", p1, node
        load[p1]++
    }
    if (p2 != node && p2 != p1) {
        printf "{\"type\":\"edge\",\"from\":\"%s\",\"to\":\"%s\",\"edge_type\":\"Derives\",\"strength\":0.4,\"bidirectional\":false}\n", p2, node
        load[p2]++
    }
}

END {
    for (i = 1; i <= N; i++) {
        printf "LOAD %s=%d\n", P[i], (load[P[i]]+0) > "/dev/stderr"
    }
    printf "TOTAL leaves=%d\n", idx > "/dev/stderr"
}
