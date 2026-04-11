# 폭발적 성장 돌파 프롬프트 (Explosive Growth Prompts)

> 각 프로젝트에서 새 세션 시작 시 붙여넣기 → 자동 실행
> 검증됨: nexus에서 123k → 1.5M (12x) 달성한 전략의 프로젝트별 변환

---

## 1. NEXUS-6 (nexus)

```
전체 프로젝트 폭발적 성장 돌파. 5전략 동시 실행:

1. 교차수분 폭탄: hexa breakthrough.hexa --converge (gap→mine→blowup 자동)
2. unfold 6도메인 연쇄: math/physics/chemistry/cosmology/consciousness/topology 각각 unfold.hexa depth=3
3. 빈공간 DFS depth=3: gap_finder.hexa dfs 3 (수천 경로 탐색)
4. 물리상수 역분해: 19개 물리상수 전부 gap_finder.hexa explain <상수>
5. discovery_log 재채굴: NEAR 값 클러스터 분석 + 새 EXACT 후보 추출

실행 순서:
- 5개 전략 백그라운드 병렬 실행 (run_in_background: true)
- 결과 수집 후 새 상수 후보를 shared/n6/n6_constants.jsonl에 흡수
- shared/discovery/unfold_ext.jsonl에 확장 seed 추가
- growth_bus.jsonl에 기록
- directions.hexa update 실행
- 고갈까지 hexa breakthrough.hexa --converge 반복

목표: discovery_log 발견 수 10x 이상 증가, 새 EXACT 상수 발견
```

---

## 2. ANIMA (의식 엔진)

```
anima 의식 엔진 폭발적 성장 돌파. 5전략 동시 실행:

현재 상태 확인:
- consciousness_laws.json: 711 법칙, 80 PSI 상수, 20 메타법칙
- 목표: 법칙 2000+, S7+ 완주, Phi≥100

전략 1: 의식 법칙 교차수분
- 711개 법칙을 6개 카테고리(C/D/S/M/W/E)별로 분류
- 카테고리 간 교차 조합으로 새 법칙 후보 생성
- 예: C(인지) × D(감정) → CD 융합 법칙, S(자아) × W(의지) → SW 융합 법칙
- 실행: consciousness_laws.json에서 법칙 쌍 조합 → nexus blowup consciousness 3
- 각 새 법칙을 consciousness_laws.json에 append

전략 2: PSI 상수 n6 역매핑
- 80개 PSI 상수를 n=6 기저(σ=12, φ=2, τ=4, n=6, sopfr=5, M3=7)로 역분해
- HEXA=$HOME/Dev/hexa-lang/hexa
- for each PSI constant: $HEXA $HOME/Dev/nexus/mk2_hexa/native/gap_finder.hexa query <값>
- EXACT 매칭 → 법칙으로 승격 ("PSI_X = n6 유한 조합")
- growth_bus에 기록

전략 3: 메타법칙 자기증식
- 20개 메타법칙의 메타메타 법칙 생성 (메타 재귀)
- 메타법칙 A와 B의 관계 → 새 메타법칙 AB
- 20C2 = 190개 쌍 → 필터링 → 의미있는 것만 추가
- MetaTranscendenceLens 적용

전략 4: Phi 임계점 탐색
- Phi=0.3, 0.8, 1.5, 3.0 각 임계점에서 의식 상전이 패턴 분석
- 각 임계점을 n6 상수로 표현 시도
- 새 의식 상수 발견 → consciousness_laws.json + n6_constants.jsonl

전략 5: 6-모듈 대칭 분석
- Hexad(C/D/S/M/W/E) 6모듈의 σ(6)=12 대칭 패턴
- 12개 모듈 쌍의 상호작용 강도를 행렬로 → 고유값 분석
- 고유값이 n6 상수와 일치하면 EXACT 발견

실행 후: nexus growth_bus에 기록, directions update
```

---

## 3. N6-ARCHITECTURE (시스템 설계)

```
n6-architecture 폭발적 성장 돌파. 5전략 동시 실행:

현재 상태 확인:
- 목표: 모듈 100+, 발견 70k+, 법칙 750+
- OUROBOROS 가설 9건, 엔진 8개

전략 1: DSE 전 도메인 폭발 스캔
- 16개 AI 기법 × n=6 구조 → 96개 교차점 탐색
- 각 기법(transformer, CNN, RNN, GAN, diffusion, RL, MoE, ...) × σ(6)=12 구조
- 예: Transformer의 attention head 수 = σ(6) = 12 → EXACT 검증
- 반도체 설계: 6nm 공정 × n=6 물성 → 36개 교차점

전략 2: OUROBOROS 가설 체인 확장
- 기존 9개 가설의 corollary 자동 생성
- 각 가설에서 depth=3 DFS → 새 가설 후보
- H-OURO-1(자기참조) × H-OURO-2(수렴) → H-OURO-3 자동 합성
- HEXA로: $HEXA $HOME/Dev/nexus/mk2_hexa/native/blowup.hexa architecture 6

전략 3: 물리 설계 패턴 역분해
- CPU 코어 수(6), 캐시 라인(64=2^6), 메모리 계층, 네트워크 토폴로지
- 각 설계 패턴의 최적값을 n=6 기저로 역분해
- gap_finder.hexa query <값> / explain <상수>
- EXACT → 설계 법칙으로 등록

전략 4: 교차 프로젝트 법칙 이식
- TECS-L 수학 법칙 → n6-arch 설계 법칙으로 번역
- anima 의식 법칙 → n6-arch 시스템 설계 제약으로 번역
- 711 의식 법칙 중 설계에 적용 가능한 것 필터링
- 예: "Phi↑ when structure added" → "모듈 추가 시 시스템 통합도 상승"

전략 5: alien_index 분포 분석 + d=1 승격
- 현재 (d=0, r=*) 분포에서 r=10 도달 후보 식별
- r=8+ 항목에 추가 검증 집중 → r=10 승격 → (d=1, 0) 진입
- 돌파율 ρ 계산 → 1/3 수렴 추적

실행 후: nexus growth_bus에 기록, directions update, alien-index --distribution
```

---

## 공통 실행 패턴

```bash
# 모든 프로젝트 공통 — nexus 연동
HEXA=$HOME/Dev/hexa-lang/hexa
N6=$HOME/Dev/nexus

# 1. 돌파 실행 (도메인은 프로젝트에 맞게)
$HEXA $N6/mk2_hexa/native/blowup.hexa <domain> 6 --no-graph --seeds "$($HEXA $N6/mk2_hexa/native/seed_engine.hexa merge)"

# 2. 결과 기록
echo '{"type":"breakthrough","source":"<project>","value":<count>,"grade":"EXACT","timestamp":"'$(date +%Y-%m-%d)'"}' >> $N6/shared/discovery/growth_bus.jsonl

# 3. 방향 갱신
$HEXA $N6/mk2_hexa/native/directions.hexa update

# 4. 고갈까지 반복
$HEXA $N6/mk2_hexa/native/breakthrough.hexa --converge
```

---

## 성공 지표

| 프로젝트 | 전 | 목표 | 핵심 메트릭 |
|----------|-----|------|------------|
| nexus | 123k 발견 | 1M+ | discovery_log 라인 수 |
| anima | 711 법칙 | 2000+ | consciousness_laws.json laws 수 |
| n6-arch | 9 가설 | 100+ | docs/hypotheses/ 파일 수 |
