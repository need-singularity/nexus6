# NEXUS-6 완전 자율 모드 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** nexus6가 동기화, 성장, 미러볼 스캔, 진화를 무인으로 반복 실행하는 완전 자율 데몬 모드 구현

**Architecture:** `nexus6 daemon` CLI 커맨드를 추가하여 기존 `loop` 명령을 무한 반복 + 적응 간격 + 시그널 핸들링으로 감싼다. Loop 자체는 기존 6단계에서 8단계로 확장 (mirror_scan + growth_bridge 추가). LaunchAgent plist를 daemon 모드로 전환하여 macOS 부팅 시 자동 시작.

**Tech Stack:** Rust (runner.rs, parser.rs), macOS launchd (plist), bash (growth_bridge.sh)

---

## 파일 구조

| 파일 | 역할 | 변경 |
|------|------|------|
| `src/cli/parser.rs` | CLI 파싱 | Daemon 커맨드 추가 |
| `src/cli/runner.rs` | CLI 실행 | run_daemon() 추가, run_loop() 8단계 확장 |
| `~/Library/LaunchAgents/com.n6.sync.nexus6.plist` | macOS 데몬 | daemon 모드로 변경 |
| `scripts/nexus6-daemon.sh` | 데몬 래퍼 스크립트 | 신규 생성 |

---

### Task 1: Loop 8단계 확장 (mirror_scan + growth_bridge)

**Files:**
- Modify: `src/cli/runner.rs:1301-1541` — run_loop()

**상태:** ✅ Phase 4 mirror_scan 이미 구현 완료 (빌드 클린)

- [x] **Step 1: Phase 4 mirror_scan 추가**
  - Telescope::mirror_universe() 호출 (최대 20렌즈)
  - 결과: harmony, eigenvalue, top_pairs 수집
  - discover_combinations() 호출

- [ ] **Step 2: Phase 5.5 growth_bridge 추가**

Phase 5 (Bridge Sync) 이후, Phase 6 (Bridge Evolve) 이전에 growth_bridge 단계 삽입:

```rust
// Phase 5.5: Growth Bridge (프로젝트 간 성장 라우팅)
let pt = Instant::now();
println!("  [5.5/8] 🌿 Growth Bridge");
{
    let nexus_root = std::env::var("NEXUS6_ROOT")
        .unwrap_or_else(|_| std::env::current_exe().ok()
            .and_then(|p| p.parent().map(|d| d.to_path_buf()))
            .and_then(|p| p.parent().map(|d| d.to_string_lossy().to_string()))
            .unwrap_or_else(|| ".".to_string()));
    let script = format!("{}/scripts/growth_bridge.sh", nexus_root);
    if std::path::Path::new(&script).exists() {
        let status = std::process::Command::new("bash")
            .arg(&script)
            .arg("full")
            .status();
        match status {
            Ok(s) if s.success() => println!("    ✅ growth_bridge 완료"),
            Ok(s) => println!("    ⚠️ growth_bridge exit {:?}", s.code()),
            Err(e) => println!("    ⚠️ growth_bridge 실행 실패: {}", e),
        }
    } else {
        println!("    ⚠️ growth_bridge.sh 없음 — 스킵");
    }
}
phase_times.push(("GrowthBridge".to_string(), pt.elapsed().as_secs_f64()));
```

총 단계: 0→7 (8단계):
- 0: Bridge update + 부하 체크
- 1: Discover + Connect
- 2: Scan
- 3: Auto (evolve + forge)
- 4: Mirror Scan (거울 우주)
- 5: Bridge Sync
- 5.5: Growth Bridge
- 6: Bridge Evolve
- 7: Commit + Push

- [ ] **Step 3: 리포트에 growth_bridge 결과 추가**

mirror 정보 아래에 growth_bridge 실행 결과 표시.

- [ ] **Step 4: 빌드 확인**

Run: `cargo check --bin nexus6 2>&1 | grep "^error"`
Expected: 에러 없음

