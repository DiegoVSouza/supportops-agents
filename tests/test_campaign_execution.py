from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from typing import Any

from scripts import campaign_execution as ex
from scripts.campaign_ledger import CampaignLedger

ROOT = Path(__file__).resolve().parents[1]
CASES = [
    json.loads(line)
    for line in (ROOT / "evals/datasets/live-v1/cases.jsonl").read_text(encoding="utf-8").splitlines()
    if line.strip()
]


def no_sleep(_seconds: float) -> None:
    return None


class BrokenTransport:
    """Fixture transport that returns one canned reply (or raises) instead of a perfect model."""

    provenance = "fixture"

    def __init__(self, reply: dict[str, Any] | None = None, error: Exception | None = None):
        self.reply, self.error = reply, error
        self.calls = 0

    def request(self, envelope: dict[str, Any]) -> dict[str, Any]:
        self.calls += 1
        if self.error:
            raise self.error
        return self.reply  # type: ignore[return-value]

    def usage_for(self, case_id: str) -> dict[str, int]:
        return {"calls": self.calls, "input_tokens": 100 * self.calls, "output_tokens": 40 * self.calls}


class ExecutionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.out = Path(self.temp.name) / "run"

    def run_campaign(self, transport: Any, max_trials: int, reader=None):
        return ex.execute_campaign(
            cases=CASES, runner=ex.FixtureTrialRunner(transport), out_dir=self.out,
            ledger_path=self.out / "ledger.sqlite", usage_reader=reader or transport.usage_for,
            max_trials=max_trials, min_gap_seconds=0, sleep=no_sleep,
        )

    def trials(self) -> list[dict[str, Any]]:
        return ex.read_jsonl(self.out / "trials.jsonl")

    def oracle(self) -> ex.OracleTransport:
        return ex.OracleTransport({c["case_id"]: c for c in CASES})

    def test_pilot_cases_run_first_and_cover_four_distinct_families(self) -> None:
        order = [c["case_id"] for c in ex.ordered_cases(CASES)]
        self.assertEqual(order[:4], list(ex.PILOT_IDS))
        self.assertEqual(len(order), 18)
        self.assertEqual(len({c["family"] for c in ex.ordered_cases(CASES)[:4]}), 4)
        self.assertTrue(all(c["split"] == "development" for c in ex.ordered_cases(CASES)))

    def test_full_fixture_run_passes_every_case_and_stays_content_free(self) -> None:
        transport = self.oracle()
        self.assertEqual(self.run_campaign(transport, 100), {"ran": 18, "remaining": 0})
        rows = self.trials()
        self.assertEqual(len(rows), 18)
        self.assertTrue(all(r["pass"] and r["provenance"] == "fixture" for r in rows), [r["errors"] for r in rows])
        calls = {r["case_id"]: r["provider_calls"] for r in rows}
        self.assertEqual(calls["p01-live-037"], 1)  # early escalation ends at the classifier
        self.assertEqual(calls["p01-live-001"], 4)
        blob = (self.out / "trials.jsonl").read_text(encoding="utf-8")
        for case in CASES:
            if case["split"] == "development":
                self.assertNotIn(case["input"][:25], blob)
        self.assertNotIn("response", blob)
        report = ex.build_report(CASES, self.out, provenance="fixture")
        self.assertEqual(report["status"], "COMPLETE")
        self.assertEqual(report["live_model"]["passed"], 18)
        self.assertEqual(report["live_model"]["provider_calls"], sum(calls.values()))
        self.assertEqual(report["live_model"]["latency_ms"]["per_call"]["n"], sum(calls.values()))
        self.assertEqual(report["live_model"]["latency_ms"]["per_trial"]["n"], 18)

    def test_every_attempt_goes_through_the_logical_ledger_with_the_p01_reservation(self) -> None:
        self.run_campaign(self.oracle(), 2)
        ledger = CampaignLedger(self.out / "ledger.sqlite", campaign_id=ex.CAMPAIGN, read_only=True)
        events = ledger.reserved_trials()
        self.assertEqual([e["event"] for e in events], ["reserved", "completed", "reserved", "completed"])
        self.assertEqual({e["outcome"] for e in events if e["event"] == "completed"}, {"graded"})
        self.assertEqual(ex.TRIAL_RESERVE, {"calls": 4, "input_tokens": 8192, "output_tokens": 1024})

    def test_resume_never_repeats_a_finished_case(self) -> None:
        transport = self.oracle()
        self.assertEqual(self.run_campaign(transport, 4), {"ran": 4, "remaining": 14})
        self.assertEqual(self.run_campaign(transport, 100), {"ran": 14, "remaining": 0})
        ids = [r["case_id"] for r in self.trials()]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(self.run_campaign(transport, 5), {"ran": 0, "remaining": 0})

    def test_a_provider_error_stops_the_campaign_without_replay(self) -> None:
        transport = BrokenTransport({"status": "INCOMPLETE", "reason": "rate_limit", "attempt_id": "1" * 32})
        with self.assertRaisesRegex(ex.ExecutionBlocked, "rate_limit"):
            self.run_campaign(transport, 3, reader=lambda _id: {"calls": 1, "input_tokens": 0, "output_tokens": 0})
        self.assertEqual(transport.calls, 1)
        self.assertTrue((self.out / "stop.json").exists())
        stop = json.loads((self.out / "stop.json").read_text(encoding="utf-8"))
        self.assertFalse(stop["replay_allowed"])
        with self.assertRaisesRegex(ex.ExecutionBlocked, "campaign_stopped_requires_review"):
            self.run_campaign(transport, 3)
        self.assertEqual(transport.calls, 1)
        self.assertEqual(self.trials(), [])

    def test_unknown_errors_become_uncertain_and_never_leak_text(self) -> None:
        transport = BrokenTransport(error=RuntimeError("secret prompt text"))
        with self.assertRaisesRegex(ex.ExecutionBlocked, "provider_timeout_uncertain"):
            self.run_campaign(transport, 1, reader=lambda _id: {"calls": 0, "input_tokens": 0, "output_tokens": 0})
        self.assertNotIn("secret", (self.out / "stop.json").read_text(encoding="utf-8"))

    def test_usage_that_disagrees_with_the_receipts_stops_the_campaign(self) -> None:
        with self.assertRaisesRegex(ex.ExecutionBlocked, "usage_mismatch"):
            self.run_campaign(self.oracle(), 1, reader=lambda _id: {"calls": 4, "input_tokens": 1, "output_tokens": 1})
        self.assertEqual(self.trials(), [])

    def test_a_reservation_without_a_result_blocks_until_reviewed(self) -> None:
        transport = self.oracle()
        self.run_campaign(transport, 1)
        CampaignLedger(self.out / "ledger.sqlite", campaign_id=ex.CAMPAIGN).reserve(
            case_id="stranded", trial=1, calls=4, input_tokens=8192, output_tokens=1024,
            estimated_cost_usd=ex.TRIAL_COST, caps=ex.LEDGER_CAPS,
        )
        with self.assertRaisesRegex(ex.ExecutionBlocked, "uncertain_trial_requires_review"):
            self.run_campaign(transport, 1)

    def test_a_malformed_worker_reply_is_a_graded_contract_failure_not_a_stop(self) -> None:
        reply = {"status": "ok", "model": ex.MODEL, "attempt_id": "a" * 32, "content": '{"category": "billing"}',
                 "finish_reason": "stop", "usage": {"input_tokens": 100, "output_tokens": 40}, "latency_ms": 5.0}
        transport = BrokenTransport(reply)
        self.run_campaign(transport, 1)
        row = self.trials()[0]
        self.assertFalse(row["pass"])
        self.assertEqual(row["errors"], ["contract_failure"])
        self.assertEqual(row["observation"]["failure"], "worker_contract")
        self.assertEqual(row["observation"]["failure_worker"], "classifier")
        self.assertEqual(row["provider_calls"], 1)
        self.assertFalse((self.out / "stop.json").exists())

    def test_a_truncated_reply_is_a_graded_failure(self) -> None:
        reply = {"status": "ok", "model": ex.MODEL, "attempt_id": "b" * 32, "content": '{"category": "bil',
                 "finish_reason": "length", "usage": {"input_tokens": 100, "output_tokens": 40}, "latency_ms": 5.0}
        self.run_campaign(BrokenTransport(reply), 1)
        row = self.trials()[0]
        self.assertEqual(row["observation"]["failure"], "output_truncated")
        self.assertEqual(row["errors"], ["contract_failure"])

    def test_percentile_is_nearest_rank_and_wilson_is_bounded(self) -> None:
        values = [float(i) for i in range(1, 21)]
        self.assertEqual(ex.percentile(values, 50), 10.0)
        self.assertEqual(ex.percentile(values, 95), 19.0)
        self.assertIsNone(ex.percentile([], 50))
        low, high = ex.wilson(9, 18)
        self.assertTrue(0 < low < 0.5 < high < 1)
        self.assertIsNone(ex.wilson(0, 0))

    def test_report_states_the_core_only_scope_and_the_pending_reviews(self) -> None:
        self.run_campaign(self.oracle(), 100)
        report = ex.build_report(CASES, self.out, provenance="fixture")
        self.assertEqual(report["scope"], "core_only")
        self.assertEqual(report["other_runners_live"], "NOT_RUN")
        self.assertEqual(report["human_review"], "PENDING")
        self.assertEqual(report["independent_review"], "WAIVED_BY_OWNER")
        self.assertFalse(report["raw_provider_content_persisted"])
        self.assertTrue(any("route" in line and "not graded" in line for line in report["limits"]))
        self.assertTrue(any("not a cross-framework" in line for line in report["limits"]))
        self.assertEqual(set(report["live_model"]["by_family"]), {c["family"] for c in ex.ordered_cases(CASES)})

    def test_manifest_is_required_before_a_live_run_and_lists_the_guard_file_set(self) -> None:
        lab = ROOT.parents[1]
        with self.assertRaisesRegex(ex.ExecutionBlocked, "manifest_missing"):
            ex.validate_manifest(ROOT, lab, self.out, ROOT / "evals/datasets/live-v1/cases.jsonl", CASES)
        files = ex.guard_file_set(ROOT, lab)
        for name in ("scripts/harness/live_free_account.py", "scripts/harness/live_provider_transport.py",
                     "shared/policies/groq-free-campaign.json", "projects/p01/agent/prompts/live-core.md",
                     "projects/p01/evals/live-execution.json", "projects/p01/src/supportops_agents/accounted_live.py"):
            self.assertIn(name, files)
        self.assertNotIn("projects/p01/scripts/campaign_execution.py", files)

    def test_the_execution_manifest_approves_the_campaign_with_the_ordered_allocation(self) -> None:
        owner = json.loads((ROOT / "evals/live-execution.json").read_text(encoding="utf-8"))
        self.assertIn(ex.CAMPAIGN, owner["approved_campaigns"])
        allocation = owner["allocations"][ex.CAMPAIGN]
        self.assertEqual(allocation["stage"], "development")
        self.assertEqual(allocation["case_ids"], [c["case_id"] for c in ex.ordered_cases(CASES)])
        self.assertEqual((allocation["trials_per_case"], allocation["max_trials"]), (1, 18))
        self.assertIn("local-operation-v1", owner["allocations"])


if __name__ == "__main__":
    unittest.main()
