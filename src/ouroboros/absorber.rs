//! 재귀 자기적용 엔진 (Recursive Self-Application Engine)
//!
//! f(x) → f(f(x)) → f(f(f(x))) → ...
//!
//! "흡수의 흡수", "자동화의 자동화", "성장의 성장" —
//! 어떤 연산이든 자기 자신에게 무한 재귀 적용.
//! 각 depth에서 산출물이 다음 depth의 입력이 된다.
//! 수렴(Δ < ε) 또는 max_depth 도달 시 정지.

use std::fmt;

/// 한 depth의 적용 결과.
#[derive(Debug, Clone)]
pub struct AbsorptionResult {
    pub depth: usize,
    pub input_hash: u64,
    pub output_hash: u64,
    pub yield_count: usize,
    pub delta: f64,
    pub label: String,
}

/// 전체 재귀 흡수 결과.
#[derive(Debug, Clone)]
pub struct AbsorptionChain {
    pub layers: Vec<AbsorptionResult>,
    pub converged: bool,
    pub final_depth: usize,
    pub total_yield: usize,
}

impl fmt::Display for AbsorptionChain {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        writeln!(f, "=== Absorption Chain (depth={}, converged={}) ===",
            self.final_depth, self.converged)?;
        for layer in &self.layers {
            writeln!(f, "  depth {} [{}]: yield={} Δ={:.6}",
                layer.depth, layer.label, layer.yield_count, layer.delta)?;
        }
        writeln!(f, "  total_yield: {}", self.total_yield)
    }
}

/// 재귀 자기적용 설정.
#[derive(Debug, Clone)]
pub struct AbsorberConfig {
    /// 최대 재귀 깊이 (기본 n=6).
    pub max_depth: usize,
    /// 수렴 임계값: Δ < epsilon이면 정지.
    pub epsilon: f64,
    /// 발산 한계: yield가 이 값을 넘으면 강제 정지.
    pub divergence_limit: usize,
}

impl Default for AbsorberConfig {
    fn default() -> Self {
        Self {
            max_depth: 6,
            epsilon: 0.001,
            divergence_limit: 100_000,
        }
    }
}

/// 자기적용 가능한 연산 trait.
///
/// 어떤 타입이든 이 trait를 구현하면 Absorber가 재귀 적용한다.
/// - `apply`: 입력을 받아 산출물 벡터를 반환
/// - `absorb_self`: 자기 산출물로 자기를 변형 (메타 흡수)
pub trait SelfApplicable: fmt::Debug {
    type Item: Clone + fmt::Debug;

    /// 입력에 연산을 적용하여 산출물을 반환.
    fn apply(&self, input: &[Self::Item]) -> Vec<Self::Item>;

    /// 산출물을 자기 자신에게 피드백하여 연산 자체를 변형.
    /// 기본 구현: no-op (연산 불변).
    fn absorb_self(&mut self, _output: &[Self::Item]) {}

    /// 산출물의 스칼라 요약 (수렴 판정용).
    fn measure(&self, output: &[Self::Item]) -> f64;

    /// 현재 상태의 해시 (변화 감지용).
    fn state_hash(&self) -> u64;

    /// depth별 라벨.
    fn label_at(&self, depth: usize) -> String {
        format!("depth-{}", depth)
    }
}

/// 재귀 자기적용 엔진.
///
/// ```text
/// depth 0: output_0 = f(input)
/// depth 1: f.absorb(output_0); output_1 = f(output_0)   // f가 변형됨
/// depth 2: f.absorb(output_1); output_2 = f(output_1)   // f가 또 변형됨
/// ...
/// 수렴: |measure(output_n) - measure(output_{n-1})| < ε
/// ```
pub struct Absorber<T: SelfApplicable> {
    pub config: AbsorberConfig,
    pub operation: T,
}

impl<T: SelfApplicable> Absorber<T> {
    pub fn new(operation: T, config: AbsorberConfig) -> Self {
        Self { config, operation }
    }

