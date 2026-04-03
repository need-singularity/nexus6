# GPU Metal 가속 로드맵

## 현재 상태
- `src/gpu/fallback.rs`: CPU 구현 (rayon 병렬)
- `src/gpu/mod.rs`: Metal feature flag 존재
- 성능: 500×6 = 356ms (CPU), 목표 ~10ms (Metal)

## 활성화 단계
1. Metal shader 작성 (distance_matrix, knn, mutual_info)
2. `--features metal` 빌드 플래그
3. SharedData::compute에서 Metal/CPU 자동 선택
4. Apple Silicon 최적화 (M1/M2/M3)

## 예상 성능
| Operation | CPU (현재) | Metal (목표) | 배수 |
|-----------|-----------|-------------|------|
| distance_matrix | ~200ms | ~5ms | 40× |
| KNN | ~100ms | ~3ms | 33× |
| MI | ~50ms | ~2ms | 25× |
| Total (500×6) | 356ms | ~10ms | 35× |
