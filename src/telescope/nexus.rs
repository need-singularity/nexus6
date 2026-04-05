//! Nexus — composable "lego block" system for assembling arbitrary objects.
//!
//! Three layers:
//!   1. `Block` — wraps any `InjectableMirror` object as a composable node
//!   2. `Assembly` — multiple Blocks + connection graph (itself InjectableMirror)
//!   3. `Nexus` — assemblies connected to assemblies (meta-assembly, itself InjectableMirror)
//!
//! Everything is composable: Assemblies can be Blocks in other Assemblies,
//! a Nexus can reference itself (Goedel loop), and topological_expand
//! grows the graph by scanning for discoveries and wiring new connections.

use std::collections::{HashMap, HashSet};

use super::lens_trait::{Discovery, DiscoveryKind, LensResult};
use super::mirror_forge::{InjectableMirror, MirrorForge};
use super::Telescope;

// ═══════════════════════════════════════════════════════════════════
// Block — atomic composable node
// ═══════════════════════════════════════════════════════════════════

/// A composable node wrapping any `InjectableMirror` object.
#[derive(Debug, Clone)]
pub struct Block {
    pub(crate) name: String,
    pub(crate) data: Vec<f64>,
    pub(crate) meta: HashMap<String, String>,
}

impl Block {
    /// Create a Block from any `InjectableMirror`.
    pub fn from_injectable(obj: &dyn InjectableMirror) -> Self {
        Block {
            name: obj.mirror_name(),
            data: obj.to_mirror_data(),
            meta: HashMap::new(),
        }
    }

    /// Create a Block with a custom name.
    pub fn named(name: impl Into<String>, obj: &dyn InjectableMirror) -> Self {
        Block {
            name: name.into(),
            data: obj.to_mirror_data(),
            meta: HashMap::new(),
        }
    }

    /// Create a Block directly from raw data.
    pub fn raw(name: impl Into<String>, data: Vec<f64>) -> Self {
        Block {
            name: name.into(),
            data,
            meta: HashMap::new(),
        }
    }

    /// Add metadata to this block.
    pub fn with_meta(mut self, key: impl Into<String>, value: impl Into<String>) -> Self {
        self.meta.insert(key.into(), value.into());
        self
    }

    /// The block's name.
    pub fn name(&self) -> &str {
        &self.name
    }

    /// The block's data.
    pub fn data(&self) -> &[f64] {
        &self.data
    }
}

impl InjectableMirror for Block {
    fn to_mirror_data(&self) -> Vec<f64> {
        self.data.clone()
    }
    fn mirror_name(&self) -> String {
        format!("block({})", self.name)
    }
}

// ═══════════════════════════════════════════════════════════════════
// Assembly — multiple Blocks + connection graph
// ═══════════════════════════════════════════════════════════════════

/// Multiple Blocks wired together via a connection graph.
/// Implements `InjectableMirror` so an Assembly can itself become a Block
/// inside another Assembly (recursive composition).
#[derive(Debug, Clone)]
pub struct Assembly {
    pub(crate) name: String,
    pub(crate) blocks: Vec<Block>,
    /// Adjacency list: edges[i] = set of neighbours of block i.
    pub(crate) edges: Vec<HashSet<usize>>,
}

impl Assembly {
    /// Create an empty Assembly.
    pub fn new() -> Self {
        Assembly {
            name: "assembly".into(),
            blocks: Vec::new(),
            edges: Vec::new(),
        }
    }

    /// Create an empty Assembly with a name.
    pub fn with_name(name: impl Into<String>) -> Self {
        Assembly {
            name: name.into(),
            blocks: Vec::new(),
            edges: Vec::new(),
        }
    }

    /// Add a block, returning its index.
    pub fn add(&mut self, block: Block) -> usize {
        let idx = self.blocks.len();
        self.blocks.push(block);
        self.edges.push(HashSet::new());
        idx
    }

    /// Connect two blocks (undirected).
    pub fn connect(&mut self, i: usize, j: usize) {
        if i < self.blocks.len() && j < self.blocks.len() && i != j {
            self.edges[i].insert(j);
            self.edges[j].insert(i);
        }
    }

