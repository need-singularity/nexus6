# hetzner_prompt — AX102-U 원격 실행 가이드 (전 프로젝트 공용)

접속: ssh hetzner (root@157.180.8.154)
json: config/hetzner.json (호스트 상세)

spec:
  CPU   AMD Ryzen 9 7950X3D 16C/32T @ 4.2GHz (Zen4, 3D V-Cache)
  RAM   128GB DDR5
  Disk  98GB / + 1.6TB /home
  GPU   없음 (GPU → Ubuntu RTX5070 또는 온디맨드)
  OS    Ubuntu 24.04, Finland HEL1, 1Gbit 무제한
  tools hexa(self-host), clang, git, htop, tmux

| 프로젝트 | 경로 | 용도 |
|----------|------|------|
| anima | /home/anima/ | CPU 서빙(8080)·학습·OUROBOROS |
| nexus | /home/nexus/ | 렌즈 스캔·blowup·gap_finder·seed |
| hexa-lang | /home/hexa-lang/ | self-host 빌드(16코어)·테스트 |
| airgenome | /home/airgenome/ | 배치 분석·crosscorr CPU |
| papers/n6 | /home/papers/ | 빌드·렌더링 |

규칙: /home/ 하위 배치(1.6TB) / tmux 장기작업 / 128GB 인메모리 활용

monitor: htop / df -h / tmux ls / curl localhost:8080/health

parent: CLAUDE.md → "config"
