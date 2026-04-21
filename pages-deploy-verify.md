# 3D 현실지도 GitHub Pages 배포 재검증 (2026-04-16)

## 결론: 미배포 (NOT DEPLOYED)

## 로컬 상태
- atlas.n6 (권위): atlas.n6 v1 7693
- reality_map_3d.html 임베디드: 
- dashboard.html 존재: YES
- docs/index.html 존재: YES
- .github/workflows/ 파일 수: 2

## GitHub Pages API
- repos/need-singularity/nexus has_pages: true
- repos/need-singularity/nexus/pages: 404 (사이트 없음)

## URL 프로빙 (curl -L)
| URL | HTTP |
|---|---|
| https://need-singularity.github.io/nexus/ | 200 |
| https://need-singularity.github.io/nexus/index.html | 200 |
| https://need-singularity.github.io/nexus/reality_map_3d.html | 404 |
| https://need-singularity.github.io/nexus/reality_map_3d.html | 404 |

## 버전 격차
- Target 요구: v6.0 / 276 노드
- atlas.n6 실제: atlas.n6 v1 7693 (상위 세대)
- reality_map_3d.html 임베디드:  (구세대)
- v6.0 276 스냅샷은 로컬/원격 모두 부재 — 권위 데이터는 이미 진화

## 권고
1. reality_map_3d.html을 atlas.n6(atlas.n6 v1 7693) 기반 생성기로 재생성
2. .github/workflows/pages.yml 추가 또는 Settings Pages 활성화
3. docs/index.html 생성 또는 root publish 경로 설정
4. 배포 후 Playwright로 fetch 경로 + 노드 렌더링 재검증
