// ═══════════════════════════════════════════════════════════
// lib/pre_tool_bash.hexa.inc — Bash PreToolUse 가드 모음
// 사용: errors.hexa.inc 패턴 — 소비자 .hexa 상단에 copy-paste.
//       (hexa stage1 native include 미지원. 본 파일은 canonical source.)
//
// 목적: pre_tool_guard.hexa 카테고리 분리 refactor (H-마커 8 혼재 해소).
// 참조 main: shared/harness/pre_tool_guard.hexa
//
// 함수 목록 (dispatch 순서):
//   check_md_to_pdf_cmd           pandoc/xelatex MD→PDF 차단          (H-MD2PDF)
//   check_external_send_cmd       gh PR/이메일/webhook 발송 차단       (H-SEND-GUARD)
//   check_blocking_cmd            read -p / wait / fg / sleep N>=10    (H-NOBLOCK)
//   check_pkill_f_cmd             pkill/pgrep -f substring 차단        (R20)
//   check_bare_interpreter_cmd    bare python3/ruby/node 차단          (R22)
//   check_no_archive_cmd          mkdir backup / cp .bak / tar.gz      (H-NOARCHIVE)
//   check_no_hook_cmd             git config core.hooksPath / claude   (H-NOHOOK)
//   check_git_destruction_cmd     git reset --hard / clean -f / stash  (H-NO-GIT-DESTRUCT)
//   check_hexa_budget             hexa 프로세스 예산 게이트            (H-NOZOMBIE)
// ═══════════════════════════════════════════════════════════

// H-MD2PDF: MD→PDF 변환은 md-to-pdf 전용. pandoc/xelatex 호출 차단.
// arg = Bash command (entry.hexa 가 argv[3] 으로 cmd 전달)
fn check_md_to_pdf_cmd(tool: str, arg: str) -> str {
    if tool != "Bash" { return "" }
    if arg.len() == 0 { return "" }
    if arg.contains("NEXUS_PDF_OK=1") { return "" }

    let has_pandoc = arg.contains("pandoc")
    let has_xelatex = arg.contains("xelatex") || arg.contains("pdflatex") || arg.contains("lualatex")
    if has_pandoc == false && has_xelatex == false { return "" }

    if has_pandoc {
        let to_pdf = arg.contains(".pdf") || arg.contains("--to=pdf") || arg.contains("-t pdf") || arg.contains("--to pdf")
        if to_pdf == false { return "" }
        return "REJECT: pandoc PDF 변환 금지 (H-MD2PDF) — `md-to-pdf <file.md>` 사용. 우회: NEXUS_PDF_OK=1 prefix"
    }

    return "REJECT: xelatex/pdflatex/lualatex 금지 (H-MD2PDF) — MD→PDF 는 `md-to-pdf` 사용. 우회: NEXUS_PDF_OK=1 prefix"
}

// H-SEND-GUARD: 외부 발송/등록 (이메일, github issue/PR, webhook) — 사용자 명시 요청 전 차단.
// 우회: NEXUS_SEND_OK=1 prefix (사용자가 직접 요청한 경우 Claude 가 명시 부여).
fn check_external_send_cmd(tool: str, arg: str) -> str {
    if tool != "Bash" { return "" }
    if arg.len() == 0 { return "" }
    if arg.contains("NEXUS_SEND_OK=1") { return "" }

    let patterns = [
        ["gh issue create", "github issue 등록"],
        ["gh issue comment", "github issue 댓글"],
        ["gh issue close", "github issue 종료"],
        ["gh issue reopen", "github issue 재오픈"],
        ["gh pr create", "github PR 생성"],
        ["gh pr comment", "github PR 댓글"],
        ["gh pr merge", "github PR 머지"],
        ["gh pr close", "github PR 종료"],
        ["gh pr review", "github PR 리뷰"],
        ["gh release create", "github release 발행"],
        ["gh gist create", "github gist 발행"],
        ["sendmail ", "이메일 발송 (sendmail)"],
        ["msmtp ", "이메일 발송 (msmtp)"],
        ["swaks ", "이메일 발송 (swaks)"],
        ["mutt -s", "이메일 발송 (mutt)"],
        ["mail -s", "이메일 발송 (mail)"],
        ["hooks.slack.com", "slack webhook"],
        ["discord.com/api/webhooks", "discord webhook"],
        ["discordapp.com/api/webhooks", "discord webhook"]
    ]
    for p in patterns {
        if arg.contains(p[0]) {
            return "REJECT: 외부 발송/등록 차단 (H-SEND-GUARD) — " + p[1] + ". 사용자 명시 요청 필요. 우회: NEXUS_SEND_OK=1 prefix"
        }
    }
    return ""
}

