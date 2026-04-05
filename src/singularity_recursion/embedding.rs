//! Simhash-based embedding of singularity invariants.
//!
//! 128-bit simhash via blake3 per n-gram, converted to a 16-dim f32 vector.
//! Distance = Hamming(simhash_a, simhash_b) / 128, range [0, 1].

use blake3::Hasher;

/// Compute a 128-bit simhash of a text.
/// Tokens = whitespace-split, n-grams of 1..=3.
pub fn simhash(text: &str) -> u128 {
    let tokens: Vec<&str> = text.split_whitespace().collect();
    if tokens.is_empty() { return 0; }

    let mut v = [0i32; 128];
    for n in 1..=3.min(tokens.len()) {
        for window in tokens.windows(n) {
            let ngram = window.join(" ");
            let mut h = Hasher::new();
            h.update(ngram.as_bytes());
            let hash = h.finalize();
            let bytes = hash.as_bytes(); // 32 bytes
            let val: u128 = u128::from_le_bytes(bytes[..16].try_into().unwrap());
            for i in 0..128 {
                if (val >> i) & 1 == 1 { v[i] += 1; } else { v[i] -= 1; }
            }
        }
    }

    let mut out: u128 = 0;
    for i in 0..128 { if v[i] > 0 { out |= 1u128 << i; } }
    out
}

/// Convert a 128-bit simhash to a 16-dim f32 vector (bit-group counts normalized).
pub fn to_vector(h: u128) -> [f32; 16] {
    let mut out = [0.0f32; 16];
    for g in 0..16 {
        let byte = ((h >> (g * 8)) & 0xFF) as u8;
        out[g] = (byte.count_ones() as f32) / 8.0;
    }
    out
}

/// Hamming-based similarity distance in [0, 1]. 0 = identical.
pub fn distance(a: u128, b: u128) -> f32 {
    (a ^ b).count_ones() as f32 / 128.0
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn identical_text_zero_distance() {
        let h = simhash("one-shot process append-only WAL crash-safe infinite");
        assert_eq!(distance(h, h), 0.0);
    }

    #[test]
    fn similar_texts_small_distance() {
        let a = simhash("crash-safe infinite singularity recursion via launchd");
        let b = simhash("crash-safe infinite singularity recursion via launchctl");
        assert!(distance(a, b) < 0.5, "similar texts too far: {}", distance(a, b));
    }

    #[test]
    fn different_texts_large_distance() {
        let a = simhash("banana quantum chromodynamics");
        let b = simhash("fourier transform filesystem lock");
        assert!(distance(a, b) > 0.3, "different texts too close: {}", distance(a, b));
    }

    #[test]
    fn distance_bounded_unit_interval() {
        let a = simhash("alpha");
        let b = simhash("bravo");
        let d = distance(a, b);
        assert!((0.0..=1.0).contains(&d));
    }

    #[test]
    fn to_vector_bounded() {
        let v = to_vector(u128::MAX);
        for x in v.iter() { assert!((0.0..=1.0).contains(x)); }
    }

    #[test]
    fn empty_text_zero_hash() {
        assert_eq!(simhash(""), 0);
    }
}