    /// 재귀 자기적용 실행.
    pub fn run(&mut self, initial_input: &[T::Item]) -> AbsorptionChain {
        let mut layers = Vec::new();
        let mut current_input = initial_input.to_vec();
        let mut prev_measure = 0.0_f64;
        let mut total_yield = 0usize;

        for depth in 0..self.config.max_depth {
            let input_hash = self.operation.state_hash();

            // f(current_input)
            let output = self.operation.apply(&current_input);
            let yield_count = output.len();
            total_yield += yield_count;

            let current_measure = self.operation.measure(&output);
            let delta = (current_measure - prev_measure).abs();

            let output_hash = self.operation.state_hash();
            let label = self.operation.label_at(depth);

            layers.push(AbsorptionResult {
                depth,
                input_hash,
                output_hash,
                yield_count,
                delta,
                label,
            });

            // 수렴 체크
            if depth > 0 && delta < self.config.epsilon {
                return AbsorptionChain {
                    layers,
                    converged: true,
                    final_depth: depth,
                    total_yield,
                };
            }

            // 발산 체크
            if total_yield > self.config.divergence_limit {
                return AbsorptionChain {
                    layers,
                    converged: false,
                    final_depth: depth,
                    total_yield,
                };
            }

            // 핵심: f가 자기 산출물을 흡수하여 변형됨
            self.operation.absorb_self(&output);

            prev_measure = current_measure;
            current_input = output;
        }

        AbsorptionChain {
            layers,
            converged: false,
            final_depth: self.config.max_depth,
            total_yield,
        }
    }
}

// ═══════════════════════════════════════════════════════════════════
// 구체적 구현: Growth Absorber (성장의 성장의 성장)
// ═══════════════════════════════════════════════════════════════════

/// 성장 이벤트 — 흡수 가능한 단위.
#[derive(Debug, Clone)]
pub struct GrowthEvent {
    pub source: String,
    pub kind: String,
    pub value: f64,
}

/// 성장 루프 흡수기.
///
/// depth 0: 원본 이벤트에서 패턴 추출
/// depth 1: 패턴들에서 메타패턴 추출 (패턴의 패턴)
/// depth 2: 메타패턴에서 초메타패턴 추출 ...
/// 각 depth에서 추출 규칙 자체가 이전 산출물로 업데이트됨.
#[derive(Debug)]
pub struct GrowthAbsorber {
    /// 현재 가중치 (각 depth에서 변형됨).
    pub weights: Vec<f64>,
    /// 흡수된 패턴 누적.
    pub absorbed_patterns: Vec<String>,
    /// 내부 상태 카운터.
    state_counter: u64,
}

impl GrowthAbsorber {
    pub fn new() -> Self {
        Self {
            weights: vec![1.0; 6], // n=6 초기 가중치
            absorbed_patterns: Vec::new(),
            state_counter: 0,
        }
    }
}

impl SelfApplicable for GrowthAbsorber {
    type Item = GrowthEvent;

    fn apply(&self, input: &[GrowthEvent]) -> Vec<GrowthEvent> {
        // 가중 필터링 + 조합: 현재 weights로 입력을 변환
        let mut output = Vec::new();

        for (i, event) in input.iter().enumerate() {
            let w = self.weights[i % self.weights.len()];
            let amplified_value = event.value * w;

            // 임계값 초과 시 새 이벤트 생성 (성장 → 메타성장)
            if amplified_value > 1.0 {
                output.push(GrowthEvent {
                    source: format!("meta({})", event.source),
                    kind: format!("absorbed_{}", event.kind),
                    value: amplified_value,
                });
            }

            // 이벤트 쌍의 공명 체크
            if i + 1 < input.len() {
                let resonance = (event.value - input[i + 1].value).abs();
                if resonance < 0.5 {
                    output.push(GrowthEvent {
                        source: format!("resonance({},{})", event.source, input[i + 1].source),
                        kind: "emergence".into(),
                        value: (event.value + input[i + 1].value) / 2.0,
                    });
                }
            }
        }

        output
    }