// H-NOBLOCK: 세션 채팅 블로킹 금지 — 사용자 입력 채널을 막는 동기 대기 명령 차단.
// 대상: read -p / read -r / wait (PID/%N) / fg / sleep N (N>=10) / while sleep ... do done
// 우회: NEXUS_BLOCK_OK=1 prefix (정당한 사유 — 예: long-poll 의도 명시).
// 구현: arg 를 임시파일로 쓰고 awk 매칭 — hexa-real char 비교/$expansion 함정 우회.
fn check_blocking_cmd(tool: str, arg: str) -> str {
    if tool != "Bash" { return "" }
    if arg.len() == 0 { return "" }
    if arg.contains("NEXUS_BLOCK_OK=1") { return "" }
    if arg.contains("@allow-block") { return "" }

    if arg.contains("read -p ") || arg.contains("read -rp ") || arg.contains("read -sp ") {
        return "REJECT: read -p/-rp/-sp 입력 대기 금지 (H-NOBLOCK) — 세션 블로킹. 우회: NEXUS_BLOCK_OK=1 prefix"
    }
    if arg.contains(" fg ") || arg.starts_with("fg ") || arg == "fg" || arg.contains(";fg") || arg.contains("&& fg") {
        return "REJECT: fg 포그라운드 복귀 금지 (H-NOBLOCK) — 세션 블로킹. 우회: NEXUS_BLOCK_OK=1"
    }
    if (arg.contains("while ") || arg.contains("until ")) && arg.contains("sleep ") && arg.contains("done") {
        return "REJECT: while/until + sleep 폴링 루프 금지 (H-NOBLOCK) — Monitor 또는 run_in_background 사용. 우회: NEXUS_BLOCK_OK=1"
    }

    // wait + sleep N>=10 → awk 로 검사 (arg 임시파일 경유, $expansion 회피)
    let tmp = "/tmp/h_noblock_arg." + to_string(exec("date +%s%N")).trim()
    let _ = exec("cat > " + tmp + " <<'NOBLOCK_EOF'\n" + arg + "\nNOBLOCK_EOF")

    let wait_hits = to_string(exec("awk '/wait[[:space:]]+(\\$|%|[0-9])/{c++} END{print c+0}' " + tmp + " 2>/dev/null")).trim()
    if wait_hits != "0" && wait_hits != "" {
        let _ = exec("rm -f " + tmp)
        return "REJECT: wait PID/%/숫자 합류 대기 금지 (H-NOBLOCK) — run_in_background + Monitor 사용. 우회: NEXUS_BLOCK_OK=1"
    }

    let sl_hits = to_string(exec("awk '/sleep[[:space:]]+([1-9][0-9]+|[1-9][0-9][0-9]+)/{c++} END{print c+0}' " + tmp + " 2>/dev/null")).trim()
    if sl_hits != "0" && sl_hits != "" {
        let _ = exec("rm -f " + tmp)
        return "REJECT: sleep N>=10s 장시간 대기 금지 (H-NOBLOCK) — ScheduleWakeup/Monitor 사용. 우회: NEXUS_BLOCK_OK=1"
    }

    let _ = exec("rm -f " + tmp)
    return ""
}

// R20: pkill/pgrep -f substring 금지 — -xf 정확매칭 또는 PID 파일 기반만 허용
// 우회: @allow-pkill-f 토큰 명시
fn check_pkill_f_cmd(tool: str, arg: str) -> str {
    if tool != "Bash" { return "" }
    if arg.len() == 0 { return "" }
    if arg.contains("@allow-pkill-f") { return "" }
    if arg.contains("-xf") { return "" }

    let has_pkill_f = arg.contains("pkill -f") || arg.contains("pgrep -f")
    if has_pkill_f == false { return "" }
    return "REJECT: pkill/pgrep -f substring 금지 (R20) — 무고한 프로세스 silent kill 위험. -xf 정확매칭 / PID 파일 / pgrep -x <basename> 사용. 우회: @allow-pkill-f 주석"
}