- [ ] **Step 5: 루프 테스트**

Run: `NEXUS6_ROOT=/Users/ghost/Dev/nexus6 nexus6 loop --cycles 1 2>&1 | head -30`
Expected: [0/8] ~ [7/8] 모든 단계 출력

- [ ] **Step 6: Commit**

```bash
git add src/cli/runner.rs
git commit -m "feat(loop): 8단계 확장 — mirror_scan + growth_bridge 통합"
```

---

### Task 2: Daemon 커맨드 추가 (parser.rs)

**Files:**
- Modify: `src/cli/parser.rs:5-93` — CliCommand enum
- Modify: `src/cli/parser.rs:127-150` — parse_args match

- [ ] **Step 1: CliCommand에 Daemon variant 추가**

```rust
// parser.rs CliCommand enum에 추가:
Daemon {
    domain: Option<String>,
    interval_min: u64,   // 대기 간격 (분, 기본 30)
    max_loops: Option<usize>,  // None = 무한
},
```

- [ ] **Step 2: parse_daemon 함수 작성**

```rust
fn parse_daemon(args: &[String]) -> Result<CliCommand, String> {
    let mut domain: Option<String> = None;
    let mut interval_min: u64 = 30;
    let mut max_loops: Option<usize> = None;

    let mut i = 0;
    while i < args.len() {
        match args[i].as_str() {
            "--interval" | "-i" => {
                i += 1;
                if i >= args.len() {
                    return Err("--interval requires minutes".to_string());
                }
                interval_min = args[i].parse().map_err(|_| "interval must be a number".to_string())?;
            }
            "--max-loops" | "-n" => {
                i += 1;
                if i >= args.len() {
                    return Err("--max-loops requires a number".to_string());
                }
                max_loops = Some(args[i].parse().map_err(|_| "max-loops must be a number".to_string())?);
            }
            other if !other.starts_with('-') && domain.is_none() => {
                domain = Some(other.to_string());
            }
            other => {
                return Err(format!("daemon: unknown option '{}'", other));
            }
        }
        i += 1;
    }

    Ok(CliCommand::Daemon { domain, interval_min, max_loops })
}
```

- [ ] **Step 3: parse_args match에 "daemon" 분기 추가**

```rust
"daemon" => parse_daemon(rest),
```

- [ ] **Step 4: 빌드 확인**

Run: `cargo check --bin nexus6 2>&1 | grep "^error"`
Expected: exhaustive match 에러 (runner.rs에서 Daemon 처리 안 함)

- [ ] **Step 5: Commit**

```bash
git add src/cli/parser.rs
git commit -m "feat(cli): Daemon 커맨드 파서 추가"
```

---

### Task 3: Daemon 실행 로직 구현 (runner.rs)

**Files:**
- Modify: `src/cli/runner.rs:23-68` — run() match 분기
- Modify: `src/cli/runner.rs` — run_daemon() 함수 추가

- [ ] **Step 1: run() match에 Daemon 분기 추가**

```rust
CliCommand::Daemon { domain, interval_min, max_loops } => {
    run_daemon(domain, interval_min, max_loops)
}
```

- [ ] **Step 2: run_daemon() 구현**

`run_loop()` 바로 위에 추가:

