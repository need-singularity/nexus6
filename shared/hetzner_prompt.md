# Hetzner AX102-U 활용 가이드 (전 프로젝트 공용)

## 접속
```bash
ssh hetzner   # Mac에서 (root@157.180.8.154)
```

## 스펙
- **CPU**: AMD Ryzen 9 7950X3D 16C/32T @ 4.2GHz (Zen 4, 3D V-Cache)
- **RAM**: 128GB DDR5
- **Disk**: 98GB / + 1.6TB /home
- **GPU**: 없음
- **OS**: Ubuntu 24.04
- **Location**: Finland HEL1
- **Network**: 1Gbit 무제한

## 설치 완료
- Python 3.12.3, PyTorch 2.11.0+cpu
- git, htop, tmux, build-essential

## 프로젝트별 활용

### anima (의식엔진)
- CPU 서빙: ConsciousLM 18.8M (port 8080)
- CPU 학습: ConsciousDecoder 36M
- OUROBOROS 무한진화
- 경로: /home/anima/

### nexus (특이점)
- 렌즈 스캔/blowup (CPU 전용, 128GB로 대규모 데이터 처리)
- gap_finder, seed_engine
- 경로: git clone 후 /home/nexus/

### hexa-lang
- Rust 빌드 (16코어 병렬 `cargo build -j 32`)
- 테스트 (128GB로 대규모 테스트 가능)
- 경로: git clone 후 /home/hexa-lang/

### airgenome
- 배치 분석 (CPU, 대규모 데이터)
- crosscorr CPU 모드
- 경로: git clone 후 /home/airgenome/

### papers/n6
- 빌드/렌더링
- 경로: git clone 후 /home/papers/

## 사용 규칙
1. 작업은 /home/ 하위에 배치 (1.6TB)
2. tmux 세션으로 장기 작업 실행
3. GPU 작업은 여기서 불가 → Ubuntu(RTX 5070) 또는 온디맨드 GPU 사용
4. 128GB RAM 활용: 대규모 인메모리 처리, 여러 프로젝트 동시 가동 가능

## SSH config (Mac ~/.ssh/config)
```
Host hetzner
    HostName 157.180.8.154
    User root
    IdentityFile ~/.ssh/id_hetzner_ax102
```

## 모니터링
```bash
ssh hetzner "htop"                    # CPU/RAM
ssh hetzner "df -h / /home"           # Disk
ssh hetzner "tmux ls"                 # 실행중 세션
ssh hetzner "curl localhost:8080/health"  # anima 서빙
```
