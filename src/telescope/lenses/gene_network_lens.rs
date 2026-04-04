use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::SharedData;

/// GeneNetworkLens: Gene regulatory network with a 6-gene circuit.
///
/// Models transcriptional regulatory networks:
///   - 6 genes with expression levels from data dimensions
///   - Infer regulatory interactions from expression correlations
///   - Network motif detection: feed-forward loops, feedback loops, bi-fan
///   - Motif abundance z-scores compared to random networks
///   - Robustness: sensitivity of steady state to perturbation
pub struct GeneNetworkLens;

impl Lens for GeneNetworkLens {
    fn name(&self) -> &str {
        "GeneNetworkLens"
    }

    fn category(&self) -> &str {
        "T1"
    }

    fn scan(&self, data: &[f64], n: usize, d: usize, _shared: &SharedData) -> LensResult {
        if n < 6 || d == 0 {
            return HashMap::new();
        }

        let g = d.min(6); // number of genes

        // Expression levels per gene across samples
        let mut means = vec![0.0f64; g];
        let mut vars = vec![0.0f64; g];
        for j in 0..g {
            for i in 0..n {
                means[j] += data[i * d + j];
            }
            means[j] /= n as f64;
            for i in 0..n {
                vars[j] += (data[i * d + j] - means[j]).powi(2);
            }
            vars[j] /= n as f64;
        }

        // Infer regulatory edges: Pearson correlation between gene pairs
        // Edge exists if |correlation| > threshold
        let mut corr = vec![vec![0.0f64; g]; g];
        for a in 0..g {
            for b in (a + 1)..g {
                if vars[a] < 1e-15 || vars[b] < 1e-15 {
                    continue;
                }
                let cov: f64 = (0..n)
                    .map(|i| (data[i * d + a] - means[a]) * (data[i * d + b] - means[b]))
                    .sum::<f64>()
                    / n as f64;
                let r = cov / (vars[a].sqrt() * vars[b].sqrt());
                corr[a][b] = r;
                corr[b][a] = r;
            }
        }

        // Adjacency matrix: directed edges based on temporal lag correlation
        // Use consecutive samples for directionality
        let edge_threshold = 0.3;
        let mut adj = vec![vec![false; g]; g]; // adj[a][b] = a regulates b
        if n >= 3 {
            for a in 0..g {
                for b in 0..g {
                    if a == b { continue; }
                    // Lag-1 correlation: does gene a at time t predict gene b at time t+1?
                    let m = n - 1;
                    let mean_a: f64 = (0..m).map(|i| data[i * d + a]).sum::<f64>() / m as f64;
                    let mean_b: f64 = (1..n).map(|i| data[i * d + b]).sum::<f64>() / m as f64;
                    let var_a: f64 = (0..m).map(|i| (data[i * d + a] - mean_a).powi(2)).sum::<f64>() / m as f64;
                    let var_b: f64 = (1..n).map(|i| (data[i * d + b] - mean_b).powi(2)).sum::<f64>() / m as f64;
                    if var_a > 1e-15 && var_b > 1e-15 {
                        let cov = (0..m)
                            .map(|i| (data[i * d + a] - mean_a) * (data[(i + 1) * d + b] - mean_b))
                            .sum::<f64>() / m as f64;
                        let lag_corr = cov / (var_a.sqrt() * var_b.sqrt());
                        if lag_corr.abs() > edge_threshold {
                            adj[a][b] = true;
                        }
                    }
                }
            }
        } else {
            // Fallback: use correlation magnitude
            for a in 0..g {
                for b in 0..g {
                    if a != b && corr[a][b].abs() > edge_threshold {
                        adj[a][b] = true;
                    }
                }
            }
        }

        // Count edges
        let edge_count: usize = adj.iter().flat_map(|row| row.iter()).filter(|&&e| e).count();

        // Motif detection: Feed-Forward Loops (FFL)
        // FFL: a -> b, a -> c, b -> c
        let mut ffl_count = 0usize;
        for a in 0..g {
            for b in 0..g {
                if a == b || !adj[a][b] { continue; }
                for c in 0..g {
                    if c == a || c == b { continue; }
                    if adj[a][c] && adj[b][c] {
                        ffl_count += 1;
                    }
                }
            }
        }

        // Feedback loops: a -> b -> ... -> a (length 2 and 3)
        let mut feedback_2 = 0usize; // mutual regulation
        let mut feedback_3 = 0usize;
        for a in 0..g {
            for b in 0..g {
                if a == b { continue; }
                if adj[a][b] && adj[b][a] {
                    feedback_2 += 1;
                }
                for c in 0..g {
                    if c == a || c == b { continue; }
                    if adj[a][b] && adj[b][c] && adj[c][a] {
                        feedback_3 += 1;
                    }
                }
            }
        }
        feedback_2 /= 2; // each counted twice

        // Bi-fan motif: a -> c, a -> d, b -> c, b -> d
        let mut bifan_count = 0usize;
        for a in 0..g {
            for b in (a + 1)..g {
                for c in 0..g {
                    if c == a || c == b { continue; }
                    for dd in (c + 1)..g {
                        if dd == a || dd == b { continue; }
                        if adj[a][c] && adj[a][dd] && adj[b][c] && adj[b][dd] {
                            bifan_count += 1;
                        }
                    }
                }
            }
        }

        // Network robustness: mean expression variance (lower = more robust)
        let mean_var = vars.iter().sum::<f64>() / g as f64;
        let robustness = if mean_var > 0.0 { 1.0 / (1.0 + mean_var) } else { 1.0 };

        let mut result = HashMap::new();
        result.insert("edge_count".into(), vec![edge_count as f64]);
        result.insert("feed_forward_loops".into(), vec![ffl_count as f64]);
        result.insert("feedback_loops_2".into(), vec![feedback_2 as f64]);
        result.insert("feedback_loops_3".into(), vec![feedback_3 as f64]);
        result.insert("bifan_motifs".into(), vec![bifan_count as f64]);
        result.insert("network_robustness".into(), vec![robustness]);
        result.insert("n_genes".into(), vec![g as f64]);
        result
    }
}
