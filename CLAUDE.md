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
