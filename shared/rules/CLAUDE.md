# rules/ — AI-native 규칙 체계

R14 단일진실: 모든 규칙 본문은 이 폴더 JSON만. CLAUDE.md는 참조만.

## 구조

```
common.json            공통 규칙 R0~R27 (전 프로젝트 적용)
lockdown.json          L0/L1/L2 동심원 보호 체계 + 프로젝트별 파일 잠금
convergence_ops.json   CDO 수렴 운영 원칙 (P1~P5 + 스키마 + 부트스트랩)
nexus.json             NX1~NX3
anima.json             AN1~AN7
n6-architecture.json   N61~N65
papers.json            PP1~PP3
hexa-lang.json         HX1~HX6
void.json              VD1~VD2
contact.json           CT1~CT4
airgenome.json         AG1~AG4
```

## 원칙

- AI-native: 저수준 마이크로 최적화 금지, 알고리즘/자료구조 레벨 돌파만
- SSOT: 규칙 원본 = 이 폴더 JSON. 중복 기록 금지
- CDO: 이슈→해결→규칙승격→재발0→100%수렴
- 골화: stable→ossified 단방향, 역전이 금지

parent: ../CLAUDE.md
