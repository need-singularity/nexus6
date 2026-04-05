import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from interpret_breakthrough import load_and_rank

FIX = Path(__file__).parent / "fixtures"

class TestInterpret(unittest.TestCase):
    def setUp(self):
        from interpret_breakthrough import reset_rule_counter
        reset_rule_counter()

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

    def test_translate_to_rule(self):
        from interpret_breakthrough import translate_to_rule
        pattern = {
            "name": "reuse_dominance", "strength": 0.82,
            "constants_matched": ["1/3"],
            "note": "tool repeat rate matches meta fixed point",
        }
        rule = translate_to_rule(pattern, source_hypothesis="H1")
        self.assertIn("R", rule["id"])
        self.assertIn("reuse_dominance", rule["rationale"])
        self.assertIn("0.82", rule["rationale"])
        self.assertIn("H1", rule["source"])
        self.assertTrue(len(rule["text"]) > 10)

    def test_translate_unknown_pattern_fallback(self):
        from interpret_breakthrough import translate_to_rule
        pattern = {"name": "unknown_xyz", "strength": 0.6, "constants_matched": []}
        rule = translate_to_rule(pattern, source_hypothesis="H?")
        self.assertIn("unknown_xyz", rule["text"])

    def test_render_rules_md_and_empty(self):
        from interpret_breakthrough import render_rules_md
        rules = [
            {"id": "R1", "text": "foo", "source": "H1", "rationale": "x"},
            {"id": "R2", "text": "bar", "source": "H2", "rationale": "y"},
        ]
        md = render_rules_md(rules, date_str="2026-04-05")
        self.assertIn("# 도출 규칙 후보", md)
        self.assertIn("R1", md)
        self.assertIn("foo", md)

        empty_md = render_rules_md([], date_str="2026-04-05")
        self.assertIn("패턴 없음", empty_md)

if __name__ == "__main__":
    unittest.main()
