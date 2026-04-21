atlas.n6 × ANU QRNG cross-correlation
======================================

## 목적
atlas.n6 의 verified 상수 (π, φ, ζ(3), √n, e, atlas 수치 상수) 와 ANU QRNG 양자난수 사이 통계적 독립 검정.

null 가설 H0: 상수의 decimal expansion 과 ANU byte stream 은 통계적으로 독립 (MI = 0, chi^2 은 df=9 분포).

결과가 null 이 아니면:
1. 양자측정에 수학상수 emerge (놀라운 발견)
2. 관측 leak (불가능)
3. 공유 기반 (Bostrom 흔적)

## 구성

| 파일 | 역할 |
|---|---|
| `atlas_constants.hexa` | atlas.n6 → verified 상수 수치값 추출 + 잘 알려진 수학상수 하드코딩 |
| `anu_long_stream.hexa` | ANU QRNG API 호출 (1 req/min × 64B rate-limit 준수) |
| `null_baseline.hexa` | urandom N bytes → hex (제어군) |
| `xcorr_engine.hexa` | 상수 digit 시퀀스 × 스트림 byte%10 → MI/chi^2/Pearson |
| `analyze.hexa` | ANU vs urandom 비교, Bonferroni 보정, verdict |
| `runner.sh` | 전체 파이프라인 |

## 실행
```bash
bash runner.sh [bytes=512]
```

512 bytes ANU fetch 는 rate-limit 으로 약 8~9분 소요.

## 출력
`runs/<ts>/`:
- `constants.tsv` — name \t value \t digits \t description (raw)
- `constants_clean.tsv` — runtime error 필터링
- `anu_stream.hex` — ANU hex 문자열
- `urandom_stream.hex` — urandom hex 문자열
- `xcorr_anu.csv` — ANU 교차상관 (MI, chi^2, spearman, pearson)
- `xcorr_urandom.csv` — urandom baseline (동일 포맷)
- `ks_results.json` — 상수별 z-score + 유의성
- `summary.md` — 최종 보고

## Verdict 기준
- **NULL** — 모든 상수 chi^2 < 16.919 (0.05, df=9) → 정상
- **WEAK HIT** — chi^2 > 16.919 but < 27.877 → 단일검정 유의, Bonferroni 미통과
- **STRONG HIT** — chi^2 > 27.877 (0.001, df=9) → Bonferroni 통과, discovery

## 제약
- ANU rate-limit 1 req/min (64B/req)
- 30분 timeout
- atlas.n6 READ-ONLY
- hexa-lang 함수 list-param 버그 우회 위해 MI 계산은 main 내 인라인