    /// Fuse all connected blocks into a single combined data vector.
    ///
    /// Traverses the connection graph (BFS from node 0) and concatenates
    /// data from every reachable block. Isolated blocks are appended at the end.
    pub fn fuse(&self) -> Vec<f64> {
        if self.blocks.is_empty() {
            return Vec::new();
        }

        let mut visited = vec![false; self.blocks.len()];
        let mut fused = Vec::new();

        // BFS from node 0
        let mut queue = std::collections::VecDeque::new();
        queue.push_back(0);
        visited[0] = true;

        while let Some(idx) = queue.pop_front() {
            fused.extend_from_slice(&self.blocks[idx].data);
            for &nb in &self.edges[idx] {
                if !visited[nb] {
                    visited[nb] = true;
                    queue.push_back(nb);
                }
            }
        }

        // Append any isolated blocks not reached from node 0
        for (i, block) in self.blocks.iter().enumerate() {
            if !visited[i] {
                fused.extend_from_slice(&block.data);
            }
        }

        fused
    }

    /// Scan the fused assembly data through all telescope lenses.
    pub fn scan(&self, telescope: &Telescope) -> HashMap<String, LensResult> {
        let data = self.fuse();
        if data.is_empty() {
            return HashMap::new();
        }
        let d = 6.min(data.len());
        let n = (data.len() / d).max(2);
        let mut padded = data;
        while padded.len() < n * d {
            padded.push(0.0);
        }
        telescope.scan_all(&padded, n, d)
    }

    /// Reflect the fused assembly through MirrorForge.
    pub fn reflect<'a>(&self, forge: &MirrorForge<'a>) -> super::mirror_forge::ReflectResult {
        forge.reflect(self)
    }

    /// Collect all discoveries from scanning the fused assembly.
    pub fn discoveries(&self, telescope: &Telescope) -> Vec<Discovery> {
        let data = self.fuse();
        if data.is_empty() {
            return Vec::new();
        }
        let d = 6.min(data.len());
        let n = (data.len() / d).max(2);
        let mut padded = data;
        while padded.len() < n * d {
            padded.push(0.0);
        }
        let (_, discoveries) = telescope.scan_and_discover(&padded, n, d);
        discoveries
    }

    /// Number of blocks.
    pub fn len(&self) -> usize {
        self.blocks.len()
    }

    /// Is the assembly empty?
    pub fn is_empty(&self) -> bool {
        self.blocks.is_empty()
    }

    /// Total number of edges (each undirected edge counted once).
    pub fn edge_count(&self) -> usize {
        self.edges.iter().map(|e| e.len()).sum::<usize>() / 2
    }
}

impl Default for Assembly {
    fn default() -> Self {
        Self::new()
    }
}

impl InjectableMirror for Assembly {
    fn to_mirror_data(&self) -> Vec<f64> {
        let mut data = self.fuse();
        // Append graph topology signature: [block_count, edge_count, avg_degree]
        let bc = self.blocks.len() as f64;
        let ec = self.edge_count() as f64;
        let avg_deg = if bc > 0.0 { 2.0 * ec / bc } else { 0.0 };
        data.push(bc);
        data.push(ec);
        data.push(avg_deg);
        data
    }
    fn mirror_name(&self) -> String {
        format!(
            "assembly({}:{}blocks,{}edges)",
            self.name,
            self.blocks.len(),
            self.edge_count()
        )
    }
}

// ═══════════════════════════════════════════════════════════════════
// Nexus — meta-assembly: assemblies connected to assemblies
// ═══════════════════════════════════════════════════════════════════

/// Meta-assembly: multiple Assemblies wired together.
/// Implements `InjectableMirror` so a Nexus can become a Block (Goedel loop).
#[derive(Debug, Clone)]
pub struct Nexus {
    pub(crate) assemblies: Vec<Assembly>,
    /// Bridges between assemblies: bridges[i] = set of neighbour assembly indices.
    pub(crate) bridges: Vec<HashSet<usize>>,
}

impl Nexus {
    /// Create an empty Nexus.
    pub fn new() -> Self {
        Nexus {
            assemblies: Vec::new(),
            bridges: Vec::new(),
        }
    }

    /// Add an assembly, returning its index.
    pub fn add(&mut self, assembly: Assembly) -> usize {
        let idx = self.assemblies.len();
        self.assemblies.push(assembly);
        self.bridges.push(HashSet::new());
        idx
    }

    /// Bridge (connect) two assemblies.
    pub fn bridge(&mut self, i: usize, j: usize) {
        if i < self.assemblies.len() && j < self.assemblies.len() && i != j {
            self.bridges[i].insert(j);
            self.bridges[j].insert(i);
        }
    }