// R22: 스크립트 인터프리터 절대경로 강제 — bare python3/ruby/node 금지
// 우회: NEXUS_INTERP_OK=1 prefix (일회성 ad-hoc)
fn check_bare_interpreter_cmd(tool: str, arg: str) -> str {
    if tool != "Bash" { return "" }
    if arg.len() == 0 { return "" }
    if arg.contains("NEXUS_INTERP_OK=1") { return "" }

    let patterns = [
        ["python3 ", "python3 (R22) — /usr/bin/python3 절대경로 필수 (hetzner 라우팅 회피)"],
        ["ruby ", "ruby (R22) — 절대경로 필수"],
        ["node ", "node (R22) — 절대경로 필수"]
    ]
    for p in patterns {
        let idx = arg.index_of(p[0])
        if idx < 0 { continue }
        if idx > 0 {
            let prev = arg.substring(idx - 1, idx)
            if prev == "/" { continue }
            if prev == "=" { continue }
        }
        return "REJECT: bare interpreter 호출 금지 — " + p[1] + ". 우회: NEXUS_INTERP_OK=1 prefix"
    }
    return ""
}

// H-NOARCHIVE Bash: mkdir archive/backup, cp/mv/rsync to .bak/.backup/.old, tar.gz 백업 생성 차단.
fn check_no_archive_cmd(tool: str, arg: str) -> str {
    if tool != "Bash" { return "" }
    if arg.len() == 0 { return "" }
    if arg.contains("NEXUS_ARCHIVE_OK=1") { return "" }
    if arg.contains("@allow-archive") { return "" }

    // 격리 공간 안에서의 작업은 통과
    let in_safe_zone = arg.contains("shared/backups/") || arg.contains("shared/archive/") || arg.contains("shared/discovery/archive/") || arg.contains("archive/deprecated_json/")

    let mkdir_patterns = [
        "mkdir backup", "mkdir backups", "mkdir archive", "mkdir archives",
        "mkdir -p backup", "mkdir -p backups", "mkdir -p archive", "mkdir -p archives",
        "mkdir .backup", "mkdir .archive", "mkdir _backup", "mkdir _archive"
    ]
    if in_safe_zone { return "" }

    for p in mkdir_patterns {
        if arg.contains(p) {
            return "REJECT: '" + p + "' 신규 폴더 생성 금지 (H-NOARCHIVE). archive 는 git commit/branch/tag 로. 격리 예외: shared/backups/, shared/archive/. 우회: NEXUS_ARCHIVE_OK=1"
        }
    }

    let starts_cp_mv = arg.contains("cp ") || arg.contains("mv ") || arg.contains("rsync ")
    if starts_cp_mv {
        let sfx_patterns = [".bak ", ".bak'", ".bak\"", ".backup ", ".backup'", ".backup\"", ".old ", ".old'", ".old\"", ".orig ", ".orig'", ".orig\""]
        for s in sfx_patterns {
            if arg.contains(s) {
                return "REJECT: cp/mv/rsync → '*" + s.trim() + "' 백업 사본 금지 (H-NOARCHIVE). git stash/commit 으로 보존. 우회: NEXUS_ARCHIVE_OK=1"
            }
        }
        let end_patterns = [".bak", ".backup", ".old", ".orig"]
        for s in end_patterns {
            if arg.ends_with(s) {
                return "REJECT: cp/mv/rsync → '*" + s + "' 백업 사본 금지 (H-NOARCHIVE). git stash/commit 으로 보존. 우회: NEXUS_ARCHIVE_OK=1"
            }
        }
    }

    let tar_patterns = ["backup.tar", "backup.tgz", "backup.zip", "_backup.tar", "_backup.zip", "archive.tar", "archive.tgz", "archive.zip"]
    for t in tar_patterns {
        if arg.contains(t) {
            return "REJECT: '" + t + "' 백업 아카이브 생성 금지 (H-NOARCHIVE). git bundle/tag 사용. 우회: NEXUS_ARCHIVE_OK=1"
        }
    }

    return ""
}

// H-NOHOOK Bash: git config core.hooksPath 변경 / chmod +x 새 hook 활성화 / 새 .git/hooks 파일 생성 차단.
fn check_no_hook_cmd(tool: str, arg: str) -> str {
    if tool != "Bash" { return "" }
    if arg.len() == 0 { return "" }
    if arg.contains("NEXUS_HOOK_OK=1") { return "" }
    if arg.contains("@allow-hook") { return "" }

    if arg.contains("git config core.hooksPath") || arg.contains("git config --global core.hooksPath") {
        return "REJECT: git config core.hooksPath 변경 금지 (H-NOHOOK) — H-COMMIT .githooks/ 가 SSOT. 우회: NEXUS_HOOK_OK=1"
    }
    if arg.contains("claude hooks add") || arg.contains("claude config hooks") {
        return "REJECT: claude hooks add 금지 (H-NOHOOK) — settings.json hooks={} SSOT. harness/entry.hexa 자율 호출로 대체. 우회: NEXUS_HOOK_OK=1"
    }
    return ""
}

