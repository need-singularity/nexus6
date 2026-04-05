/// Map `n6_match` quality (1.0 EXACT / 0.8 CLOSE / 0.5 WEAK / 0.0) to `r`.
/// Per spec: EXACT → 9, CLOSE → 7, WEAK → 5, NONE → 0.
pub fn rank_from_n6_quality(quality: f64) -> u8 {
    if quality >= 1.0 { 9 }
    else if quality >= 0.8 { 7 }
    else if quality >= 0.5 { 5 }
    else { 0 }
}

/// Map lens consensus count to `r`:
/// 1 lens → 3, 3 lenses → 6, 7 lenses → 7, 12+ lenses → 8.
pub fn rank_from_lens_consensus(count: u32) -> u8 {
    if count >= 12 { 8 }
    else if count >= 7 { 7 }
    else if count >= 3 { 6 }
    else if count >= 1 { 3 }
    else { 0 }
}

/// Parse a MATH_ATLAS grade emoji token to `r`.
/// Returns `None` for unknown / `"-"` / empty.
pub fn rank_from_grade(grade: &str) -> Option<u8> {
    let g = grade.trim();
    if g.is_empty() || g == "-" || g == "none" { return None; }
    if g.starts_with("⬜") { return Some(0); }
    if g == "⚪" { return Some(1); }
    if g == "🟥" { return Some(2); }
    if g == "🟥★" { return Some(3); }
    if g.starts_with("🟥★★") { return Some(4); }
    if g == "🟦" { return Some(5); }
    if g == "🟧" { return Some(6); }
    if g == "🟧★" { return Some(7); }
    if g.starts_with("🟧★★") { return Some(8); }
    if g == "🟩" { return Some(9); }
    None
}

/// Take the strongest signal. `r = max(all available)`.
pub fn combine_signals(
    n6_quality: Option<f64>,
    lens_consensus: Option<u32>,
    grade: Option<&str>,
) -> u8 {
    let r_n6 = n6_quality.map(rank_from_n6_quality).unwrap_or(0);
    let r_lens = lens_consensus.map(rank_from_lens_consensus).unwrap_or(0);
    let r_grade = grade.and_then(rank_from_grade).unwrap_or(0);
    r_n6.max(r_lens).max(r_grade)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn rank_from_n6_quality_exact_is_nine() {
        assert_eq!(rank_from_n6_quality(1.0), 9);
    }

    #[test]
    fn rank_from_n6_quality_close_is_seven() {
        assert_eq!(rank_from_n6_quality(0.8), 7);
    }

    #[test]
    fn rank_from_n6_quality_weak_is_five() {
        assert_eq!(rank_from_n6_quality(0.5), 5);
    }

    #[test]
    fn rank_from_n6_quality_none_is_zero() {
        assert_eq!(rank_from_n6_quality(0.0), 0);
    }

    #[test]
    fn rank_from_lens_consensus_thresholds() {
        assert_eq!(rank_from_lens_consensus(0), 0);
        assert_eq!(rank_from_lens_consensus(1), 3);
        assert_eq!(rank_from_lens_consensus(3), 6);
        assert_eq!(rank_from_lens_consensus(7), 7);
        assert_eq!(rank_from_lens_consensus(12), 8);
        assert_eq!(rank_from_lens_consensus(99), 8);
    }

    #[test]
    fn rank_from_grade_known_tokens() {
        assert_eq!(rank_from_grade("🟩"), Some(9));
        assert_eq!(rank_from_grade("🟧★★★"), Some(8));
        assert_eq!(rank_from_grade("🟧★★"), Some(8));
        assert_eq!(rank_from_grade("🟧★"), Some(7));
        assert_eq!(rank_from_grade("🟧"), Some(6));
        assert_eq!(rank_from_grade("🟦"), Some(5));
        assert_eq!(rank_from_grade("⚪"), Some(1));
        assert_eq!(rank_from_grade("🟥"), Some(2));
        assert_eq!(rank_from_grade("🟥★"), Some(3));
        assert_eq!(rank_from_grade("🟥★★"), Some(4));
        assert_eq!(rank_from_grade("🟥★★★★"), Some(4));
        assert_eq!(rank_from_grade("⬜ UNTESTED"), Some(0));
        assert_eq!(rank_from_grade("-"), None);
        assert_eq!(rank_from_grade(""), None);
    }

    #[test]
    fn combined_takes_max_of_signals() {
        let r = combine_signals(Some(1.0), Some(3), None);
        assert_eq!(r, 9);
        let r = combine_signals(None, None, Some("🟩"));
        assert_eq!(r, 9);
        assert_eq!(combine_signals(None, None, None), 0);
    }
}
