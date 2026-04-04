use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::SharedData;

/// StateSpaceObservabilityLens: Control theory analysis with 6-state systems.
///
/// Constructs a state-space model from data and analyzes:
/// - Observability rank (of 6x6 observability matrix)
/// - Controllability Gramian trace
/// - System pole locations
/// - Hankel singular values
pub struct StateSpaceObservabilityLens;

impl Lens for StateSpaceObservabilityLens {
    fn name(&self) -> &str { "StateSpaceObservabilityLens" }
    fn category(&self) -> &str { "T2" }

    fn scan(&self, data: &[f64], n: usize, d: usize, _shared: &SharedData) -> LensResult {
        if n < 12 || d == 0 { return HashMap::new(); }

        let state_dim = 6;
        let obs_dim = d.min(6);

        // Build state transition matrix A (6x6) from data via DMD-like approach
        // and observation matrix C (obs_dim x 6)
        let (a_mat, c_mat) = estimate_state_space(data, n, d, state_dim, obs_dim);

        // Observability matrix: O = [C; CA; CA^2; ...; CA^(n-1)]
        let obs_rank = observability_rank(&a_mat, &c_mat, state_dim, obs_dim);

        // Controllability Gramian approximation (using A and B=I)
        let gram_trace = controllability_gramian_trace(&a_mat, state_dim);

        // System poles: eigenvalues of A (via power iteration for dominant)
        let poles = estimate_eigenvalues(&a_mat, state_dim);
        let max_pole_mag = poles.iter().cloned().fold(0.0, f64::max);
        let is_stable = max_pole_mag < 1.0 + 1e-6;

        // Hankel singular values approximation
        let hankel_svs = hankel_singular_values(data, n, d, state_dim);

        let mut result = HashMap::new();
        result.insert("ss_observability_rank".to_string(), vec![obs_rank as f64]);
        result.insert("ss_gramian_trace".to_string(), vec![gram_trace]);
        result.insert("ss_pole_magnitudes".to_string(), poles);
        result.insert("ss_max_pole".to_string(), vec![max_pole_mag]);
        result.insert("ss_is_stable".to_string(), vec![if is_stable { 1.0 } else { 0.0 }]);
        result.insert("ss_hankel_sv".to_string(), hankel_svs);
        result.insert("ss_state_dim".to_string(), vec![state_dim as f64]);
        result
    }
}

/// Estimate state-space matrices A (state_dim x state_dim), C (obs_dim x state_dim)
/// using Dynamic Mode Decomposition (DMD)-like approach.
fn estimate_state_space(
    data: &[f64], n: usize, d: usize, state_dim: usize, obs_dim: usize,
) -> (Vec<f64>, Vec<f64>) {
    // Build data matrices X = [x_0, ..., x_{n-2}], Y = [x_1, ..., x_{n-1}]
    // where x_i is the i-th observation (obs_dim-dimensional)
    let m = n - 1;
    let sd = state_dim.min(obs_dim);

    // Compute covariance-like matrices for A estimation
    // A_approx = Y * X^T * (X * X^T)^{-1} projected to state_dim x state_dim

    // Simple approach: use first state_dim components as state
    let mut a_mat = vec![0.0; state_dim * state_dim];
    let mut xtx = vec![0.0; sd * sd];
    let mut ytx = vec![0.0; sd * sd];

    for t in 0..m {
        for i in 0..sd {
            let xi = data[t * d + i];
            let yi = data[(t + 1) * d + i];
            for j in 0..sd {
                let xj = data[t * d + j];
                xtx[i * sd + j] += xi * xj;
                ytx[i * sd + j] += yi * xj;
            }
        }
    }

    // Regularize
    for i in 0..sd {
        xtx[i * sd + i] += 1e-6;
    }

    // Solve A_sd = YX^T * (XX^T)^{-1}
    let xtx_inv = invert_matrix(&xtx, sd);
    let mut a_sd = vec![0.0; sd * sd];
    for i in 0..sd {
        for j in 0..sd {
            let mut sum = 0.0;
            for k in 0..sd {
                sum += ytx[i * sd + k] * xtx_inv[k * sd + j];
            }
            a_sd[i * sd + j] = sum;
        }
    }

    // Embed into state_dim x state_dim
    for i in 0..sd {
        for j in 0..sd {
            a_mat[i * state_dim + j] = a_sd[i * sd + j];
        }
    }
    // Fill remaining with small identity-like values
    for i in sd..state_dim {
        a_mat[i * state_dim + i] = 0.1;
    }

    // C matrix: identity-like mapping from state to observation
    let mut c_mat = vec![0.0; obs_dim * state_dim];
    for i in 0..obs_dim.min(state_dim) {
        c_mat[i * state_dim + i] = 1.0;
    }

    (a_mat, c_mat)
}