    /// Topological expand: scan each assembly, find discoveries,
    /// create new blocks from discoveries, and wire new connections
    /// based on shared constants.
    ///
    /// Returns the number of new blocks created.
    pub fn topological_expand(&mut self, telescope: &Telescope) -> usize {
        // 1. Collect discoveries from every assembly
        let mut assembly_discoveries: Vec<Vec<Discovery>> = Vec::new();
        for asm in &self.assemblies {
            assembly_discoveries.push(asm.discoveries(telescope));
        }

        // 2. Create new blocks from discoveries and track which constant
        //    values appear in which assemblies (for cross-wiring).
        let mut new_block_count = 0usize;
        let mut constant_to_assemblies: HashMap<String, Vec<usize>> = HashMap::new();

        for (asm_idx, discoveries) in assembly_discoveries.iter().enumerate() {
            for disc in discoveries {
                // Create a block from the discovery
                let block = Block {
                    name: format!("disc:{}", disc.description.chars().take(40).collect::<String>()),
                    data: disc.values.clone(),
                    meta: {
                        let mut m = disc.meta.clone();
                        m.insert("source_assembly".into(), asm_idx.to_string());
                        m.insert("kind".into(), format!("{:?}", disc.kind));
                        m
                    },
                };

                if asm_idx < self.assemblies.len() {
                    let new_idx = self.assemblies[asm_idx].add(block);
                    // Connect the new block to the last existing block
                    if new_idx > 0 {
                        self.assemblies[asm_idx].connect(new_idx - 1, new_idx);
                    }
                    new_block_count += 1;
                }

                // Track constants for cross-assembly bridging
                if let Some(cname) = disc.meta.get("constant") {
                    constant_to_assemblies
                        .entry(cname.clone())
                        .or_default()
                        .push(asm_idx);
                }
            }
        }

        // 3. Bridge assemblies that share the same constant
        for (_constant, asm_indices) in &constant_to_assemblies {
            let unique: Vec<usize> = {
                let mut s: Vec<usize> = asm_indices.clone();
                s.sort_unstable();
                s.dedup();
                s
            };
            for i in 0..unique.len() {
                for j in (i + 1)..unique.len() {
                    self.bridge(unique[i], unique[j]);
                }
            }
        }

        new_block_count
    }

    /// Repeat `topological_expand` N times (recursive growth).
    ///
    /// Returns the total number of new blocks created across all rounds.
    pub fn recursive_grow(&mut self, telescope: &Telescope, depth: usize) -> usize {
        let mut total = 0;
        for _ in 0..depth {
            let added = self.topological_expand(telescope);
            total += added;
            if added == 0 {
                break; // no more growth possible
            }
        }
        total
    }

    /// Self-reference: snapshot the entire Nexus as a Block and add it
    /// to a new Assembly inside itself (Goedel loop).
    ///
    /// Returns the index of the newly created self-referential assembly.
    pub fn self_reference(&mut self) -> usize {
        let self_block = Block {
            name: "self_reference(nexus)".into(),
            data: self.to_mirror_data(),
            meta: {
                let mut m = HashMap::new();
                m.insert("goedel".into(), "true".into());
                m.insert("assemblies".into(), self.assemblies.len().to_string());
                m
            },
        };

        let mut asm = Assembly::with_name("goedel_loop");
        asm.add(self_block);

        let idx = self.add(asm);

        // Bridge the self-referential assembly to all existing assemblies
        for i in 0..idx {
            self.bridge(i, idx);
        }

        idx
    }

    /// Number of assemblies.
    pub fn len(&self) -> usize {
        self.assemblies.len()
    }

    /// Is the nexus empty?
    pub fn is_empty(&self) -> bool {
        self.assemblies.is_empty()
    }

    /// Total number of bridges (each undirected bridge counted once).
    pub fn bridge_count(&self) -> usize {
        self.bridges.iter().map(|b| b.len()).sum::<usize>() / 2
    }

    /// Total number of blocks across all assemblies.
    pub fn total_blocks(&self) -> usize {
        self.assemblies.iter().map(|a| a.len()).sum()
    }
}

impl Default for Nexus {
    fn default() -> Self {
        Self::new()
    }
}