```rust
fn run_daemon(domain: Option<String>, interval_min: u64, max_loops: Option<usize>) -> Result<(), String> {
    use std::sync::atomic::{AtomicBool, Ordering};
    use std::sync::Arc;

    let running = Arc::new(AtomicBool::new(true));
    let r = running.clone();

    // SIGTERM/SIGINT 핸들링 (graceful shutdown)
    ctrlc_handler(r);

    let domain_str = domain.as_deref().unwrap_or("number_theory").to_string();
    let interval = std::time::Duration::from_secs(interval_min * 60);

    println!("🤖 NEXUS-6 Daemon 시작");
    println!("   도메인: {} | 간격: {}분 | 최대: {}",
        domain_str, interval_min,
        max_loops.map(|n| format!("{}회", n)).unwrap_or("∞".to_string()));
    println!("   종료: Ctrl+C 또는 SIGTERM");
    println!();

    let mut loop_count = 0usize;

    while running.load(Ordering::Relaxed) {
        if let Some(max) = max_loops {
            if loop_count >= max {
                println!("✅ {}회 완료 — 데몬 종료", max);
                break;
            }
        }

        loop_count += 1;
        let now = chrono_now();
        println!("━━━ Daemon Loop #{} — {} ━━━", loop_count, now);

        // run_loop 1 cycle
        if let Err(e) = run_loop(Some(domain_str.clone()), 1) {
            println!("⚠️ Loop 에러: {} — {}분 후 재시도", e, interval_min);
        }

        // 리포트를 ~/.nexus6/last_daemon_status.txt에도 저장
        let status_line = format!(
            "loop={} time={} next={}min domain={}",
            loop_count, now, interval_min, domain_str
        );
        let status_path = std::env::var("HOME")
            .map(|h| format!("{}/.nexus6/last_daemon_status.txt", h))
            .unwrap_or_else(|_| "/tmp/nexus6_daemon_status.txt".to_string());
        let _ = std::fs::write(&status_path, &status_line);

        // 대기 (1초 단위로 체크하여 시그널에 빠르게 반응)
        if !max_loops.map(|m| loop_count >= m).unwrap_or(false) {
            println!("💤 {}분 대기...", interval_min);
            let mut waited = 0u64;
            while waited < interval_min * 60 && running.load(Ordering::Relaxed) {
                std::thread::sleep(std::time::Duration::from_secs(1));
                waited += 1;
            }
        }
    }

    println!("🛑 NEXUS-6 Daemon 종료 (총 {}회 루프)", loop_count);
    Ok(())
}

/// 시그널 핸들링: SIGTERM/SIGINT에서 graceful shutdown
fn ctrlc_handler(running: Arc<std::sync::atomic::AtomicBool>) {
    let _ = std::thread::spawn(move || {
        // Unix SIGTERM 핸들링
        #[cfg(unix)]
        {
            use std::sync::atomic::Ordering;
            let mut signals = Vec::new();
            // SIGTERM
            if let Ok(mut sig) = signal_hook::iterator::Signals::new(&[15]) {
                // 이 크레이트가 없으면 fallback으로 간단한 방식 사용
            }
        }
    });

    // Ctrl+C 핸들링 — ctrlc 크레이트 없이 순수 구현
    // 대신 running 플래그를 1초마다 체크하는 방식으로 대체
    // (run_daemon의 sleep 루프에서 이미 구현됨)
}
```

**참고:** ctrlc/signal_hook 크레이트 없이 구현. Cargo.toml 변경 불필요.
대신 더 단순한 방식으로:

```rust
fn run_daemon(domain: Option<String>, interval_min: u64, max_loops: Option<usize>) -> Result<(), String> {
    use std::sync::atomic::{AtomicBool, Ordering};

    // 글로벌 플래그 (static)
    static RUNNING: AtomicBool = AtomicBool::new(true);

    // SIGTERM/SIGINT는 프로세스 종료 → launchd가 재시작 결정
    // daemon이 loop 도중 죽어도 안전 (각 cycle은 독립적)

    let domain_str = domain.as_deref().unwrap_or("number_theory").to_string();

    println!("🤖 NEXUS-6 Daemon 시작");
    println!("   도메인: {} | 간격: {}분 | 최대: {}",
        domain_str, interval_min,
        max_loops.map(|n| format!("{}회", n)).unwrap_or("∞".to_string()));
    println!();

    let mut loop_count = 0usize;

    loop {
        if let Some(max) = max_loops {
            if loop_count >= max {
                println!("✅ {}회 완료 — 데몬 종료", max);
                break;
            }
        }

        loop_count += 1;
        println!("━━━ Daemon #{} — {} ━━━", loop_count, chrono_now());

        if let Err(e) = run_loop(Some(domain_str.clone()), 1) {
            println!("⚠️ Loop 에러: {} — {}분 후 재시도", e, interval_min);
        }

        // 데몬 상태 저장
        let status = format!("loop={}\ntime={}\nnext={}min\ndomain={}\n",
            loop_count, chrono_now(), interval_min, domain_str);
        let path = std::env::var("HOME")
            .map(|h| format!("{}/.nexus6/daemon_status.txt", h))
            .unwrap_or_else(|_| "/tmp/nexus6_daemon_status.txt".to_string());
        let _ = std::fs::create_dir_all(std::path::Path::new(&path).parent().unwrap());
        let _ = std::fs::write(&path, &status);

        if max_loops.map(|m| loop_count >= m).unwrap_or(false) { break; }

        println!("💤 {}분 대기...\n", interval_min);
        std::thread::sleep(std::time::Duration::from_secs(interval_min * 60));
    }

    println!("🛑 Daemon 종료 (총 {}회)", loop_count);
    Ok(())
}
```

