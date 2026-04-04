use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::SharedData;

/// SchurFunctorLens: Detect Schur functor / combinatorial geometry patterns —
/// partitions, Young tableaux, Littlewood-Richardson coefficients.
///
/// n=6 connection: p(6) = 11 partitions, Schur polynomials S_λ for |λ|=6,
/// Littlewood-Richardson rule governs tensor product decomposition.
pub struct SchurFunctorLens;

/// Generate all partitions of n (descending order).
fn partitions(n: usize) -> Vec<Vec<usize>> {
    let mut result = Vec::new();
    let mut current = Vec::new();
    partitions_helper(n, n, &mut current, &mut result);
    result
}

fn partitions_helper(n: usize, max_part: usize, current: &mut Vec<usize>, result: &mut Vec<Vec<usize>>) {
    if n == 0 {
        result.push(current.clone());
        return;
    }
    for k in (1..=n.min(max_part)).rev() {
        current.push(k);
        partitions_helper(n - k, k, current, result);
        current.pop();
    }
}

/// Hook length for a cell (i,j) in partition lambda.
fn hook_length(lambda: &[usize], i: usize, j: usize) -> usize {
    let arm = lambda[i] - j - 1;
    let leg = lambda.iter().skip(i + 1).filter(|&&part| part > j).count();
    arm + leg + 1
}

/// Dimension of irrep via hook-length formula: n! / prod(hook lengths).
fn hook_dimension(lambda: &[usize], n: usize) -> f64 {
    let n_fact: f64 = (1..=n).map(|i| i as f64).product();
    let mut hook_prod = 1.0;
    for (i, &part) in lambda.iter().enumerate() {
        for j in 0..part {
            hook_prod *= hook_length(lambda, i, j) as f64;
        }
    }
    if hook_prod > 0.0 { n_fact / hook_prod } else { 0.0 }
}

/// Compute Schur polynomial proxy: evaluate s_λ(x_1,...,x_k) using
/// ratio of alternants formula for small cases.
fn schur_polynomial_eval(lambda: &[usize], x: &[f64]) -> f64 {
    let k = x.len().min(6);
    if k == 0 {
        return 0.0;
    }

    // Compute the Vandermonde determinant: prod_{i<j} (x_i - x_j)
    let mut vander = 1.0;
    for i in 0..k {
        for j in (i + 1)..k {
            vander *= x[i] - x[j];
        }
    }
    if vander.abs() < 1e-15 {
        return 0.0;
    }

    // Numerator: det(x_j^(λ_i + k - i - 1))
    // For efficiency, compute 3x3 or smaller
    let m = k.min(lambda.len()).min(3);
    let mut num_det = 0.0;
    if m == 1 {
        let exp = lambda.get(0).copied().unwrap_or(0) as f64;
        num_det = x[0].powf(exp);
    } else if m == 2 {
        let e0 = lambda.get(0).copied().unwrap_or(0) as f64 + 1.0;
        let e1 = lambda.get(1).copied().unwrap_or(0) as f64;
        num_det = x[0].powf(e0) * x[1].powf(e1) - x[0].powf(e1) * x[1].powf(e0);
    } else {
        // 3x3 determinant
        let exp = |i: usize| lambda.get(i).copied().unwrap_or(0) as f64 + (m - 1 - i) as f64;
        let a = |i: usize, j: usize| x[j].powf(exp(i));
        num_det = a(0, 0) * (a(1, 1) * a(2, 2) - a(1, 2) * a(2, 1))
            - a(0, 1) * (a(1, 0) * a(2, 2) - a(1, 2) * a(2, 0))
            + a(0, 2) * (a(1, 0) * a(2, 1) - a(1, 1) * a(2, 0));
    }

    num_det / vander.abs().max(1e-15)
}

impl Lens for SchurFunctorLens {
    fn name(&self) -> &str {
        "SchurFunctorLens"
    }

    fn category(&self) -> &str {
        "T2"
    }

