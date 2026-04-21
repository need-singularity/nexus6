# Secret Repository Reference

> 민감 정보 (계정, API 토큰)는 private 리포에 보관.
> 절대 public 리포에 토큰/비밀번호 하드코딩 금지.

## 리포

- **리포**: [need-singularity/secret](https://github.com/need-singularity/secret) (private)
- **로컬**: `~/Dev/secret/`
- **이전 이름**: `claude-code-secrets` (2026-04-01 renamed)

## 토큰 위치

| 토큰 | 위치 | 용도 |
|------|------|------|
| Zenodo | `~/Dev/TECS-L/.local/zenodo_token` | 논문 발행 (DOI) |
| OSF | `~/Dev/TECS-L/.local/osf_token` | 논문 발행 (OSF) |
| Gmail | `~/Dev/TECS-L/.local/gmail_credentials.json` | 이메일 아웃리치 |
| Gmail Token | `~/Dev/TECS-L/.local/gmail_token.json` | OAuth 토큰 |
| RunPod | `~/Dev/TECS-L/.local/runpod_api_key` | GPU 서버 |
| Zenodo Sandbox | `~/Dev/TECS-L/.local/zenodo_sandbox_token` | 테스트용 |

## 계정 정보 (상세: ~/Dev/secret/README.md)

| # | 서비스 | 용도 | 위치 |
|---|--------|------|------|
| 1 | Claude Code ×10 | AI 코딩 세션 | `secret/README.md` §1 |
| 2 | Cloudflare R2 | anima 모델/corpus/메모리 스토리지 | `secret/README.md` §2 |
| 3 | fal.ai | 이미지 생성 (creator) | `secret/README.md` §3 |
| 4 | OpenRouter | LLM API 번역 (creator) | `secret/README.md` §4 |
| 5 | Gmail API | 논문 아웃리치 이메일 | `secret/README.md` §5 |
| 6 | Zenodo | 논문 DOI 발행 | `secret/README.md` §6 |
| 7 | OSF | 논문 노드 업로드 | `secret/README.md` §7 |
| 8 | Google AI (Gemini) | LLM API | `secret/README.md` §8 |
| 9 | Vast.ai | 4×4090 GPU 학습 | `secret/README.md` §9 |
| 10 | RunPod | A100/H100 GPU | `secret/README.md` §10 |
| 11 | Namecheap | 도메인 | `secret/README.md` §11+ |

## 프로젝트별 사용 토큰

| 프로젝트 | 사용 토큰 |
|----------|-----------|
| 🔭 **nexus** | — (인프라 전용, 토큰 불필요) |
| 🧠 **anima** | Vast.ai (§9), R2 (§2), RunPod (§10) |
| 🏗️ **n6-architecture** | — (설계 전용) |
| 📄 **papers** | Zenodo (§6), OSF (§7) |
| 💎 **hexa-lang** | — (컴파일러 전용) |
| 🖥️ **void** | — (터미널 전용) |
| 🧬 **airgenome** | — (스캐너 전용) |
| 📧 **contact** (private) | Gmail API (§5) |
| 🎨 **creator** (private) | fal.ai (§3), OpenRouter (§4) |

## 사용법

```bash
# Zenodo 논문 발행
ZENODO_TOKEN=$(cat ~/Dev/TECS-L/.local/zenodo_token)

# OSF 논문 발행
OSF_TOKEN=$(cat ~/Dev/TECS-L/.local/osf_token)

# Gmail 이메일
# send_emails.py가 자동으로 ~/Dev/TECS-L/.local/ 참조

# 각 리포 CLAUDE.md에서 이 파일 참조:
# "API 토큰/계정: ~/Dev/TECS-L/.shared/SECRET.md 참조"
```

## 규칙

1. **토큰은 `.local/` 디렉토리에만** — `.gitignore`에 포함됨
2. **계정 정보는 `secret` 리포에만** — private 리포
3. **public 리포에 절대 하드코딩 금지**
4. **새 토큰 추가 시 이 파일 + `secret/README.md` 동시 업데이트**
