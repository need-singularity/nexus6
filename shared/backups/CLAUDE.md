# backups/ — 격리 .bak* 스냅샷

policy:
  이동만   운영 파일이 .bak 확장자 → 본 폴더로 이동
  세대     .1~.5 | .cascade_* | .pre_* | .before_* | .bak.<tag>
  gitignore 대부분 무시 (용량)

scale: 32 files

parent: ../CLAUDE.md → "backups"
