# NEXUS GitHub Pages

This `docs/` directory is published via GitHub Pages.

## Contents

<!-- 노드 수는 index.html 내장 데이터 기준, atlas.n6 SSOT는 4,411 노드 -->
- `index.html` — Reality Map 3D (n=6, 4,411 nodes, embedded data)
- `reality_map_3d.html` — same as index (mirror)
- `reality_map.json` — full reality map dataset (relative fetch ok)
- `hypotheses/`, `mk2/`, `mk4/`, `superpowers/` — supporting docs

## Pages 활성화 방법 (사용자 권한 필요)

1. GitHub repo → **Settings** → **Pages**
2. **Build and deployment** → **Source**: `GitHub Actions` 선택
3. `main` 브랜치에 `docs/` 변경을 푸시하면 `.github/workflows/pages.yml`이 자동 배포
4. 배포 후 URL: `https://dancinlab.github.io/nexus/`
5. 수동 트리거: Actions 탭 → `Deploy GitHub Pages` → `Run workflow`

## 로컬 미리보기

```sh
cd docs && python3 -m http.server 8000
# http://localhost:8000/
```
