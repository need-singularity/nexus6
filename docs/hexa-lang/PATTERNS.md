# hexa-lang 자주 쓰는 관용구 (SSOT 복붙용)

각 스니펫은 `n6/atlas_query.hexa` 또는 `mk2_hexa/mk2/src/atlas/*.hexa` 에서
검증된 형태. `_ns_now`, `_mtime_of`, `_shq` 등 핵심 헬퍼는 모듈마다 동일 SSOT.

---

## 1. ns clock — 3-stage fallback (BSD/GNU 양립)

`date +%s%N` 은 macOS BSD `date(1)` 가 미지원이라 literal `...N` 을 exit-0 로
출력. `to_int` 가 그대로 0 으로 fall-through 되면 모든 duration_ms 가 collapse.

```hexa
fn _ns_now() -> i64 {
    let mut r: i64 = 0
    let raw = to_string(exec("date +%s%N 2>/dev/null")).trim()  // @allow-bare-exec
    if raw.len() > 0 && raw.contains("N") == false {
        try { r = to_int(raw) } catch e {}  // @allow-silent-catch
    }
    if r < 1 {
        let s2 = to_string(exec("python3 -c 'import time;print(time.time_ns())' 2>/dev/null")).trim()  // @allow-bare-exec
        try { r = to_int(s2) } catch e2 {}  // @allow-silent-catch
    }
    if r < 1 {
        let s3 = to_string(exec("date +%s")).trim()  // @allow-bare-exec
        try { let sec = to_int(s3); r = sec * 1000000000 } catch e3 {}  // @allow-silent-catch
    }
    return r
}
```

출처: `n6/atlas_query.hexa:47`, 4개 atlas 모듈에서 동일 SSOT 복제.

---

## 2. mtime (BSD/GNU 양립)

```hexa
fn _mtime_of(path: string) -> i64 {
    let mut r: i64 = 0
    try {
        let raw = to_string(exec("stat -c '%Y' '" + path
            + "' 2>/dev/null || stat -f '%m' '" + path + "' 2>/dev/null")).trim()  // @allow-bare-exec
        r = to_int(raw)
    } catch e {}   // @allow-silent-catch
    return r
}
```

출처: `n6/atlas_query.hexa:68`. GNU `-c '%Y'` 우선, BSD `-f '%m'` 폴백.

---

## 3. shell-arg single-quote escape

```hexa
fn _shq(s: string) -> string {
    return s.replace("'", "'\\''")
}
```

`exec("cmd '" + _shq(user_input) + "'")` 패턴으로 사용. 출처:
`mk2_hexa/mk2/src/atlas/hypothesis.hexa:46`.

---

## 4. NDJSON meta emit (stderr)

```hexa
let mut m: [string] = []
m.push("NEXUS_<MODULE> {\"stage\":\"")
m.push(stage)
m.push("\",\"matches\":")
m.push(to_string(n))
m.push(",\"duration_us\":")
m.push(to_string(dur_us))
m.push("}")
eprintln(m.join(""))
```

키 명명: `NEXUS_<NS>_<EVENT>` (예: `NEXUS_ATLAS_QUERY`,
`NEXUS_MK2_ATLAS_DISPATCH`). 한 라인 = 1 NDJSON object.

---

## 5. 서브프로세스 hexa 호출 + exit code 회수

```hexa
let cmd = "hexa run '" + _shq(target_path) + "' " + _shq_args(args) + "; echo \"__RC=$?\""
let out = to_string(exec(cmd))                           // @allow-bare-exec
let rc_at = out.index_of("__RC=")
let mut rc: i64 = 1
if rc_at > -1 {
    let tail = out.substring(rc_at + 5, len(out)).trim()
    try { rc = to_int(tail) } catch e {}                 // @allow-silent-catch
}
let payload = if rc_at > -1 { out.substring(0, rc_at) } else { out }
```

출처: `mk2_hexa/mk2/src/atlas/mod.hexa` dispatch 패턴.

---

