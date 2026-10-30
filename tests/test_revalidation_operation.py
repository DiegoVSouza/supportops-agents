"""Offline controls for the single explicitly authorized P01 revalidation."""

import copy
import json
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path
from unittest.mock import Mock

from scripts.campaign_ledger import CampaignBlocked, CampaignLedger
from scripts.revalidation_operation import (
    CAPS,
    CAMPAIGN,
    CASE,
    WORKFLOW_RESERVE,
    Bridge,
    RevalidationBlocked,
    owner_allocation,
    run,
    write_once,
)
from supportops_agents.accounted_live import BoundaryError, MODEL
from test_accounted_core import FixtureGuard


class Session:
    def __init__(self):
        self.guard = FixtureGuard()

    def preview(self, envelope):
        assert envelope["campaign_id"] == CAMPAIGN
        assert envelope["case_id"] == CASE

    def complete(self, envelope):
        assert "operation" not in envelope
        return self.guard.request(envelope)


class RevalidationOperationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="p01-revalidation-")
        self.addCleanup(self.temp.cleanup)
        self.ledger_path = Path(self.temp.name) / "ledger.sqlite"
        self.historical = {}
        self.seed_history("local-operation-v1", "fixture-local-01")
        self.seed_history("local-diagnostic-v1", "fixture-diagnostic-01")
        self.seed_history("local-diagnostic-2-v1", "fixture-diagnostic-02")

    def seed_history(self, campaign, case_id):
        ledger = CampaignLedger(self.ledger_path, campaign_id=campaign)
        ledger.reserve(
            case_id=case_id,
            trial=1,
            calls=4,
            input_tokens=8192,
            output_tokens=1024,
            estimated_cost_usd=Decimal("0.0009216"),
            caps=CAPS,
        )
        ledger.complete(
            case_id=case_id,
            trial=1,
            input_tokens=None,
            output_tokens=None,
            actual_cost_usd=None,
            outcome="incomplete",
            error_class="unknown",
        )
        self.historical[campaign] = ledger.reserved_trials()

    def test_exact_reservation_succeeds_and_preserves_all_prior_workflows(self):
        session = Session()

        def factory():
            totals = CampaignLedger(self.ledger_path, campaign_id=CAMPAIGN).totals()
            self.assertEqual(totals["requests"], 16)
            self.assertEqual(totals["input_tokens"], 32768)
            self.assertEqual(totals["output_tokens"], 4096)
            return session

        result = run(
            self.ledger_path,
            authority_check=lambda: None,
            session_factory=factory,
        )
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["calls"], 4)
        self.assertEqual(
            CampaignLedger(self.ledger_path, campaign_id=CAMPAIGN).totals()["requests"],
            16,
        )
        for campaign, events in self.historical.items():
            self.assertEqual(
                CampaignLedger(self.ledger_path, campaign_id=campaign).reserved_trials(),
                events,
            )
        self.assertEqual(CAPS["requests"], 16)
        self.assertEqual(CAPS["estimated_cost_usd"], Decimal("0.0036864"))

    def test_unknown_failure_retains_full_reserve_and_cannot_replay(self):
        session = Session()
        session.guard.failure = TimeoutError("private response text")
        result = run(
            self.ledger_path,
            authority_check=lambda: None,
            session_factory=lambda: session,
        )
        self.assertEqual(result["status"], "INCOMPLETE")
        self.assertTrue(result["revalidation_reserve_retained"])
        self.assertNotIn("private response", json.dumps(result))
        self.assertEqual(
            CampaignLedger(self.ledger_path, campaign_id=CAMPAIGN).totals()["requests"],
            16,
        )
        denied = Mock(side_effect=AssertionError("replay forbidden"))
        with self.assertRaisesRegex(CampaignBlocked, "already_reserved"):
            run(self.ledger_path, authority_check=lambda: None, session_factory=denied)
        denied.assert_not_called()

    def test_authority_denial_precedes_reservation_and_client_factory(self):
        factory = Mock(side_effect=AssertionError("client must stay closed"))

        def deny():
            raise CampaignBlocked("authority_denied")

        with self.assertRaisesRegex(CampaignBlocked, "authority_denied"):
            run(
                self.ledger_path,
                authority_check=deny,
                session_factory=factory,
            )
        factory.assert_not_called()
        self.assertEqual(
            CampaignLedger(self.ledger_path, campaign_id=CAMPAIGN).totals()["requests"],
            12,
        )

    def test_worker_contract_failure_is_terminal_and_keeps_unknown_reserve(self):
        session = Session()
        session.guard.outputs["kb_researcher"] = {"context": "", "private": "discard"}
        result = run(
            self.ledger_path,
            authority_check=lambda: None,
            session_factory=lambda: session,
        )
        self.assertEqual(result["status"], "INCOMPLETE")
        self.assertEqual(result["calls"], 2)
        self.assertNotIn("discard", json.dumps(result))
        self.assertEqual(
            CampaignLedger(self.ledger_path, campaign_id=CAMPAIGN).totals()["requests"],
            16,
        )
        self.assertEqual(
            CampaignLedger(self.ledger_path, campaign_id=CAMPAIGN).reserved_trials()[-1][
                "outcome"
            ],
            "incomplete",
        )

    def test_startup_error_mapping_is_categorical(self):
        def denied():
            raise RuntimeError("reviewed_revalidation_authority_or_history_invalid")

        with self.assertRaises(BoundaryError) as context:
            Bridge(denied, "fixture").request({"operation": "complete"})
        self.assertEqual(context.exception.diagnostic["reason"], "guard_denied")
        self.assertEqual(context.exception.diagnostic["provider_error_code"], None)

    def test_owner_scope_and_invocation_marker_are_single_use(self):
        self.assertEqual(owner_allocation()["allocations"][CAMPAIGN]["max_trials"], 1)
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / "invocation.json"
            write_once(marker, {"campaign": CAMPAIGN, "single_invocation": True})
            with self.assertRaisesRegex(RevalidationBlocked, "invocation_already_started"):
                write_once(marker, {"campaign": CAMPAIGN, "single_invocation": True})

    def test_workflow_caps_match_user_authorized_delta(self):
        self.assertEqual(WORKFLOW_RESERVE["calls"], 4)
        self.assertEqual(WORKFLOW_RESERVE["input_tokens"], 8192)
        self.assertEqual(WORKFLOW_RESERVE["output_tokens"], 1024)
        self.assertEqual(WORKFLOW_RESERVE["estimated_cost_usd"], Decimal("0.0009216"))
        self.assertEqual(MODEL, "openai/gpt-oss-20b")


if __name__ == "__main__":
    unittest.main()
