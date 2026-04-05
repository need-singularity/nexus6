//! token-forge: LLM 자기 압축 엔진
//!
//! `nexus6 forge compress <file>` — 반복 자기 압축
//! `nexus6 forge verify <compressed> --original <file>` — 의미 보존 검증
//! `nexus6 forge profile <file>` — 섹션별 정보 밀도 분석

pub mod compress;
pub mod anvil;
pub mod profiler;

pub use compress::ForgeEngine;
pub use anvil::AnvilEngine;
pub use profiler::Profiler;