    fn scan(&self, data: &[f64], n: usize, d: usize, _shared: &SharedData) -> LensResult {
        if n < 6 {
            return HashMap::new();
        }

        let mut result = HashMap::new();
        let max_n = n.min(200);
        let vals: Vec<f64> = (0..max_n).map(|i| data[i * d]).collect();

        // 1. Partition count verification: p(6) = 11
        let parts = partitions(6);
        result.insert("partition_count".to_string(), vec![parts.len() as f64]);

        // 2. Hook-length dimensions for all partitions of 6
        let dims: Vec<f64> = parts.iter().map(|p| hook_dimension(p, 6)).collect();
        result.insert("hook_dimensions".to_string(), dims.clone());

        // Verify dimension sum: Σ d_λ² = 6! = 720
        let dim_sq_sum: f64 = dims.iter().map(|d| d * d).sum();
        let dim_formula_error = (dim_sq_sum - 720.0).abs() / 720.0;
        result.insert("dimension_formula_error".to_string(), vec![dim_formula_error]);

        // 3. Schur polynomial evaluation on data samples
        let sample_x: Vec<f64> = vals.iter().take(6).cloned().collect();
        if sample_x.len() >= 3 {
            let mut schur_vals = Vec::new();
            for part in parts.iter().take(6) {
                schur_vals.push(schur_polynomial_eval(part, &sample_x));
            }
            result.insert("schur_polynomial_values".to_string(), schur_vals);
        }

        // 4. Littlewood-Richardson proxy: measure tensor product structure
        //    Check if pairwise products of data segments decompose into "irrep" components
        let chunk_size = 6;
        if vals.len() >= chunk_size * 3 {
            let a = &vals[0..chunk_size];
            let b = &vals[chunk_size..2 * chunk_size];
            let c = &vals[2 * chunk_size..3 * chunk_size];

            // Tensor product: a ⊗ b should decompose as Σ c_λ · irrep_λ
            let mut tensor = Vec::with_capacity(chunk_size * chunk_size);
            for &ai in a {
                for &bi in b {
                    tensor.push(ai * bi);
                }
            }

            // Compare tensor structure with third segment
            let tensor_mean = tensor.iter().sum::<f64>() / tensor.len() as f64;
            let c_mean = c.iter().sum::<f64>() / c.len() as f64;
            let lr_coherence = if tensor_mean.abs() > 1e-12 {
                1.0 - (tensor_mean - c_mean).abs() / tensor_mean.abs().max(c_mean.abs()).max(1e-12)
            } else {
                0.0
            };
            result.insert("lr_coherence".to_string(), vec![lr_coherence.max(0.0)]);
        }

        // 5. Conjugate partition symmetry: λ ↔ λ' duality
        //    The conjugate of [6] is [1,1,1,1,1,1] — measure self-conjugate proximity
        let mut self_conj_count = 0;
        for part in &parts {
            // Compute conjugate
            let max_part = part.first().copied().unwrap_or(0);
            let conj: Vec<usize> = (0..max_part)
                .map(|j| part.iter().filter(|&&p| p > j).count())
                .collect();
            if *part == conj {
                self_conj_count += 1;
            }
        }
        result.insert("self_conjugate_count".to_string(), vec![self_conj_count as f64]);
        result.insert("score".to_string(), vec![result["partition_count"][0].min(1.0).max(0.0)]);

        result
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::telescope::shared_data::SharedData;

    #[test]
    fn test_schur_functor_basic() {
        let data: Vec<f64> = (0..60).map(|i| (i as f64 + 1.0).ln()).collect();
        let n = 10;
        let d = 6;
        let shared = SharedData::compute(&data, n, d);
        let result = SchurFunctorLens.scan(&data, n, d, &shared);
        assert!(!result.is_empty());
        assert_eq!(result["partition_count"][0], 11.0);
    }

    #[test]
    fn test_partitions_of_6() {
        let parts = partitions(6);
        assert_eq!(parts.len(), 11);
    }

    #[test]
    fn test_hook_dimension_trivial() {
        // Trivial representation [6] has dimension 1
        let dim = hook_dimension(&[6], 6);
        assert!((dim - 1.0).abs() < 0.01);
    }

    #[test]
    fn test_schur_functor_small() {
        let data = vec![1.0; 5];
        let shared = SharedData::compute(&data, 5, 1);
        let result = SchurFunctorLens.scan(&data, 5, 1, &shared);
        assert!(result.is_empty());
    }
}
