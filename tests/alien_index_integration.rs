use nexus6::alien_index::{
    breakthrough_ratio, combine_signals, histogram, AlienIndex, AlienIndexRecord,
};

#[test]
fn closed_form_candidate_flow() {
    let mut rec = AlienIndexRecord::new("H-TEST-1", AlienIndex::new(0, 5));
    rec.update(AlienIndex::new(0, 7), "7-lens consensus").unwrap();
    rec.update(AlienIndex::new(0, 9), "n6_check EXACT").unwrap();
    rec.update(AlienIndex::new(0, 10), "proof committed").unwrap();
    assert!(rec.promotion_candidate);
    let child = rec.promote().unwrap();
    assert_eq!(child.current, AlienIndex::new(1, 0));
    assert!(!rec.promotion_candidate);
    assert_eq!(child.promoted_from.as_deref(), Some("H-TEST-1"));
}

#[test]
fn d_monotonic_enforced() {
    let mut rec = AlienIndexRecord::new("H-TEST-2", AlienIndex::new(1, 3));
    assert!(rec.update(AlienIndex::new(1, 2), "refutation").is_ok());
    assert!(rec.update(AlienIndex::new(0, 9), "nope").is_err());
}

#[test]
fn combine_signals_picks_max() {
    let r = combine_signals(Some(1.0), Some(3), Some("🟧"));
    assert_eq!(r, 9);
}

#[test]
fn breakthrough_ratio_on_synthetic_set() {
    let records: Vec<AlienIndexRecord> = (0..9)
        .map(|i| AlienIndexRecord::new(format!("X{i}"), AlienIndex::new(0, 5)))
        .chain(std::iter::once(AlienIndexRecord::new(
            "B",
            AlienIndex::new(1, 0),
        )))
        .collect();
    let ratio = breakthrough_ratio(&records);
    assert!((ratio - 0.1).abs() < 1e-9);
    let h = histogram(&records);
    assert_eq!(h.get(&(0, 5)).copied().unwrap_or(0), 9);
    assert_eq!(h.get(&(1, 0)).copied().unwrap_or(0), 1);
}
