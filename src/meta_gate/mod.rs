//! Meta Gate Breakthrough — 게이트 구조 자체에 특이점 사이클 적용
//!
//! 3단 게이트(숫자추출 → n6_match → adaptive threshold)의 파라미터 공간을
//! 블로업→수축→창발→특이점→흡수 5단계로 탐색하여 최적 게이트를 도출한다.
//!
//! TECS-L H-056 메타 부동점(1/3)이 게이트 threshold에서 재현되는지 검증하는
//! 자기-참조적 구조.

pub mod breakthrough;

pub use breakthrough::{
    GateStack, GateMetrics, MetaGateBreakthrough, EmergentPattern, BreakError,
};