/// Compute observability rank: rank of [C; CA; CA^2; ...; CA^(n-1)]
fn observability_rank(
    a: &[f64], c: &[f64], state_dim: usize, obs_dim: usize,
) -> usize {
    let total_rows = obs_dim * state_dim;
    let mut obs_matrix = vec![0.0; total_rows * state_dim];

    // First block: C
    for i in 0..obs_dim {
        for j in 0..state_dim {
            obs_matrix[i * state_dim + j] = c[i * state_dim + j];
        }
    }

    // CA^k blocks
    let mut a_power = vec![0.0; state_dim * state_dim];
    // A^0 = I
    for i in 0..state_dim { a_power[i * state_dim + i] = 1.0; }

    for k in 1..state_dim {
        // A^k = A^(k-1) * A
        let mut new_power = vec![0.0; state_dim * state_dim];
        for i in 0..state_dim {
            for j in 0..state_dim {
                let mut sum = 0.0;
                for l in 0..state_dim {
                    sum += a_power[i * state_dim + l] * a[l * state_dim + j];
                }
                new_power[i * state_dim + j] = sum;
            }
        }
        a_power = new_power;

        // C * A^k
        let row_offset = k * obs_dim;
        for i in 0..obs_dim {
            for j in 0..state_dim {
                let mut sum = 0.0;
                for l in 0..state_dim {
                    sum += c[i * state_dim + l] * a_power[l * state_dim + j];
                }
                if (row_offset + i) * state_dim + j < obs_matrix.len() {
                    obs_matrix[(row_offset + i) * state_dim + j] = sum;
                }
            }
        }
    }

    // Rank via Gaussian elimination
    matrix_rank(&obs_matrix, total_rows, state_dim)
}

/// Matrix rank via Gaussian elimination with pivoting.
fn matrix_rank(mat: &[f64], rows: usize, cols: usize) -> usize {
    let mut work = mat.to_vec();
    let mut rank = 0;
    let mut pivot_col = 0;

    for row in 0..rows {
        if pivot_col >= cols { break; }

        // Find pivot
        let mut max_val = 0.0;
        let mut max_row = row;
        for r in row..rows {
            let v = work[r * cols + pivot_col].abs();
            if v > max_val { max_val = v; max_row = r; }
        }

        if max_val < 1e-10 {
            pivot_col += 1;
            continue;
        }

        // Swap rows
        if max_row != row {
            for j in 0..cols {
                work.swap(row * cols + j, max_row * cols + j);
            }
        }

        // Eliminate
        let pivot = work[row * cols + pivot_col];
        for r in (row + 1)..rows {
            let factor = work[r * cols + pivot_col] / pivot;
            for j in pivot_col..cols {
                let v = work[row * cols + j];
                work[r * cols + j] -= factor * v;
            }
        }

        rank += 1;
        pivot_col += 1;
    }

    rank
}

/// Controllability Gramian trace: tr(sum A^k * (A^k)^T) for k=0..N.
fn controllability_gramian_trace(a: &[f64], n: usize) -> f64 {
    let mut trace = 0.0;
    let mut a_power = vec![0.0; n * n];
    for i in 0..n { a_power[i * n + i] = 1.0; }

    for _ in 0..n {
        // Add trace of A^k * (A^k)^T = sum of squared entries of A^k
        for val in a_power.iter() {
            trace += val * val;
        }

        // A^(k+1) = A^k * A
        let mut new_power = vec![0.0; n * n];
        for i in 0..n {
            for j in 0..n {
                let mut sum = 0.0;
                for l in 0..n {
                    sum += a_power[i * n + l] * a[l * n + j];
                }
                new_power[i * n + j] = sum;
            }
        }
        a_power = new_power;
    }

    trace
}

