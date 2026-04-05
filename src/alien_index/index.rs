use serde::{Deserialize, Serialize};

/// Alien Index: `(d, r)` pair.
///
/// - `d`: cycle depth (how many blowup→absorption cycles have closed on this object)
/// - `r`: rank within depth `d`, clamped to `0..=10`
///
/// `r == 10` at depth `d` means the object has reached the "closed-form ceiling"
/// of that depth and is eligible for breakthrough to `(d+1, 0)`.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub struct AlienIndex {
    pub d: u32,
    pub r: u8,
}

impl AlienIndex {
    /// Construct an index, clamping `r` to `0..=10`.
    pub const fn new(d: u32, r: u8) -> Self {
        let r = if r > 10 { 10 } else { r };
        Self { d, r }
    }

    /// True iff `r == 10` (promotion eligible).
    pub const fn can_promote(&self) -> bool {
        self.r == 10
    }

    /// Promote `(d, 10) → (d+1, 0)`. Returns `None` if `r != 10`.
    pub fn breakthrough(&self) -> Option<AlienIndex> {
        if self.can_promote() {
            Some(AlienIndex::new(self.d + 1, 0))
        } else {
            None
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn new_clamps_rank_to_ten() {
        let ai = AlienIndex::new(0, 10);
        assert_eq!(ai.d, 0);
        assert_eq!(ai.r, 10);
    }

    #[test]
    fn new_rejects_rank_above_ten() {
        let ai = AlienIndex::new(0, 42);
        assert_eq!(ai.r, 10);
    }

    #[test]
    fn can_promote_only_when_r_is_ten() {
        assert!(AlienIndex::new(0, 10).can_promote());
        assert!(!AlienIndex::new(0, 9).can_promote());
        assert!(AlienIndex::new(3, 10).can_promote());
    }

    #[test]
    fn breakthrough_increments_depth_and_resets_rank() {
        let ai = AlienIndex::new(1, 10);
        let next = ai.breakthrough().unwrap();
        assert_eq!(next.d, 2);
        assert_eq!(next.r, 0);
    }

    #[test]
    fn breakthrough_none_when_not_at_ten() {
        assert!(AlienIndex::new(0, 9).breakthrough().is_none());
    }

    #[test]
    fn ordering_d_then_r() {
        assert!(AlienIndex::new(0, 10) < AlienIndex::new(1, 0));
        assert!(AlienIndex::new(0, 5) < AlienIndex::new(0, 6));
    }
}