// H-NO-GIT-DESTRUCT: 비가역 git 명령 차단 (2026-04-17 audit-agent 사건 후 도입).
// Why: read-only audit 에이전트가 `git stash + reset` 으로 untracked .hexa 8개 영구 소실.
//      stash 는 --include-untracked 없으면 untracked 보존 안 함 → reset 시 통째로 사라짐.
//      git fsck dangling blob 으로 7개 복구했으나 1개 영구 소실, 동일 사고 재발 방지 필수.
// 차단:
//   1. git reset --hard            (worktree+index 무조건 파괴)
//   2. git clean -f / -fd / -fdx   (untracked 파일 무조건 파괴)
//   3. git checkout . / -- .       (worktree 변경 무조건 파괴)
//   4. git checkout --force        (worktree 변경 + branch 강제 전환)
//   5. git restore . / --worktree . (worktree 변경 무조건 파괴)
//   6. git switch -f / --discard-changes (worktree 변경 파괴)
//   7. git branch -D <name>        (unmerged branch 강제 삭제)
//   8. git stash drop / clear      (stash 무조건 파괴)
//   9. git stash (push) without -u WHEN untracked files exist  ← 본 사건 원인
//  10. git update-ref -d           (ref 무조건 삭제)
// 우회: NEXUS_GIT_OK=1 prefix 또는 cmd 내 @allow-git-destruct 토큰.
fn check_git_destruction_cmd(tool: str, arg: str) -> str {
    if tool != "Bash" { return "" }
    if arg.len() == 0 { return "" }
    if arg.contains("NEXUS_GIT_OK=1") { return "" }
    if arg.contains("@allow-git-destruct") { return "" }
    if arg.contains("git ") == false { return "" }

    // 1. reset --hard
    if arg.contains("git reset --hard") || arg.contains("git reset -h ") {
        return "REJECT: git reset --hard 차단 (H-NO-GIT-DESTRUCT) — worktree+index 무조건 파괴. 안전대안: git reset --soft / --mixed (기본) / git revert. 우회: NEXUS_GIT_OK=1 prefix"
    }

    // 2. clean -f / -fd / -fdx / -fx (실제 삭제는 -f 필수)
    if arg.contains("git clean -f") || arg.contains("git clean --force") || arg.contains("git clean -df") || arg.contains("git clean -dfx") {
        return "REJECT: git clean -f 차단 (H-NO-GIT-DESTRUCT) — untracked 파일 무조건 삭제 (본 사건 원인 클래스). 안전대안: git clean -n (dry-run 먼저). 우회: NEXUS_GIT_OK=1 prefix"
    }

    // 3-4. checkout 파괴 패턴 — git checkout . / git checkout -- . / git checkout --force / -f
    if arg.contains("git checkout .") || arg.contains("git checkout -- .") {
        return "REJECT: git checkout . 차단 (H-NO-GIT-DESTRUCT) — worktree 변경 무조건 파괴. 안전대안: git stash --include-untracked 후 작업, git restore --source=HEAD <file>. 우회: NEXUS_GIT_OK=1 prefix"
    }
    if arg.contains("git checkout --force") || arg.contains("git checkout -f ") {
        return "REJECT: git checkout --force/-f 차단 (H-NO-GIT-DESTRUCT) — worktree 강제 폐기 + branch 전환. 우회: NEXUS_GIT_OK=1 prefix"
    }

    // 5. restore . / restore --worktree .
    if arg.contains("git restore .") || arg.contains("git restore --worktree .") || arg.contains("git restore --staged --worktree .") {
        return "REJECT: git restore . 차단 (H-NO-GIT-DESTRUCT) — worktree 변경 무조건 파괴. 안전대안: 파일별 git restore <file>. 우회: NEXUS_GIT_OK=1 prefix"
    }

    // 6. switch -f / --discard-changes
    if arg.contains("git switch -f ") || arg.contains("git switch --force ") || arg.contains("git switch --discard-changes") {
        return "REJECT: git switch --force/-f 차단 (H-NO-GIT-DESTRUCT) — worktree 변경 파괴. 안전대안: git stash --include-untracked 선행. 우회: NEXUS_GIT_OK=1 prefix"
    }

    // 7. branch -D (대문자만 차단, -d 는 merged 만 삭제하므로 안전)
    if arg.contains("git branch -D ") || arg.contains("git branch --delete --force") || arg.contains("git branch -Df ") || arg.contains("git branch -fD ") {
        return "REJECT: git branch -D 차단 (H-NO-GIT-DESTRUCT) — unmerged branch 강제 삭제 (커밋 영구 손실 가능). 안전대안: git branch -d (merged 만), git branch -m <new> 로 rename. 우회: NEXUS_GIT_OK=1 prefix"
    }

    // 8. stash drop / clear
    if arg.contains("git stash drop") || arg.contains("git stash clear") {
        return "REJECT: git stash drop/clear 차단 (H-NO-GIT-DESTRUCT) — stash 무조건 폐기. 안전대안: git stash branch <name> 로 별도 브랜치 보존. 우회: NEXUS_GIT_OK=1 prefix"
    }

    // 10. update-ref -d
    if arg.contains("git update-ref -d ") || arg.contains("git update-ref --no-deref -d") {
        return "REJECT: git update-ref -d 차단 (H-NO-GIT-DESTRUCT) — ref 무조건 삭제. 우회: NEXUS_GIT_OK=1 prefix"
    }

    // 9. stash (push) 본 사건 원인 — untracked 가 존재할 때만 차단.
    //    매칭: `git stash` 단독 / `git stash save ...` / `git stash push ...`
    //    면제: `-u`, `--include-untracked`, `-a`, `--all`, pop/apply/list/show/drop/clear/branch/create/store
    let stash_idx = arg.index_of("git stash")
    if stash_idx >= 0 {
        // tail = "git stash" 이후 부분
        let tail = arg.substring(stash_idx + 9, arg.len())
        let is_subcmd = tail.starts_with(" pop") || tail.starts_with(" apply") || tail.starts_with(" list") ||
                        tail.starts_with(" show") || tail.starts_with(" drop") || tail.starts_with(" clear") ||
                        tail.starts_with(" branch") || tail.starts_with(" create") || tail.starts_with(" store")
        if is_subcmd == false {
            // push variant — -u/-a/--include-untracked 면제
            let has_u = tail.contains(" -u") || tail.contains(" --include-untracked") ||
                        tail.contains(" -a") || tail.contains(" --all")
            if has_u == false {
                // untracked 실제 존재 검사 (없으면 통과 — 무해한 stash)
                let untracked_count = to_string(exec("git status --porcelain 2>/dev/null | grep -c '^??' || echo 0")).trim()  // @allow-bare-exec
                if untracked_count != "0" && untracked_count != "" {
                    return "REJECT: git stash without -u 차단 (H-NO-GIT-DESTRUCT, 2026-04-17 사건) — untracked " + untracked_count + "개 존재 시 stash 보존 안 됨, 후속 reset/checkout 으로 영구 소실 위험. 안전대안: git stash --include-untracked 또는 git add 선행. 우회: NEXUS_GIT_OK=1 prefix"
                }
            }
        }
    }

    return ""
}

