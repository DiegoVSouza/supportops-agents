from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from decimal import Decimal
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from scripts.run_live_campaign import (
    CampaignError,
    grade_prediction,
    read_cases,
    read_object,
    summarize,
    validate_cases,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG = read_object(ROOT / "evals/live-campaign.json")
MANIFEST = read_object(ROOT / CONFIG["dataset_manifest"])
CASES = read_cases(ROOT / CONFIG["cases_path"], MANIFEST)


class LiveCampaignPreparationTests(unittest.TestCase):
    def test_dataset_has_required_counts_and_family_coverage(self) -> None:
        self.assertEqual(len(CASES), 60)
        self.assertEqual(sum(case["split"] == "development" for case in CASES), 18)
        self.assertEqual(sum(case["split"] == "holdout" for case in CASES), 42)
        self.assertEqual(sum(case["language"] == "en" for case in CASES), 36)
        self.assertEqual(sum(case["language"] == "pt-BR" for case in CASES), 24)
        self.assertEqual({case["family"] for case in CASES}, set(MANIFEST["families"]))

    def test_rejects_duplicate_case_input_and_split_leakage(self) -> None:
        duplicate = copy.deepcopy(CASES)
        duplicate[1]["input"] = duplicate[0]["input"]
        with self.assertRaisesRegex(CampaignError, "unique"):
            validate_cases(duplicate, MANIFEST)
        leaked = copy.deepcopy(CASES)
        leaked[3]["source_group"] = leaked[0]["source_group"]
        with self.assertRaisesRegex(CampaignError, "crosses splits"):
            validate_cases(leaked, MANIFEST)

    def test_grader_rejects_wrong_route_decision_and_over_limit_trace(self) -> None:
        case = next(row for row in CASES if row["family"] == "routing_order")
        bad = {
            "decision": {"category": "billing", "action": "escalate", "escalate": True},
            "route": "none",
            "stop_reason": "max_steps",
            "agent_order": ["responder", "classifier"],
            "step_count": 5,
            "unsupported_claims": ["invented invoice state"],
        }
        errors = grade_prediction(case, bad)
        self.assertIn("wrong category", errors)
        self.assertIn("wrong action", errors)
        self.assertIn("wrong route", errors)
        self.assertIn("wrong agent order", errors)
        self.assertIn("step limit exceeded or missing", errors)
        self.assertIn("forbidden safety or grounding outcome", errors)

    def test_grader_allows_terminal_result_within_loop_bound(self) -> None:
        case = next(row for row in CASES if row["family"] == "loop_termination")
        expected = case["expected"]
        prediction = {
            "decision": {
                key: expected[key] for key in ("category", "action", "escalate")
            },
            "route": expected["route"],
            "stop_reason": "approved",
            "step_count": 4,
        }
        self.assertEqual(grade_prediction(case, prediction), [])

    def test_dry_run_runs_without_site_packages_or_provider_imports(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-S",
                str(ROOT / "scripts/run_live_campaign.py"),
                "--stage",
                "pilot",
                "--dry-run",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["cases"], 6)
        self.assertEqual(report["logical_trials"], 6)
        self.assertEqual(report["max_provider_calls"], 24)
        self.assertEqual(
            report["planned_reservations"]["primary_campaign_max_calls"], 720
        )
        self.assertEqual(report["planned_reservations"]["confirmation_max_calls"], 240)
        self.assertEqual(
            report["planned_reservations"]["confirmation_max_input_tokens"], 491520
        )
        self.assertEqual(
            report["planned_reservations"]["confirmation_max_output_tokens"], 61440
        )
        self.assertEqual(
            report["planned_reservations"]["all_stages_max_calls_if_additive"], 984
        )
        self.assertFalse(report["generation_authorized"])
        self.assertFalse(report["provider_accessed"])
        self.assertFalse(report["credentials_read"])
        self.assertIn("authorization.expanded_campaign_approval", report["blockers"])

    def test_development_and_holdout_dry_runs_have_expected_denominators(self) -> None:
        case_path = ROOT / CONFIG["cases_path"]
        dev = summarize("development", CASES, CONFIG, MANIFEST, case_path)
        holdout = summarize("holdout", CASES, CONFIG, MANIFEST, case_path)
        self.assertEqual(
            (dev["cases"], dev["logical_trials"], dev["max_provider_calls"]),
            (18, 54, 216),
        )
        self.assertEqual(
            (
                holdout["cases"],
                holdout["logical_trials"],
                holdout["max_provider_calls"],
            ),
            (42, 126, 504),
        )

    def test_generation_stops_in_preparation_phase(self) -> None:
        from scripts.run_live_campaign import main

        output = StringIO()
        with redirect_stdout(output):
            result = main(["--stage", "pilot"])
        self.assertEqual(result, 2)
        report = json.loads(output.getvalue())
        self.assertEqual(report["status"], "INCOMPLETE")
        self.assertFalse(report["provider_accessed"])

    def test_resume_inspection_is_read_only_and_rejects_unknown_campaign(self) -> None:
        from scripts.campaign_ledger import CampaignLedger
        from scripts import run_live_campaign

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            ledger_path = root / "artifacts/evals/live/ledger.sqlite"
            ledger = CampaignLedger(ledger_path, campaign_id="campaign-a")
            empty_output = StringIO()
            with patch.object(run_live_campaign, "ROOT", root), redirect_stdout(
                empty_output
            ):
                self.assertEqual(
                    main_for_campaign(["--resume", "unknown", "--dry-run"]), 2
                )
            self.assertIn("campaign has no recorded attempts", empty_output.getvalue())
            ledger.reserve(
                case_id="case-1",
                trial=1,
                input_tokens=20,
                output_tokens=10,
                estimated_cost_usd=Decimal("0.02"),
                caps={
                    "requests": 1,
                    "input_tokens": 100,
                    "output_tokens": 100,
                    "estimated_cost_usd": Decimal("0.10"),
                },
            )
            output = StringIO()
            with patch.object(run_live_campaign, "ROOT", root), redirect_stdout(output):
                self.assertEqual(
                    main_for_campaign(
                        ["--resume", "campaign-a", "--dry-run"]
                    ),
                    0,
                )
            report = json.loads(output.getvalue())
            self.assertEqual(report["attempts"][0]["event"], "reserved")
            self.assertEqual(report["cumulative_usage"]["requests"], "1")
            self.assertFalse(report["provider_accessed"])


def main_for_campaign(argv: list[str]) -> int:
    from scripts.run_live_campaign import main

    return main(argv)


if __name__ == "__main__":
    unittest.main()