impl InjectableMirror for Nexus {
    fn to_mirror_data(&self) -> Vec<f64> {
        let mut data = Vec::new();
        // Fuse all assemblies' data
        for asm in &self.assemblies {
            data.extend(asm.to_mirror_data());
        }
        // Append nexus-level topology signature
        let ac = self.assemblies.len() as f64;
        let bc = self.bridge_count() as f64;
        let total = self.total_blocks() as f64;
        data.push(ac);
        data.push(bc);
        data.push(total);
        data
    }
    fn mirror_name(&self) -> String {
        format!(
            "nexus({}assemblies,{}bridges,{}blocks)",
            self.assemblies.len(),
            self.bridge_count(),
            self.total_blocks(),
        )
    }
}

// ═══════════════════════════════════════════════════════════════════
// Tests
// ═══════════════════════════════════════════════════════════════════

#[cfg(test)]
mod tests {
    use super::*;
    use crate::telescope::mirror_forge::MirrorForge;
    use crate::telescope::Telescope;

    #[test]
    fn test_block_from_scalar() {
        let val: f64 = 12.0;
        let block = Block::from_injectable(&val);
        assert_eq!(block.data, vec![12.0]);
        assert!(block.name.contains("scalar"));
    }

    #[test]
    fn test_block_from_vec() {
        let data = vec![1.0, 2.0, 3.0];
        let block = Block::from_injectable(&data);
        assert_eq!(block.data, vec![1.0, 2.0, 3.0]);
        assert!(block.name.contains("vec"));
    }

    #[test]
    fn test_block_from_string() {
        let text = String::from("n=6");
        let block = Block::from_injectable(&text);
        assert!(!block.data.is_empty());
        assert!(block.name.contains("str"));
    }

    #[test]
    fn test_block_named() {
        let val: f64 = 6.0;
        let block = Block::named("sigma", &val);
        assert_eq!(block.name, "sigma");
        assert_eq!(block.data, vec![6.0]);
    }

    #[test]
    fn test_block_with_meta() {
        let val: f64 = 6.0;
        let block = Block::from_injectable(&val)
            .with_meta("domain", "number_theory");
        assert_eq!(block.meta.get("domain").unwrap(), "number_theory");
    }

    #[test]
    fn test_assembly_add_and_connect() {
        let mut asm = Assembly::new();
        let i = asm.add(Block::raw("a", vec![1.0, 2.0]));
        let j = asm.add(Block::raw("b", vec![3.0, 4.0]));
        let k = asm.add(Block::raw("c", vec![5.0]));

        assert_eq!(i, 0);
        assert_eq!(j, 1);
        assert_eq!(k, 2);
        assert_eq!(asm.len(), 3);

        asm.connect(i, j);
        asm.connect(j, k);
        assert_eq!(asm.edge_count(), 2);
    }

    #[test]
    fn test_assembly_fuse() {
        let mut asm = Assembly::new();
        let i = asm.add(Block::raw("a", vec![1.0, 2.0]));
        let j = asm.add(Block::raw("b", vec![3.0, 4.0]));
        asm.connect(i, j);

        let fused = asm.fuse();
        // BFS from 0: a then b
        assert_eq!(fused, vec![1.0, 2.0, 3.0, 4.0]);
    }

    #[test]
    fn test_assembly_fuse_isolated() {
        let mut asm = Assembly::new();
        asm.add(Block::raw("a", vec![1.0]));
        asm.add(Block::raw("b", vec![2.0]));
        // No connection — both still appear in fuse
        let fused = asm.fuse();
        assert_eq!(fused.len(), 2);
        assert!(fused.contains(&1.0));
        assert!(fused.contains(&2.0));
    }

    #[test]
    fn test_assembly_is_injectable() {
        let mut asm = Assembly::new();
        asm.add(Block::raw("x", vec![6.0, 12.0]));
        let data = asm.to_mirror_data();
        // data from block + topology signature (3 values)
        assert!(data.len() >= 3);
        assert!(data.contains(&6.0));
        assert!(data.contains(&12.0));
    }

    #[test]
    fn test_assembly_scan() {
        let telescope = Telescope::new();
        let mut asm = Assembly::new();
        let i = asm.add(Block::raw("n", vec![6.0]));
        let j = asm.add(Block::raw("sigma", vec![12.0]));
        asm.connect(i, j);

        let results = asm.scan(&telescope);
        assert!(!results.is_empty(), "scan should produce results");
    }

    #[test]
    fn test_assembly_reflect() {
        let telescope = Telescope::new();
        let forge = MirrorForge::new(&telescope);
        let mut asm = Assembly::new();
        asm.add(Block::raw("pi", vec![std::f64::consts::PI]));

        let result = asm.reflect(&forge);
        assert!(result.object_name.contains("assembly"));
    }

