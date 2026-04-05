//! 섹션별 정보 밀도 프로파일러.

use super::compress::ForgeEngine;

const SECTION_COMPRESS_PROMPT: &str = r#"Compress this to minimum tokens only you can decode. Preserve ALL meaning. Output ONLY compressed text:

---
{TEXT}
---"#;

#[derive(Debug, Clone, serde::Serialize)]
pub struct SectionResult {
    pub name: String,
    pub original_chars: usize,
    pub compressed_chars: usize,
    pub r: f64,
    pub grade: String,
}

#[derive(Debug, Clone, serde::Serialize)]
pub struct ProfileReport {
    pub sections: Vec<SectionResult>,
    pub total_original: usize,
    pub total_compressed: usize,
    pub overall_r: f64,
    pub skip_count: usize,
    pub skip_chars: usize,
}

pub struct Profiler;

impl Profiler {
    /// `##` 기준으로 섹션 분리.
    fn split_sections(text: &str) -> Vec<(String, String)> {
        let mut sections = Vec::new();
        let mut current_name = "HEADER".to_string();
        let mut current_body = String::new();

        for line in text.lines() {
            if line.starts_with("## ") {
                if !current_body.trim().is_empty() {
                    sections.push((current_name.clone(), current_body.trim().to_string()));
                }
                current_name = line.trim_start_matches('#').trim().to_string();
                current_body.clear();
            } else {
                current_body.push_str(line);
                current_body.push('\n');
            }
        }
        if !current_body.trim().is_empty() {
            sections.push((current_name, current_body.trim().to_string()));
        }

        sections
    }

    /// 섹션별 정보 밀도 측정.
    pub fn profile(text: &str) -> Result<ProfileReport, String> {
        let sections = Self::split_sections(text);
        let mut results = Vec::new();

        for (name, body) in &sections {
            let orig_chars = body.len();
            if orig_chars < 20 {
                continue;
            }

            let prompt = SECTION_COMPRESS_PROMPT.replace("{TEXT}", body);
            let compressed = ForgeEngine::llm_call(&prompt)?;
            let comp_chars = compressed.len();
            let r = (comp_chars as f64 / orig_chars as f64 * 10000.0).round() / 10000.0;

            let grade = if r > 0.35 {
                "HIGH"
            } else if r > 0.20 {
                "MED"
            } else if r > 0.10 {
                "LOW"
            } else {
                "SKIP"
            };

            let bar: String = "█".repeat((r * 30.0) as usize);
            println!(
                "  {:30} {:5}→{:5}  r={:.4}  {} [{}]",
                name, orig_chars, comp_chars, r, bar, grade
            );

            results.push(SectionResult {
                name: name.clone(),
                original_chars: orig_chars,
                compressed_chars: comp_chars,
                r,
                grade: grade.to_string(),
            });
        }

        let total_orig: usize = results.iter().map(|r| r.original_chars).sum();
        let total_comp: usize = results.iter().map(|r| r.compressed_chars).sum();
        let skip: Vec<&SectionResult> = results
            .iter()
            .filter(|r| r.grade == "SKIP" || r.grade == "LOW")
            .collect();
        let skip_chars: usize = skip.iter().map(|r| r.original_chars).sum();

        let overall_r = if total_orig > 0 {
            (total_comp as f64 / total_orig as f64 * 10000.0).round() / 10000.0
        } else {
            0.0
        };

        println!();
        println!(
            "전체: {}→{} chars (r={:.4})",
            total_orig, total_comp, overall_r
        );
        if !skip.is_empty() {
            println!(
                "삭제 후보 (LOW/SKIP): {}섹션, {} chars ({:.1}%)",
                skip.len(),
                skip_chars,
                skip_chars as f64 / total_orig as f64 * 100.0
            );
        }

        Ok(ProfileReport {
            sections: results,
            total_original: total_orig,
            total_compressed: total_comp,
            overall_r,
            skip_count: skip.len(),
            skip_chars,
        })
    }
}
