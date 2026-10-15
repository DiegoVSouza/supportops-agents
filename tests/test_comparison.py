import json
import tempfile
import unittest
from pathlib import Path

from supportops_agents.comparison import run_comparison


class ComparisonTests(unittest.TestCase):
    def test_emits_all_runner_slots_but_only_measured_core_behavior(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            run_comparison(Path(temp_dir))
            loaded = json.loads((Path(temp_dir) / "results.json").read_text(encoding="utf-8"))
        self.assertEqual(len(loaded["runners"]), 6)
        self.assertEqual(loaded["evaluation_metrics"], "PENDING")
        core = loaded["runners"][0]
        self.assertEqual(core["status"], "EXECUTED")
        self.assertTrue(all(row["status"] == "EXECUTED" for row in loaded["runners"]))
        self.assertTrue(all(case["contract_match"] for runner in loaded["runners"] for case in runner["cases"]))
        self.assertTrue(all(row["metrics"]["accuracy"] == "PENDING" for row in loaded["runners"]))


if __name__ == "__main__":
    unittest.main()