## 6. JSON 블록 파싱 (awk RS="    }")

`discovery/math_atlas.json` 등 4-space-indent pretty JSON 전용.

```awk
function streq(a,b){ return length(a)==length(b) && index(a,b)==1 }
BEGIN{ RS="    }" }
{
  blk=$0; id=""; grade=""; domain=""
  n=split(blk, lines, "\n")
  for(i=1;i<=n;i++){
    L=lines[i]
    if(match(L, /"id": "[^"]*"/))    { id=substr(L,RSTART+7,RLENGTH-8) }
    else if(match(L, /"grade": "[^"]*"/)) { grade=substr(L,RSTART+10,RLENGTH-11) }
  }
  if(id=="") next
  if(MODE=="grade" && streq(grade, FILT)) printf "%s\t%s\n", id, grade
}
```

출처: `mk2_hexa/mk2/src/atlas/hypothesis.hexa:57` (`_write_awk_script`).
**중요**: `==` 직접비교 금지 — `streq()` 헬퍼 (GOTCHAS.md §1) 사용.

---

## 7. hex byte 파싱 (awk lookup table)

awk 에 `strtonum` 이 없거나 BSD 호환을 위해 lookup 사용.

```awk
hx["0"]=0; hx["1"]=1; hx["2"]=2; hx["3"]=3; hx["4"]=4
hx["5"]=5; hx["6"]=6; hx["7"]=7; hx["8"]=8; hx["9"]=9
hx["a"]=10; hx["b"]=11; hx["c"]=12; hx["d"]=13; hx["e"]=14; hx["f"]=15
hx["A"]=10; hx["B"]=11; hx["C"]=12; hx["D"]=13; hx["E"]=14; hx["F"]=15
# byte = hx[substr(h,1,1)]*16 + hx[substr(h,2,1)]
```

출처: `n6/atlas_query.hexa:92-95` (atlas_bloom check awk).

---

## 8. dual-file awk (선택적 라인 추출)

`set_file` (line numbers) + `data_file` (대상) → 지정된 라인만 출력.

```awk
NR==FNR{ S[$1+1]=1; next }
(FNR in S){ print $0 }
```

호출: `awk '<src>' set_file data_file`. 출처: `n6/atlas_query.hexa:182`
(stage-3 cold mmap lookup).

---

## 9. JSON 배열 추출 (간이 — index_of 기반)

```hexa
let raw = read_file(path)
let marker = "\"" + key + "\":["
let bs = raw.index_of(marker)
if bs < 0 { return "" }
let after = raw.substring(bs + len(marker), len(raw))
let close = after.index_of("]")
if close < 0 { return "" }
return after.substring(0, close).trim()  // CSV 형태로 사용
```

출처: `n6/atlas_query.hexa:161` (`_bucket_csv`).

---

## 10. file-write awk script + invoke

awk 스크립트가 길어지면 `[string]` 빌드 → join → `write_file` → `awk -f`.

```hexa
let mut p: [string] = []
p.push("BEGIN{ ... } ")
p.push("{ ... }")
let src = p.join("")
try { write_file("/tmp/<module>.awk", src) } catch e { return false }  // @allow-silent-catch
let out = to_string(exec("awk -v MODE='" + mode + "' -f '/tmp/<module>.awk' '"
    + _shq(data_path) + "' 2>/dev/null"))                // @allow-bare-exec
```

출처: `mk2_hexa/mk2/src/atlas/hypothesis.hexa:57`, `n6/atlas_query.hexa:83`.

---

## 11. CLI dispatch boilerplate

```hexa
let a = args()
let mut cmd = "query"
if len(a) > 2 { cmd = a[2] }

if cmd == "query" {
    if len(a) < 4 { println("usage: ..."); exit(1) }   // @allow-silent-exit
    let prefix = a[3]
    // ...
    exit(0)
} else {
    println("usage: ...")
    exit(1)                                            // @allow-silent-exit
}
```

출처: `n6/atlas_query.hexa:267`.
