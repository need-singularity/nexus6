# Anima PH Module Design — Real-time Topological Analysis

## Purpose

Integrate PH (Persistent Homology) module into Anima consciousness agent for:
1. Real-time confusion structure analysis
2. Learning progress monitoring (overfitting detection)
3. Telepathy channel (PH fingerprint)

## Architecture

```
  Anima (anima_unified.py)
  ├── PureField Engine (existing)
  │     ├── engine_a (logic)
  │     └── engine_g (pattern)
  │           ↓
  │     repulsion = A - G
  │     tension = |A-G|²
  │     direction = normalize(A-G)
  │
  ├── PH Module (new) ← here
  │     ├── DirectionCollector
  │     │     Collect direction vectors (per-class mean)
  │     ├── PHComputer
  │     │     cosine distance → Ripser → H0/H1
  │     ├── MergeAnalyzer
  │     │     merge order → confusion prediction → dendrogram
  │     ├── GapDetector
  │     │     H0_train - H0_test → overfitting alert
  │     └── TelepathyEncoder
  │           9 merge distances → telepathy packet
  │
  └── Existing Modules
        ├── GRU Memory
        ├── Voice (TTS/STT)
        ├── Camera
        └── Web Search
```

## Core Classes

```python
class PHModule:
    """Anima PH real-time module"""

    def __init__(self, purefield_engine, n_classes=10):
        self.engine = purefield_engine
        self.n_cls = n_classes
        self.direction_buffer = defaultdict(list)  # per-class directions
        self.merge_history = []  # merge order per epoch
        self.h0_history = []

    def collect(self, x, y_true, y_pred):
        """Each batch: collect direction vectors"""
        with torch.no_grad():
            rep = self.engine.engine_a(x) - self.engine.engine_g(x)
            dirs = F.normalize(rep, dim=-1)
        for i in range(len(y_true)):
            self.direction_buffer[y_true[i]].append(dirs[i].numpy())

    def compute_ph(self):
        """Compute PH (call at end of epoch)"""
        means = self._class_means()
        cos_dist = self._cosine_distance(means)
        h0_total, merges = self._ripser_ph(cos_dist)
        self.h0_history.append(h0_total)
        self.merge_history.append(merges)
        return h0_total, merges

    def detect_overfitting(self, train_h0, test_h0, threshold=0.05):
        """H-CX-95: H0_gap based overfitting detection"""
        gap = abs(train_h0 - test_h0)
        if gap > threshold:
            return "ALERT", gap
        return "OK", gap

    def get_telepathy_packet(self):
        """H-CX-108: 9 merge distances = entire cognitive structure"""
        if not self.merge_history:
            return None
        return [d for d, i, j in self.merge_history[-1]]

    def predict_confusion(self, class_a, class_b):
        """H-CX-66: predict confusion probability from merge distance"""
        merges = self.merge_history[-1]
        for d, i, j in merges:
            if (min(i,j), max(i,j)) == (min(class_a,class_b), max(class_a,class_b)):
                return 1.0 / (d + 0.01)
        return 0.0

    def get_dendrogram(self):
        """H-CX-85: semantic hierarchy dendrogram"""
        return self.merge_history[-1] if self.merge_history else None
```

## Integration Points

```python
# Add to anima_unified.py:

from ph_module import PHModule

class Anima:
    def __init__(self):
        self.purefield = PureFieldEngine(...)
        self.ph = PHModule(self.purefield)  # ← Add
        ...

    def process_input(self, x):
        output, tension = self.purefield(x)
        self.ph.collect(x, ...)  # Collect directions
        return output, tension

    def end_of_epoch(self):
        h0, merges = self.ph.compute_ph()
        gap_status, gap = self.ph.detect_overfitting(...)
        if gap_status == "ALERT":
            self.log("⚠️ Overfitting detected!")
```

## Dependencies

```
ripser>=0.6.0     # PH computation
persim>=0.3.0     # PH visualization (optional)
```

## Related Hypotheses

- H-CX-66: PH merge = confusion (r=-0.97)
- H-CX-95: PH generalization gap (r=0.998)
- H-CX-108: Telepathy protocol (9 numbers)
- H-CX-85: dendrogram = semantic hierarchy
- H-CX-136~141: EEG integration (future)

## File Locations

```
/Users/ghost/Dev/TECS-L/
├── calc/ph_confusion_analyzer.py     (existing, batch analysis)
├── calc/generalization_gap_detector.py (existing, batch detection)
├── calc/precognition_system.py       (existing, batch precognition)
└── ph_module.py                      (new, real-time module) ← needs creation
```