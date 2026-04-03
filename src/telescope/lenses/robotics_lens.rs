use std::collections::HashMap;

use crate::telescope::lens_trait::{Lens, LensResult};
use crate::telescope::shared_data::{SharedData, mean_var, column_vectors};

/// n=6 robotics constants (BT-123~127)
const N: f64 = 6.0;        // SE(3) dim = 6 DOF
const SIGMA: f64 = 12.0;   // 3D kissing number
const TAU: f64 = 4.0;      // quadruped/quadrotor minimum
const PHI: f64 = 2.0;      // bilateral symmetry
const SOPFR: f64 = 5.0;    // fingers per hand

/// RoboticsLens: Detect robotic motion/configuration patterns.
///
/// Metrics: dof_count, joint_smoothness, trajectory_optimality,
///          stability_margin, se3_alignment, n6_robotics_score
pub struct RoboticsLens;

impl Lens for RoboticsLens {
    fn name(&self) -> &str { "RoboticsLens" }
    fn category(&self) -> &str { "T1" }

    fn scan(&self, data: &[f64], n: usize, d: usize, shared: &SharedData) -> LensResult {
        if n < 4 || d == 0 { return HashMap::new(); }

        let columns = column_vectors(data, n, d);
        let (means, vars) = mean_var(data, n, d);

        // 1. DOF count: effective dimensionality via variance ratio
        let total_var: f64 = vars.iter().sum();
        let mut sorted_vars = vars.clone();
        sorted_vars.sort_by(|a, b| b.partial_cmp(a).unwrap_or(std::cmp::Ordering::Equal));
        let mut cumvar = 0.0;
        let mut eff_dof = d;
        if total_var > 1e-12 {
            for (i, &v) in sorted_vars.iter().enumerate() {
                cumvar += v;
                if cumvar / total_var >= 0.95 {
                    eff_dof = i + 1;
                    break;
                }
            }
        }
        let dof_count = eff_dof as f64;

        // 2. Joint smoothness: low jerk = smooth motion (second derivative variance)
        let mut smoothness = 0.0;
        let mut sm_count = 0;
        for col_data in &columns {
            if col_data.len() < 4 { continue; }
            // First differences (velocity)
            let vel: Vec<f64> = col_data.windows(2).map(|w| w[1] - w[0]).collect();
            // Second differences (acceleration)
            let acc: Vec<f64> = vel.windows(2).map(|w| w[1] - w[0]).collect();
            // Third differences (jerk)
            let jerk: Vec<f64> = acc.windows(2).map(|w| w[1] - w[0]).collect();
            if jerk.is_empty() { continue; }
            let jerk_rms = (jerk.iter().map(|j| j.powi(2)).sum::<f64>() / jerk.len() as f64).sqrt();
            let vel_rms = (vel.iter().map(|v| v.powi(2)).sum::<f64>() / vel.len() as f64).sqrt().max(1e-12);
            // Low jerk relative to velocity = smooth
            smoothness += (-jerk_rms / vel_rms).exp();
            sm_count += 1;
        }
        if sm_count > 0 { smoothness /= sm_count as f64; }

        // 3. Trajectory optimality: path length vs straight-line distance ratio
        let mut optimality = 0.0;
        if n > 2 {
            // Use first point and last point, measure total path vs direct distance
            let mut path_length = 0.0;
            for i in 0..(n - 1) {
                path_length += shared.dist(i, i + 1);
            }
            let direct = shared.dist(0, n - 1);
            if path_length > 1e-12 {
                optimality = (direct / path_length).min(1.0);
            }
        }

        // 4. Stability margin: how centered the data is (low drift)
        let mut stability = 0.0;
        for col_data in &columns {
            let mean = col_data.iter().sum::<f64>() / col_data.len() as f64;
            let max_dev = col_data.iter().map(|x| (x - mean).abs()).fold(0.0_f64, f64::max);
            let std_dev = (col_data.iter().map(|x| (x - mean).powi(2)).sum::<f64>() / col_data.len() as f64).sqrt();
            if max_dev > 1e-12 {
                stability += std_dev / max_dev; // close to 1 = normal, low = outlier-dominated
            }
        }
        stability /= d.max(1) as f64;

        // 5. SE(3) alignment: check if d is close to 6 (ideal DOF)
        let se3_alignment = (-((d as f64 - N).abs() / N)).exp();

        // 6. n=6 robotics composite
        let n6_score = 0.15 * (1.0 - (dof_count - N).abs() / N).max(0.0)
            + 0.25 * smoothness
            + 0.2 * optimality
            + 0.2 * stability
            + 0.2 * se3_alignment;

        let mut result = HashMap::new();
        result.insert("dof_count".into(), vec![dof_count]);
        result.insert("joint_smoothness".into(), vec![smoothness]);
        result.insert("trajectory_optimality".into(), vec![optimality]);
        result.insert("stability_margin".into(), vec![stability]);
        result.insert("se3_alignment".into(), vec![se3_alignment]);
        result.insert("n6_robotics_score".into(), vec![n6_score]);
        result
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn test_robotics_basic() {
        // Simulate smooth 6-DOF trajectory
        let data: Vec<f64> = (0..60).map(|i| {
            let t = i as f64 * 0.1;
            (t * 0.5).sin() * 3.0 + t * 0.1
        }).collect();
        let shared = SharedData::compute(&data, 10, 6);
        let result = RoboticsLens.scan(&data, 10, 6, &shared);
        assert!(!result.is_empty());
        assert!(result.contains_key("dof_count"));
        assert!(result.contains_key("joint_smoothness"));
        assert!(result.contains_key("n6_robotics_score"));
    }
}