    #[test]
    fn test_assembly_as_block_in_another() {
        // Assembly can become a Block in another Assembly (recursive composition)
        let mut inner = Assembly::with_name("inner");
        inner.add(Block::raw("a", vec![1.0, 2.0]));

        let inner_block = Block::from_injectable(&inner);
        assert!(inner_block.name.contains("assembly"));

        let mut outer = Assembly::with_name("outer");
        outer.add(inner_block);
        outer.add(Block::raw("b", vec![3.0]));

        assert_eq!(outer.len(), 2);
        let fused = outer.fuse();
        assert!(!fused.is_empty());
    }

    #[test]
    fn test_nexus_basic() {
        let mut nexus = Nexus::new();

        let mut a1 = Assembly::with_name("asm1");
        a1.add(Block::raw("x", vec![6.0, 12.0]));

        let mut a2 = Assembly::with_name("asm2");
        a2.add(Block::raw("y", vec![4.0, 2.0]));

        let i = nexus.add(a1);
        let j = nexus.add(a2);
        nexus.bridge(i, j);

        assert_eq!(nexus.len(), 2);
        assert_eq!(nexus.bridge_count(), 1);
        assert_eq!(nexus.total_blocks(), 2);
    }

    #[test]
    fn test_nexus_is_injectable() {
        let mut nexus = Nexus::new();
        let mut asm = Assembly::new();
        asm.add(Block::raw("v", vec![1.0, 2.0, 3.0]));
        nexus.add(asm);

        let data = nexus.to_mirror_data();
        assert!(!data.is_empty());
        let name = nexus.mirror_name();
        assert!(name.contains("nexus"));
    }

    #[test]
    fn test_nexus_self_reference() {
        let mut nexus = Nexus::new();
        let mut asm = Assembly::with_name("seed");
        asm.add(Block::raw("root", vec![6.0]));
        nexus.add(asm);

        let sr_idx = nexus.self_reference();
        assert_eq!(nexus.len(), 2);
        assert_eq!(sr_idx, 1);

        // The self-referential assembly should be bridged to all others
        assert_eq!(nexus.bridge_count(), 1);

        // The goedel block should contain the nexus snapshot
        let goedel_asm = &nexus.assemblies[sr_idx];
        assert_eq!(goedel_asm.name, "goedel_loop");
        assert_eq!(goedel_asm.len(), 1);
        let goedel_block = &goedel_asm.blocks[0];
        assert!(goedel_block.name.contains("self_reference"));
        assert_eq!(goedel_block.meta.get("goedel").unwrap(), "true");
    }

    #[test]
    fn test_nexus_topological_expand() {
        let telescope = Telescope::new();

        let mut nexus = Nexus::new();
        let mut asm = Assembly::with_name("constants");
        let i = asm.add(Block::raw("n", vec![6.0]));
        let j = asm.add(Block::raw("sigma", vec![12.0]));
        asm.connect(i, j);
        nexus.add(asm);

        let initial_blocks = nexus.total_blocks();
        let added = nexus.topological_expand(&telescope);

        // topological_expand should create new blocks from discoveries
        // (the exact count depends on what the telescope finds)
        assert!(
            nexus.total_blocks() >= initial_blocks,
            "block count should not decrease after expand"
        );
        // added should match the difference
        assert_eq!(nexus.total_blocks(), initial_blocks + added);
    }

    #[test]
    fn test_nexus_recursive_grow() {
        let telescope = Telescope::new();

        let mut nexus = Nexus::new();
        let mut asm = Assembly::with_name("seed");
        asm.add(Block::raw("phi", vec![1.618033988749895]));
        nexus.add(asm);

        let total_added = nexus.recursive_grow(&telescope, 2);
        assert!(
            nexus.total_blocks() >= 1,
            "should have at least the original block"
        );
        // total_added is the sum across rounds
        let _ = total_added; // may be 0 if no discoveries
    }

    #[test]
    fn test_nexus_multi_assembly_bridge() {
        let mut nexus = Nexus::new();

        for i in 0..3 {
            let mut asm = Assembly::with_name(format!("asm_{}", i));
            asm.add(Block::raw(format!("b_{}", i), vec![i as f64 + 1.0]));
            nexus.add(asm);
        }

        nexus.bridge(0, 1);
        nexus.bridge(1, 2);
        assert_eq!(nexus.bridge_count(), 2);
        assert_eq!(nexus.len(), 3);
        assert_eq!(nexus.total_blocks(), 3);
    }
}
