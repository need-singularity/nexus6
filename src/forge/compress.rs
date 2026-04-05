//! 반복 자기 압축 엔진.

use std::io::Write;
use std::path::{Path, PathBuf};
use std::process::Command;
use std::time::{SystemTime, UNIX_EPOCH};

use tracing::info;

const COMPRESS_PROMPT: &str = r#"You are a compression engine. Compress the following document into the MINIMUM number of tokens that YOU (Claude) can later decode back to the full original meaning.

Rules:
- The compressed output is ONLY for LLM consumption, not humans
- Use any symbols, abbreviations, shorthand, unicode, or encoding you want
- Preserve ALL semantic content — every rule, every detail, every nuance
- Structure markers (headers, lists) can be replaced with minimal delimiters
- Repeated patterns should use the shortest possible reference
- Output ONLY the compressed text, nothing else

Document:
---
{TEXT}
---"#;

const RECOMPRESS_PROMPT: &str = r#"You previously compressed a document into this form:

---
{TEXT}
---

Compress it FURTHER. Find any remaining redundancy and eliminate it.
Same rules: minimum tokens, preserve all meaning, LLM-only consumption.
Output ONLY the re-compressed text, nothing else."#;

#[derive(Debug, Clone)]
pub struct ForgeConfig {
    pub rounds: usize,
    pub convergence_threshold: f64,
    pub output_dir: Option<PathBuf>,
}

impl Default for ForgeConfig {
    fn default() -> Self {
        Self {
            rounds: 5,
            convergence_threshold: 0.01,
            output_dir: None,
        }
    }
}

#[derive(Debug, Clone, serde::Serialize)]
pub struct RoundResult {
    pub round: usize,
    pub chars: usize,
    pub r: f64,
    pub delta_r: f64,
}

#[derive(Debug, Clone, serde::Serialize)]
pub struct ForgeReport {
    pub run_id: String,
    pub original_chars: usize,
    pub rounds: Vec<RoundResult>,
    pub final_r: f64,
    pub final_chars: usize,
    pub converged_at: Option<usize>,
}

pub struct ForgeEngine;

impl ForgeEngine {
    /// claude CLI를 사용해 LLM 호출.
    fn llm_call(prompt: &str) -> Result<String, String> {
        // claude CLI 경로 탐색
        let cli = Self::find_claude_cli()
            .ok_or_else(|| "claude CLI를 찾을 수 없습니다".to_string())?;

        let output = Command::new(&cli)
            .arg("-p")
            .arg(prompt)
            .output()
            .map_err(|e| format!("claude 실행 실패: {}", e))?;

        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            return Err(format!("claude 오류: {}", stderr));
        }

        Ok(String::from_utf8_lossy(&output.stdout).trim().to_string())
    }

    fn find_claude_cli() -> Option<String> {
        // which claude
        if let Ok(output) = Command::new("which").arg("claude").output() {
            if output.status.success() {
                let path = String::from_utf8_lossy(&output.stdout).trim().to_string();
                if !path.is_empty() {
                    return Some(path);
                }
            }
        }
        // 알려진 경로
        for p in &[
            dirs::home_dir().map(|h| h.join(".local/bin/claude")),
            Some(PathBuf::from("/usr/local/bin/claude")),
            Some(PathBuf::from("/opt/homebrew/bin/claude")),
        ] {
            if let Some(path) = p {
                if path.is_file() {
                    return Some(path.to_string_lossy().to_string());
                }
            }
        }
        None
    }

    /// 반복 자기 압축 실행.
    pub fn compress(text: &str, config: &ForgeConfig) -> Result<ForgeReport, String> {
        let ts = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs();
        let run_id = format!("forge_{}", ts);

        let out_dir = config
            .output_dir
            .clone()
            .unwrap_or_else(|| PathBuf::from("bench/runs").join(&run_id));
        std::fs::create_dir_all(&out_dir)
            .map_err(|e| format!("디렉토리 생성 실패: {}", e))?;

        let original_chars = text.len();
        let mut results = Vec::new();
        let mut current = text.to_string();
        let mut converged_at = None;

        for i in 0..config.rounds {
            let prompt = if i == 0 {
                COMPRESS_PROMPT.replace("{TEXT}", &current)
            } else {
                RECOMPRESS_PROMPT.replace("{TEXT}", &current)
            };

            info!("Round {}/{}: 압축 중...", i + 1, config.rounds);
            let compressed = Self::llm_call(&prompt)?;
            let comp_chars = compressed.len();
            let r = comp_chars as f64 / original_chars as f64;
            let delta_r = if let Some(prev) = results.last() {
                (r - prev.r).abs()
            } else {
                1.0
            };

            // 저장
            let round_path = out_dir.join(format!("round_{}.tf", i));
            std::fs::write(&round_path, &compressed)
                .map_err(|e| format!("파일 저장 실패: {}", e))?;

            let result = RoundResult {
                round: i,
                chars: comp_chars,
                r: (r * 10000.0).round() / 10000.0,
                delta_r: (delta_r * 10000.0).round() / 10000.0,
            };

            println!(
                "  [Round {}] {} chars | r={:.4} | Δr={:.4}",
                i, comp_chars, r, delta_r
            );

            if i > 0 && delta_r < config.convergence_threshold {
                println!("  ★ 수렴 달성 (Δr < {}) at round {}", config.convergence_threshold, i);
                converged_at = Some(i);
                results.push(result);
                break;
            }

            results.push(result);
            current = compressed;
        }

        let last = results.last().unwrap();
        let report = ForgeReport {
            run_id: run_id.clone(),
            original_chars,
            rounds: results,
            final_r: last.r,
            final_chars: last.chars,
            converged_at,
        };

        // JSON 리포트 저장
        let report_json = serde_json::to_string_pretty(&report)
            .map_err(|e| format!("JSON 직렬화 실패: {}", e))?;
        std::fs::write(out_dir.join("report.json"), &report_json)
            .map_err(|e| format!("리포트 저장 실패: {}", e))?;

        Ok(report)
    }
}