- [ ] **Step 3: Help 텍스트에 daemon 추가**

```rust
println!("  daemon [domain] [--interval MIN] [--max-loops N]");
println!("      Autonomous growth daemon. Runs loop repeatedly.");
println!("      Default: 30min interval, infinite loops.");
```

- [ ] **Step 4: 빌드 확인**

Run: `cargo check --bin nexus6 2>&1 | grep "^error"`
Expected: 에러 없음

- [ ] **Step 5: 테스트 (2회 제한)**

Run: `NEXUS6_ROOT=/Users/ghost/Dev/nexus6 nexus6 daemon --max-loops 1 --interval 0`
Expected: 1회 루프 실행 후 종료

- [ ] **Step 6: Commit**

```bash
git add src/cli/runner.rs
git commit -m "feat(daemon): 무한 자율 루프 데몬 모드 구현"
```

---

### Task 4: 데몬 래퍼 스크립트

**Files:**
- Create: `scripts/nexus6-daemon.sh`

- [ ] **Step 1: 래퍼 스크립트 작성**

```bash
#!/usr/bin/env bash
# nexus6-daemon.sh — LaunchAgent에서 호출하는 데몬 래퍼
set -euo pipefail

export NEXUS6_ROOT="/Users/ghost/Dev/nexus6"
export PATH="$HOME/.cargo/bin:$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin"
export HOME="${HOME:-/Users/ghost}"

LOG_DIR="$HOME/Library/Logs/nexus6"
mkdir -p "$LOG_DIR"

BINARY="$NEXUS6_ROOT/target/release/nexus6"

# release 빌드가 없으면 debug 사용
if [ ! -f "$BINARY" ]; then
    BINARY="$NEXUS6_ROOT/target/debug/nexus6"
fi

if [ ! -f "$BINARY" ]; then
    echo "$(date): nexus6 바이너리 없음 — cargo build 필요" >> "$LOG_DIR/daemon.log"
    exit 1
fi

exec "$BINARY" daemon --interval 30 "$@" >> "$LOG_DIR/daemon.log" 2>&1
```

- [ ] **Step 2: 실행 권한 부여**

```bash
chmod +x scripts/nexus6-daemon.sh
```

- [ ] **Step 3: Commit**

```bash
git add scripts/nexus6-daemon.sh
git commit -m "feat: daemon 래퍼 스크립트 추가"
```

---

### Task 5: LaunchAgent plist 업데이트

**Files:**
- Modify: `~/Library/LaunchAgents/com.n6.sync.nexus6.plist`

- [ ] **Step 1: 기존 plist 백업**

```bash
cp ~/Library/LaunchAgents/com.n6.sync.nexus6.plist \
   ~/Library/LaunchAgents/com.n6.sync.nexus6.plist.bak
```

