//! 압축본 의미 보존 검증 엔진.

use super::compress::ForgeEngine;

const QA_PROMPT: &str = r#"You will test whether a compressed document preserves the meaning of the original.

ORIGINAL DOCUMENT:
---
{ORIGINAL}
---

COMPRESSED DOCUMENT:
---
{COMPRESSED}
---

Generate exactly 5 factual questions about the original document. For each question, answer it using ONLY the compressed document. Then judge if the compressed-based answer matches the original meaning.

Output format (exactly 5 lines, no other text):
Q1: [question] | A: [answer from compressed] | PASS or FAIL
Q2: [question] | A: [answer from compressed] | PASS or FAIL
Q3: [question] | A: [answer from compressed] | PASS or FAIL
Q4: [question] | A: [answer from compressed] | PASS or FAIL
Q5: [question] | A: [answer from compressed] | PASS or FAIL"#;

#[derive(Debug, Clone, serde::Serialize)]
pub struct VerifyResult {
    pub header_score: f64,
    pub qa_score: f64,
    pub loss: f64,
    pub pass: bool,
    pub qa_raw: String,
}

pub struct AnvilEngine;

impl AnvilEngine {
    /// 헤더 커버리지 측정.
    fn header_coverage(original: &str, compressed: &str) -> (usize, usize) {
        let headers: Vec<&str> = original
            .lines()
            .filter(|l| l.trim_start().starts_with('#'))
            .map(|l| l.trim_start_matches('#').trim())
            .collect();

        let compressed_lower = compressed.to_lowercase();
        let covered = headers
            .iter()
            .filter(|h| {
                let prefix: String = h.chars().take(20).collect();
                compressed_lower.contains(&prefix.to_lowercase())
            })
            .count();

        (covered, headers.len())
    }

    /// 압축본 검증: Q&A 5문제 + 헤더 커버리지.
    pub fn verify(compressed: &str, original: &str) -> Result<VerifyResult, String> {
        // 1. 헤더 커버리지
        let (covered, total_headers) = Self::header_coverage(original, compressed);
        let header_score = if total_headers > 0 {
            covered as f64 / total_headers as f64
        } else {
            1.0
        };

        println!("  헤더 커버리지: {}/{} = {:.2}", covered, total_headers, header_score);

        // 2. Q&A 테스트
        let prompt = QA_PROMPT
            .replace("{ORIGINAL}", original)
            .replace("{COMPRESSED}", compressed);

        let qa_result = ForgeEngine::llm_call(&prompt)?;
        println!("{}", qa_result);

        let pass_count = qa_result.matches("PASS").count();
        let total_q = 5;
        let qa_score = pass_count as f64 / total_q as f64;
        let loss = ((1.0 - qa_score) * 10000.0).round() / 10000.0;
        let passed = loss <= 0.05;

        println!();
        println!("=== 결과 ===");
        println!("Q&A 정답률:    {}/{} = {:.2}", pass_count, total_q, qa_score);
        println!("의미 손실도 L: {}", loss);
        println!("판정: {} (기준: L ≤ 0.05)", if passed { "PASS" } else { "FAIL" });

        Ok(VerifyResult {
            header_score: (header_score * 10000.0).round() / 10000.0,
            qa_score: (qa_score * 10000.0).round() / 10000.0,
            loss,
            pass: passed,
            qa_raw: qa_result,
        })
    }
}
