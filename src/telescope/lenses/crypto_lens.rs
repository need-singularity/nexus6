use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::{SharedData, mean_var, shannon_entropy};

/// n=6 crypto constants (BT-53)
const N: f64 = 6.0;       // BTC 6 confirms
const SIGMA: f64 = 12.0;  // ETH 12s block time
const J2: f64 = 24.0;     // Jordan J₂(6)
const TAU: f64 = 4.0;
const SOPFR: f64 = 5.0;

/// Key blockchain/crypto constants
const CRYPTO_CONSTANTS: &[(f64, &str)] = &[
    (6.0, "n (BTC confirms)"),
    (12.0, "sigma (ETH block time)"),
    (24.0, "J2"),
    (21.0, "J2-n/phi (BTC 21M supply)"),
    (10.0, "sigma-phi (min interval)"),
    (256.0, "2^(sigma-tau) (SHA-256)"),
    (128.0, "2^(sigma-sopfr) (AES-128)"),
    (64.0, "2^n (hash output bits)"),
    (32.0, "2^sopfr (nonce bytes)"),
];

const REL_TOL: f64 = 0.05;

/// CryptoLens: Detect blockchain/cryptographic patterns in data.
///
/// Metrics: hash_uniformity, nonce_distribution, block_time_regularity,
///          merkle_depth, n6_crypto_matches
pub struct CryptoLens;

fn matches_constant(val: f64, target: f64) -> bool {
    if target.abs() < 1e-12 { return val.abs() < 0.01; }
    (val - target).abs() / target.abs() < REL_TOL
}

impl Lens for CryptoLens {
    fn name(&self) -> &str { "CryptoLens" }
    fn category(&self) -> &str { "T1" }

    fn scan(&self, data: &[f64], n: usize, d: usize, shared: &SharedData) -> LensResult {
        if n < 3 || d == 0 { return HashMap::new(); }

        let (means, vars) = mean_var(data, n, d);

        // 1. Hash uniformity: entropy of each feature should be high (near uniform)
        let mut entropy_sum = 0.0;
        for col in 0..d {
            entropy_sum += shannon_entropy(&data[col*n..(col+1)*n], (n as f64).sqrt() as usize);
        }
        let hash_uniformity = (entropy_sum / d as f64).min(1.0);

        // 2. Nonce distribution: check if values spread across range (low clustering)
        let mut nonce_score = 0.0;
        for col in 0..d {
            let var = vars[col];
            let mean_abs = means[col].abs().max(1e-12);
            let cv = var.sqrt() / mean_abs;
            nonce_score += cv.min(2.0) / 2.0;
        }
        nonce_score /= d as f64;

        // 3. Block time regularity: consecutive difference stability
        let mut regularity = 0.0;
        if n > 2 {
            for col in 0..d.min(3) {
                let mut diffs = Vec::with_capacity(n - 1);
                for i in 0..(n - 1) {
                    let idx0 = i * d + col;
                    let idx1 = (i + 1) * d + col;
                    if idx1 < data.len() {
                        diffs.push((data[idx1] - data[idx0]).abs());
                    }
                }
                if diffs.len() > 1 {
                    let mean_d = diffs.iter().sum::<f64>() / diffs.len() as f64;
                    if mean_d > 1e-12 {
                        let var_d = diffs.iter().map(|x| (x - mean_d).powi(2)).sum::<f64>() / diffs.len() as f64;
                        regularity += (-var_d.sqrt() / mean_d).exp();
                    }
                }
            }
            regularity /= d.min(3) as f64;
        }

        // 4. Merkle depth: log2-like structure detection
        let merkle_depth = (n as f64).log2().round();

        // 5. n=6 crypto constant matching
        let mut n6_matches = 0;
        for &mean in &means {
            for &(target, _) in CRYPTO_CONSTANTS {
                if matches_constant(mean, target) { n6_matches += 1; break; }
            }
        }

        let mut result = HashMap::new();
        result.insert("hash_uniformity".into(), vec![hash_uniformity]);
        result.insert("nonce_distribution".into(), vec![nonce_score]);
        result.insert("block_time_regularity".into(), vec![regularity]);
        result.insert("merkle_depth".into(), vec![merkle_depth]);
        result.insert("n6_crypto_matches".into(), vec![n6_matches as f64]);
        result
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn test_crypto_basic() {
        let data: Vec<f64> = (0..60).map(|i| (i as f64 * 0.5).sin() * 12.0).collect();
        let shared = SharedData::compute(&data, 10, 6);
        let result = CryptoLens.scan(&data, 10, 6, &shared);
        assert!(!result.is_empty());
        assert!(result.contains_key("hash_uniformity"));
        assert!(result.contains_key("n6_crypto_matches"));
    }
}