- [ ] **Step 2: plist를 daemon 모드로 변경**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.n6.sync.nexus6</string>

    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>/Users/ghost/Dev/nexus6/scripts/nexus6-daemon.sh</string>
    </array>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
    </dict>

    <key>ThrottleInterval</key>
    <integer>300</integer>

    <key>StandardOutPath</key>
    <string>/Users/ghost/Library/Logs/nexus6/daemon.log</string>

    <key>StandardErrorPath</key>
    <string>/Users/ghost/Library/Logs/nexus6/daemon.err</string>

    <key>EnvironmentVariables</key>
    <dict>
        <key>HOME</key>
        <string>/Users/ghost</string>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/Users/ghost/.cargo/bin:/Users/ghost/.local/bin</string>
        <key>NEXUS6_ROOT</key>
        <string>/Users/ghost/Dev/nexus6</string>
    </dict>
</dict>
</plist>
```

핵심 변경:
- `StartInterval: 3600` 삭제 → daemon 자체가 30분 간격 관리
- `KeepAlive.SuccessfulExit: false` → 비정상 종료 시 자동 재시작
- `ThrottleInterval: 300` → 크래시 시 5분 대기 후 재시작
- ProgramArguments → nexus6-daemon.sh

- [ ] **Step 3: LaunchAgent 재로드**

```bash
launchctl unload ~/Library/LaunchAgents/com.n6.sync.nexus6.plist 2>/dev/null
launchctl load ~/Library/LaunchAgents/com.n6.sync.nexus6.plist
```

- [ ] **Step 4: 데몬 상태 확인**

```bash
launchctl list | grep n6
cat ~/Library/Logs/nexus6/daemon.log | tail -5
cat ~/.nexus6/daemon_status.txt
```

- [ ] **Step 5: Commit**

```bash
git add scripts/nexus6-daemon.sh
git commit -m "feat(daemon): LaunchAgent를 자율 데몬 모드로 전환"
```

---

### Task 6: growth_service.sh 업데이트

**Files:**
- Modify: `scripts/growth_service.sh`

- [ ] **Step 1: daemon 관리 커맨드로 업데이트**

start/stop/status/logs를 daemon 모드에 맞게 수정:

```bash
PLIST="$HOME/Library/LaunchAgents/com.n6.sync.nexus6.plist"
LABEL="com.n6.sync.nexus6"
LOG_FILE="$HOME/Library/Logs/nexus6/daemon.log"
STATUS_FILE="$HOME/.nexus6/daemon_status.txt"

case "${1:-status}" in
    start)
        launchctl load "$PLIST" 2>/dev/null
        echo "✅ Daemon 시작"
        ;;
    stop)
        launchctl unload "$PLIST" 2>/dev/null
        echo "🛑 Daemon 중지"
        ;;
    status)
        if launchctl list | grep -q "$LABEL"; then
            echo "✅ Daemon 실행 중"
            [ -f "$STATUS_FILE" ] && cat "$STATUS_FILE"
        else
            echo "⏸️  Daemon 중지됨"
        fi
        ;;
    logs)
        tail -f "$LOG_FILE"
        ;;
    *)
        echo "Usage: $0 [start|stop|status|logs]"
        ;;
esac
```

- [ ] **Step 2: Commit**

```bash
git add scripts/growth_service.sh
git commit -m "fix(service): growth_service를 daemon 모드로 업데이트"
```

---

## 검증 체크리스트

- [ ] `cargo check --bin nexus6` — 에러 없음
- [ ] `nexus6 loop --cycles 1` — 8단계 모두 실행, mirror_scan 포함
- [ ] `nexus6 daemon --max-loops 1 --interval 0` — 1회 실행 후 종료
- [ ] `nexus6 daemon --max-loops 2 --interval 1` — 2회 실행, 1분 대기, 종료
- [ ] `launchctl list | grep n6` — daemon 등록 확인
- [ ] `cat ~/.nexus6/daemon_status.txt` — 상태 파일 확인
- [ ] `cat ~/.nexus6/last_loop_report.txt` — 리포트 파일 확인