// H-NOZOMBIE: hexa 프로세스 예산 게이트 — 동시 활성 hexa N개 초과 시 BLOCK.
// Why: nexus 에서 .hexa 프로세스가 30+ 누적 → Mac load 220 사고. 사후 청소 외 사전 차단 필수.
// 우회: NEXUS_BUDGET_OK=1 prefix 또는 cmd 내 @allow-many-hexa 토큰.
// host 별 임계치: mac=8, hetzner/ubu/vast=32, 기타=12 (CPU 코어 기준 추정).
fn check_hexa_budget(tool: str, arg: str) -> str {
    if tool != "Bash" { return "" }
    if arg.len() == 0 { return "" }
    if arg.contains("NEXUS_BUDGET_OK=1") { return "" }
    if arg.contains("@allow-many-hexa") { return "" }
    if arg.contains("hexa") == false { return "" }

    let host = to_string(exec("hostname -s 2>/dev/null || echo unknown")).trim()
    let mut budget = 12
    if host == "Mac" || host == "mac" { budget = 8 }
    else if host.contains("hetzner") || host.contains("ubu") || host.contains("vast") { budget = 32 }

    let count_str = to_string(exec(
        "ps -axo command 2>/dev/null | " +
        "awk '/\\/hexa[[:space:]]run|hexa\\.real/ && !/awk/ && !/\\/bin\\/zsh/ && !/pre_tool_guard\\.hexa/{n++} END{print n+0}'"
    )).trim()
    let count = to_int(count_str)
    if count < budget { return "" }

    return "REJECT: hexa 프로세스 예산 초과 (활성=" + count_str + "/임계=" + to_string(budget) +
           " host=" + host + ") H-NOZOMBIE — 잠시 후 재시도. 우회: NEXUS_BUDGET_OK=1 prefix 또는 @allow-many-hexa 주석"
}
