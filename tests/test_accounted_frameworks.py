"""Fixture-only accounting coverage for the actual framework integrations."""
import json
import tempfile
import threading
import time
import unittest
from pathlib import Path

from scripts.campaign_execution import OracleTransport
from supportops_agents.accounted_frameworks import _OrderedFixtureClient, run_fixture
from supportops_agents.accounted_live import AccountedCoreClient, BoundaryError, WorkflowBinding
from supportops_agents.registry import RUNNER_NAMES

ROOT = Path(__file__).resolve().parents[1]
CASES = [json.loads(line) for line in (ROOT / "evals/datasets/live-v1/cases.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
CASE = next(case for case in CASES if case["case_id"] == "p01-live-001")
ESCALATION = next(case for case in CASES if case["case_id"] == "p01-live-037")


class AccountedFrameworkTests(unittest.TestCase):
    def test_each_framework_uses_bounded_fixture_receipts(self):
        for name in RUNNER_NAMES[1:]:
            with self.subTest(runner=name), tempfile.TemporaryDirectory() as directory:
                transport = OracleTransport({CASE["case_id"]: CASE})
                result, receipts = run_fixture(name, CASE, transport, Path(directory))
                self.assertEqual(result.stop_reason, "approved")
                self.assertTrue(result.decision.approved)
                self.assertEqual([r["call_index"] for r in receipts], [1, 2, 3, 4])
                self.assertTrue(all(r["provenance"] == "fixture" for r in receipts))

    def test_live_transport_is_rejected_before_dispatch(self):
        class LiveTransport:
            provenance = "live"

            def request(self, _envelope):
                raise AssertionError("must not dispatch")

        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                run_fixture("crewai", CASE, LiveTransport(), Path(directory))

    def test_each_framework_stops_after_classifier_escalation(self):
        for name in RUNNER_NAMES[1:]:
            with self.subTest(runner=name), tempfile.TemporaryDirectory() as directory:
                transport = OracleTransport({ESCALATION["case_id"]: ESCALATION})
                result, receipts = run_fixture(name, ESCALATION, transport, Path(directory))
                self.assertEqual(result.stop_reason, "escalated")
                self.assertEqual(len(receipts), 1)

    def test_uncertain_first_attempt_is_not_retried_by_any_framework(self):
        class UncertainTransport:
            provenance = "fixture"

            def __init__(self):
                self.calls = 0

            def request(self, _envelope):
                self.calls += 1
                raise TimeoutError("synthetic uncertainty")

        for name in RUNNER_NAMES[1:]:
            with self.subTest(runner=name), tempfile.TemporaryDirectory() as directory:
                transport = UncertainTransport()
                with self.assertRaises(Exception):
                    run_fixture(name, CASE, transport, Path(directory))
                self.assertEqual(transport.calls, 1)

    def test_parallel_workers_preserve_receipt_order_and_call_limit(self):
        transport = OracleTransport({CASE["case_id"]: CASE})
        client = AccountedCoreClient(transport, WorkflowBinding("fixture-framework-029", CASE["case_id"], 1))
        ordered = _OrderedFixtureClient(client)
        state = {"ticket": {"id": CASE["case_id"], "subject": "Synthetic", "description": CASE["input"], "customer_id": "synthetic"}}
        ordered.complete("classifier", state)
        errors = []

        def billing():
            try:
                ordered.complete("billing_agent", state)
            except Exception as error:
                errors.append(error)

        thread = threading.Thread(target=billing)
        thread.start()
        time.sleep(0.05)
        ordered.complete("kb_researcher", state)
        thread.join(timeout=3)
        self.assertFalse(thread.is_alive())
        self.assertEqual(errors, [])
        ordered.complete("responder", state)
        self.assertEqual([r["worker"] for r in client.receipts], ["classifier", "kb_researcher", "billing_agent", "responder"])
        with self.assertRaises(BoundaryError):
            ordered.complete("responder", state)
        self.assertEqual(transport.counts[CASE["case_id"]][0], 4)
        client.close()

    def test_uncertain_parallel_worker_stops_all_later_calls(self):
        class SecondCallUncertain(OracleTransport):
            def __init__(self):
                super().__init__({CASE["case_id"]: CASE})
                self.attempts = 0

            def request(self, envelope):
                self.attempts += 1
                if self.attempts == 2:
                    raise TimeoutError("synthetic uncertainty")
                return super().request(envelope)

        with tempfile.TemporaryDirectory() as directory:
            transport = SecondCallUncertain()
            with self.assertRaises(Exception):
                run_fixture("langgraph", CASE, transport, Path(directory))
            self.assertEqual(transport.attempts, 2)
