#!/bin/bash
# @hexa-first-exempt — perl alarm wrapper for macOS (no gtimeout/timeout)
# perl_timeout.sh — macOS 대응 timeout wrapper (gtimeout/timeout 없음)
# usage: perl_timeout.sh <seconds> <cmd> [args...]
#   e.g. perl_timeout.sh 45 hexa run script.hexa arg1 arg2
# exit codes:
#   124  timeout 발동 (TERM→KILL 단계)
#   *    자식 프로세스 exit code 그대로 전파
# 우회: NEXUS_NO_TIMEOUT=1 → timeout 미적용, 그대로 exec

if [ -n "$NEXUS_NO_TIMEOUT" ]; then
    shift  # drop timeout arg
    exec "$@"
fi

if [ $# -lt 2 ]; then
    echo "usage: perl_timeout.sh <seconds> <cmd> [args...]" >&2
    exit 2
fi

t="$1"
shift

exec perl -e '
    use POSIX qw(setsid WNOHANG);
    my $t = shift;
    my @c = @ARGV;
    my $pid = fork();
    if (!defined $pid) { die "fork failed: $!\n" }
    if ($pid == 0) {
        setsid();  # new process group → kill -$pid 가 자식들까지 전파
        exec { $c[0] } @c;
        die "exec failed: $!\n";
    }
    my $timed_out = 0;
    eval {
        local $SIG{ALRM} = sub {
            $timed_out = 1;
            kill("TERM", -$pid);  # negative = process group
            # 1s grace polling (SIGKILL 이전 자식 종료 기회)
            for my $i (1..10) {
                select(undef, undef, undef, 0.1);
                my $kid = waitpid($pid, WNOHANG);
                last if $kid == $pid;
            }
            kill("KILL", -$pid);
            waitpid($pid, 0);
            die "to\n";
        };
        alarm $t;
        waitpid($pid, 0);
        alarm 0;
    };
    if ($timed_out) {
        print STDERR "[perl_timeout ${t}s] killed pid=$pid cmd=@c\n";
        exit 124;
    }
    exit($? >> 8);
' "$t" "$@"
