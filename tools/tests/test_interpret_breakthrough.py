import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from interpret_breakthrough import load_and_rank

FIX = Path(__file__).parent / "fixtures"

class TestInterpret(unittest.TestCase):
    def test_load_and_rank(self):
        result = load_and_rank(
            FIX / "sample_breakthrough.json",
            FIX / "sample_discovery.jsonl",
            min_strength=0.5,
        )
        # 3 patterns total, 2 above 0.5
        self.assertEqual(len(result), 2)
        # sorted by strength desc
        self.assertEqual(result[0]["name"], "reuse_dominance")
        self.assertGreater(result[0]["strength"], result[1]["strength"])
        # discovery note가 연결됨
        self.assertIn("note", result[0])

if __name__ == "__main__":
    unittest.main()