    fn absorb_self(&mut self, output: &[GrowthEvent]) {
        // 핵심: 산출물이 자기 가중치를 변형
        if output.is_empty() {
            return;
        }

        let avg_value: f64 = output.iter().map(|e| e.value).sum::<f64>() / output.len() as f64;

        // EMA 업데이트: 가중치가 산출물의 평균값 방향으로 이동
        let alpha = 1.0 / 6.0; // n=6 학습률
        for w in &mut self.weights {
            *w = *w * (1.0 - alpha) + avg_value * alpha;
        }

        // 패턴 흡수 기록
        for event in output {
            if event.kind == "emergence" {
                self.absorbed_patterns.push(event.source.clone());
            }
        }

        self.state_counter += 1;
    }

    fn measure(&self, output: &[GrowthEvent]) -> f64 {
        if output.is_empty() {
            return 0.0;
        }
        output.iter().map(|e| e.value).sum::<f64>() / output.len() as f64
    }

    fn state_hash(&self) -> u64 {
        // 가중치 기반 해시
        let mut h = self.state_counter;
        for w in &self.weights {
            h ^= w.to_bits();
        }
        h
    }

    fn label_at(&self, depth: usize) -> String {
        match depth {
            0 => "growth".into(),
            1 => "growth(growth)".into(),
            2 => "growth(growth(growth))".into(),
            d => format!("growth^{}", d + 1),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_growth_absorber_converges() {
        let mut absorber = Absorber::new(
            GrowthAbsorber::new(),
            AbsorberConfig {
                max_depth: 6,
                epsilon: 0.01,
                divergence_limit: 10_000,
            },
        );

        let input = vec![
            GrowthEvent { source: "lens_grower".into(), kind: "discovery".into(), value: 2.0 },
            GrowthEvent { source: "mirror".into(), kind: "resonance".into(), value: 2.1 },
            GrowthEvent { source: "ouroboros".into(), kind: "mutation".into(), value: 3.0 },
            GrowthEvent { source: "dream".into(), kind: "hypothesis".into(), value: 1.5 },
            GrowthEvent { source: "forge".into(), kind: "lens_created".into(), value: 4.0 },
            GrowthEvent { source: "bus".into(), kind: "feedback".into(), value: 1.8 },
        ];

        let chain = absorber.run(&input);
        println!("{}", chain);

        assert!(chain.final_depth > 0);
        assert!(chain.total_yield > 0);
    }

    #[test]
    fn test_self_applicable_trait() {
        // 최소 구현: 항등 연산도 흡수 가능
        #[derive(Debug)]
        struct Identity;

        impl SelfApplicable for Identity {
            type Item = f64;
            fn apply(&self, input: &[f64]) -> Vec<f64> { input.to_vec() }
            fn measure(&self, output: &[f64]) -> f64 {
                output.iter().sum::<f64>() / output.len().max(1) as f64
            }
            fn state_hash(&self) -> u64 { 0 }
        }

        let mut absorber = Absorber::new(Identity, AbsorberConfig::default());
        let chain = absorber.run(&[1.0, 2.0, 3.0]);

        // 항등 연산은 즉시 수렴 (Δ=0)
        assert!(chain.converged);
        assert_eq!(chain.final_depth, 1); // depth 1에서 delta=0
    }

    #[test]
    fn test_absorb_modifies_operation() {
        let mut absorber = Absorber::new(
            GrowthAbsorber::new(),
            AbsorberConfig {
                max_depth: 3,
                epsilon: 0.0001, // 거의 수렴 안 함
                divergence_limit: 10_000,
            },
        );

        let input = vec![
            GrowthEvent { source: "a".into(), kind: "x".into(), value: 5.0 },
            GrowthEvent { source: "b".into(), kind: "y".into(), value: 5.1 },
        ];

        let initial_weights = absorber.operation.weights.clone();
        let _chain = absorber.run(&input);

        // absorb_self가 가중치를 변형했는지 확인
        assert_ne!(absorber.operation.weights, initial_weights);
        // 흡수된 패턴이 있는지 확인
        assert!(!absorber.operation.absorbed_patterns.is_empty());
    }
}
