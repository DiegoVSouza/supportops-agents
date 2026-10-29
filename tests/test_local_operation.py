import tempfile
import unittest
from contextlib import nullcontext
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import Mock

from scripts.campaign_ledger import CampaignBlocked, CampaignLedger
from scripts.local_operation import CAMPAIGN, run_fixture_operation
from test_accounted_core import FixtureGuard


class LocalOperationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "ledger.sqlite"
        self.guard = FixtureGuard()

    def run_case(self, request_id="fixture-one", factory=None, lease=None):
        return run_fixture_operation(self.path, request_id, "Synthetic ticket", lease=lease or nullcontext(),
                                     transport_factory=factory or (lambda: self.guard))

    def test_success_is_durable_and_replay_is_rejected_before_new_client(self):
        result = self.run_case()
        self.assertEqual(result["calls"], 4)
        self.assertEqual(CampaignLedger(self.path, campaign_id=CAMPAIGN).totals()["requests"], 4)
        factory = Mock(side_effect=AssertionError("must not construct"))
        with self.assertRaises(CampaignBlocked):
            self.run_case(factory=factory)
        factory.assert_not_called()

    def test_failure_retains_reservation_and_blocks_later_work(self):
        self.guard.failure = TimeoutError("private")
        with self.assertRaises(Exception):
            self.run_case()
        ledger = CampaignLedger(self.path, campaign_id=CAMPAIGN)
        self.assertEqual(ledger.totals()["input_tokens"], 8192)
        factory = Mock(side_effect=AssertionError("must not construct"))
        with self.assertRaisesRegex(CampaignBlocked, "prior_work"):
            self.run_case("fixture-two", factory=factory)
        factory.assert_not_called()

    def test_reservation_precedes_fixture_client_and_nonfixture_stops(self):
        def factory():
            self.assertEqual(CampaignLedger(self.path, campaign_id=CAMPAIGN).totals()["requests"], 4)
            self.guard.provenance = "live"
            return self.guard
        with self.assertRaisesRegex(CampaignBlocked, "fixture_transport"):
            self.run_case(factory=factory)
        self.assertEqual(self.guard.requests, [])

    def test_non_synthetic_id_rejected_before_ledger_creation(self):
        with self.assertRaisesRegex(CampaignBlocked, "invalid_synthetic"):
            self.run_case("not-fixture")
        self.assertFalse(self.path.exists())

    def test_lease_contention_stops_before_ledger_or_client(self):
        @contextmanager
        def denied():
            raise CampaignBlocked("lease_busy")
            yield
        factory = Mock(side_effect=AssertionError("must not construct"))
        with self.assertRaisesRegex(CampaignBlocked, "lease_busy"):
            self.run_case(factory=factory, lease=denied())
        self.assertFalse(self.path.exists())
        factory.assert_not_called()

    def test_missing_receipt_keeps_full_reservation(self):
        self.guard.override = {"status": "ok", "content": "{}", "model": "openai/gpt-oss-20b"}
        with self.assertRaises(Exception):
            self.run_case()
        self.assertEqual(CampaignLedger(self.path, campaign_id=CAMPAIGN).totals()["output_tokens"], 1024)

    def test_live_operation_requires_explicit_mode_and_fixed_synthetic_case(self):
        from unittest.mock import patch
        from scripts.local_operation import run_live_operation

        with patch.dict("os.environ", {"LLM_MODE": "fake"}):
            with self.assertRaisesRegex(CampaignBlocked, "explicit_synthetic"):
                run_live_operation("fixture-local-01")
        with patch.dict("os.environ", {"LLM_MODE": "live"}):
            with self.assertRaisesRegex(CampaignBlocked, "explicit_synthetic"):
                run_live_operation("customer-data")

    def test_cli_exposes_only_allowlisted_boundary_diagnostic(self):
        import io
        from contextlib import redirect_stdout
        from unittest.mock import patch
        from scripts.local_operation import main
        from supportops_agents.accounted_live import BoundaryError

        output = io.StringIO()
        with (patch("sys.argv", ["local_operation", "--request-id", "fixture-local-01"]),
              patch("scripts.local_operation.run_live_operation", side_effect=BoundaryError("output_truncated", {"content": "private"})),
              redirect_stdout(output)):
            self.assertEqual(main(), 2)
        self.assertIn("output_truncated", output.getvalue())
        self.assertNotIn("private", output.getvalue())