/// Estimate eigenvalue magnitudes via power iteration.
fn estimate_eigenvalues(a: &[f64], n: usize) -> Vec<f64> {
    let mut magnitudes = Vec::new();

    // Deflated power iteration for up to n eigenvalues
    let mut work = a.to_vec();

    for _ in 0..n {
        let mut v = vec![1.0 / (n as f64).sqrt(); n];
        let mut eigenvalue = 0.0;

        for _ in 0..100 {
            // w = A * v
            let mut w = vec![0.0; n];
            for i in 0..n {
                for j in 0..n {
                    w[i] += work[i * n + j] * v[j];
                }
            }

            // Rayleigh quotient
            let mut numer = 0.0;
            let mut denom = 0.0;
            for i in 0..n {
                numer += w[i] * v[i];
                denom += v[i] * v[i];
            }
            eigenvalue = if denom > 1e-15 { numer / denom } else { 0.0 };

            // Normalize
            let norm: f64 = w.iter().map(|x| x * x).sum::<f64>().sqrt();
            if norm < 1e-15 { break; }
            for i in 0..n { v[i] = w[i] / norm; }
        }

        magnitudes.push(eigenvalue.abs());

        // Deflate: A <- A - lambda * v * v^T
        let mut v_final = vec![1.0 / (n as f64).sqrt(); n];
        let mut w = vec![0.0; n];
        for _ in 0..50 {
            for i in 0..n {
                w[i] = 0.0;
                for j in 0..n { w[i] += work[i * n + j] * v_final[j]; }
            }
            let norm: f64 = w.iter().map(|x| x * x).sum::<f64>().sqrt();
            if norm < 1e-15 { break; }
            for i in 0..n { v_final[i] = w[i] / norm; }
        }
        for i in 0..n {
            for j in 0..n {
                work[i * n + j] -= eigenvalue * v_final[i] * v_final[j];
            }
        }
    }

    magnitudes.sort_by(|a, b| b.partial_cmp(a).unwrap_or(std::cmp::Ordering::Equal));
    magnitudes
}

/// Hankel singular values from data (approximation via Hankel matrix SVD).
fn hankel_singular_values(data: &[f64], n: usize, d: usize, state_dim: usize) -> Vec<f64> {
    let _obs_dim = d.min(6);
    let block_rows = (n / 2).min(state_dim * 2);
    let block_cols = n - block_rows;

    if block_rows == 0 || block_cols == 0 { return Vec::new(); }

    // Build Hankel matrix from first feature
    let mut hankel = vec![0.0; block_rows * block_cols];
    for i in 0..block_rows {
        for j in 0..block_cols {
            let idx = (i + j) * d;
            if idx < data.len() {
                hankel[i * block_cols + j] = data[idx];
            }
        }
    }

    // Approximate singular values via H^T H eigenvalues
    let m = block_cols.min(state_dim);
    let mut hth = vec![0.0; m * m];
    for i in 0..m {
        for j in 0..m {
            let mut sum = 0.0;
            for k in 0..block_rows {
                if i < block_cols && j < block_cols {
                    sum += hankel[k * block_cols + i] * hankel[k * block_cols + j];
                }
            }
            hth[i * m + j] = sum;
        }
    }

    let eigs = estimate_eigenvalues(&hth, m);
    eigs.iter().map(|&e| e.max(0.0).sqrt()).collect()
}

/// Invert a small matrix via Gauss-Jordan.
fn invert_matrix(mat: &[f64], n: usize) -> Vec<f64> {
    let mut aug = vec![0.0; n * 2 * n];
    for i in 0..n {
        for j in 0..n {
            aug[i * 2 * n + j] = mat[i * n + j];
        }
        aug[i * 2 * n + n + i] = 1.0;
    }

    for col in 0..n {
        let mut max_row = col;
        let mut max_val = aug[col * 2 * n + col].abs();
        for row in (col + 1)..n {
            let v = aug[row * 2 * n + col].abs();
            if v > max_val { max_val = v; max_row = row; }
        }
        if max_val < 1e-14 { continue; }

        if max_row != col {
            for j in 0..2 * n {
                aug.swap(col * 2 * n + j, max_row * 2 * n + j);
            }
        }

        let pivot = aug[col * 2 * n + col];
        for j in 0..2 * n {
            aug[col * 2 * n + j] /= pivot;
        }

        for row in 0..n {
            if row == col { continue; }
            let factor = aug[row * 2 * n + col];
            for j in 0..2 * n {
                let v = aug[col * 2 * n + j];
                aug[row * 2 * n + j] -= factor * v;
            }
        }
    }

    let mut inv = vec![0.0; n * n];
    for i in 0..n {
        for j in 0..n {
            inv[i * n + j] = aug[i * 2 * n + n + j];
        }
    }
    inv
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_state_space_lens() {
        let n = 32;
        let d = 3;
        // Simple rotating system
        let mut data = Vec::with_capacity(n * d);
        for i in 0..n {
            let t = i as f64 * 0.1;
            data.push(t.cos());
            data.push(t.sin());
            data.push((-0.1 * t).exp());
        }
        let shared = SharedData::compute(&data, n, d);
        let result = StateSpaceObservabilityLens.scan(&data, n, d, &shared);
        assert!(result.contains_key("ss_observability_rank"));
        assert!(result["ss_observability_rank"][0] >= 1.0);
    }
}
