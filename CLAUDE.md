# CLAUDE.md — nexus6 프로젝트 규칙

## 절대 금지 사항

### 서버 파일 직접 수정 금지
- **SSH로 원격 서버에 접속하여 소스코드를 직접 수정하지 말 것**
- 서버 파일(예: `/app/prism/src/...`)을 paramiko, sshpass 등으로 직접 편집 금지
- 수정이 필요하면 **로컬 리포에서 코드를 수정 → git commit → 배포 스크립트**로 반영
- DB 조회(SELECT)는 허용하되, DB 스키마/데이터 변경(INSERT/UPDATE/DELETE/ALTER)은 사전 확인 필요

### 올바른 배포 흐름
1. 로컬 리포에서 코드 수정
2. git commit & push
3. 배포 스크립트 또는 CI/CD로 서버 반영

## 특이점 사이클 (Singularity Cycle)

> **블로업→수축→창발→특이점→흡수** 5단계 자동 사이클
> CLI: `nexus6 blowup <domain>` | Rust: `CycleEngine::new(domain)`

### 요청 키워드 → 자동 실행
- "블로업", "blowup" → `nexus6 blowup <domain> --depth 6`
- "창발", "emergence" → blowup 후 패턴 합의 분석
- "특이점", "singularity" → CycleEngine 자동 수렴 루프
- "흡수", "absorption" → 발견 규칙 승격 + 다음 사이클 시드
- "사이클", "cycle" → 전체 5단계 1회 실행

### 사용법
```bash
nexus6 blowup <domain> --depth 6    # 블로업 + 창발 리포트
nexus6 loop --cycles 1              # 8단계 루프 (mirror+blowup 포함)
nexus6 daemon --interval 30         # 자율 데몬 (30분 간격)
```

