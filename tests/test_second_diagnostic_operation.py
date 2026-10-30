import tempfile
import unittest
from decimal import Decimal
from pathlib import Path
from unittest.mock import Mock

from scripts.campaign_ledger import CampaignBlocked, CampaignLedger
from scripts.second_diagnostic_operation import CAMPAIGN, CAPS, Bridge, run
from supportops_agents.accounted_live import BoundaryError
from test_accounted_core import FixtureGuard


class Session:
    def __init__(self):
        self.guard = FixtureGuard()

    def preview(self, envelope):
        pass

    def complete(self, envelope):
        assert "operation" not in envelope, "direct shared session rejects protocol operation field"
        return self.guard.request(envelope)


class DiagnosticTests(unittest.TestCase):
    def test_startup_diagnostic_is_categorical_and_content_free(self):
        def denied():
            raise RuntimeError("authenticated_model_catalog_incomplete")
        with self.assertRaises(BoundaryError) as context:
            Bridge(denied,"fixture").request({"operation":"complete"})
        self.assertEqual(context.exception.diagnostic["reason"],"model_access")
        def private():
            raise RuntimeError("PRIVATE UNKNOWN")
        with self.assertRaises(BoundaryError) as context:
            Bridge(private,"fixture").request({"operation":"complete"})
        self.assertNotIn("PRIVATE",str(context.exception.diagnostic))

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "ledger.sqlite"
        original = CampaignLedger(self.path, campaign_id="local-operation-v1")
        original.reserve(case_id="fixture-local-01",trial=1,calls=4,input_tokens=8192,output_tokens=1024,
                         estimated_cost_usd=Decimal("0.0009216"),caps=CAPS)
        original.complete(case_id="fixture-local-01",trial=1,input_tokens=None,output_tokens=None,
                          actual_cost_usd=None,outcome="incomplete",error_class="unknown")
        first=CampaignLedger(self.path,campaign_id="local-diagnostic-v1")
        first.reserve(case_id="fixture-diagnostic-01",trial=1,calls=4,input_tokens=8192,output_tokens=1024,estimated_cost_usd=Decimal("0.0009216"),caps=CAPS)
        first.complete(case_id="fixture-diagnostic-01",trial=1,input_tokens=None,output_tokens=None,actual_cost_usd=None,outcome="incomplete",error_class="unknown")
        self.first=first.reserved_trials()
        self.original = original.reserved_trials()

    def test_one_separate_workflow_retains_original_and_total_ceiling(self):
        session = Session()
        def factory():
            self.assertEqual(CampaignLedger(self.path,campaign_id=CAMPAIGN).totals()["requests"],12)
            return session
        result = run(self.path,authority_check=lambda:None,session_factory=factory)
        self.assertEqual(result["status"],"ok")
        self.assertEqual(result["calls"],4)
        self.assertEqual(CampaignLedger(self.path,campaign_id="local-operation-v1").reserved_trials(),self.original)
        self.assertEqual(CampaignLedger(self.path,campaign_id="local-diagnostic-v1").reserved_trials(),self.first)
        denied = Mock(side_effect=AssertionError("no replay"))
        with self.assertRaisesRegex(CampaignBlocked,"already_reserved"):
            run(self.path,authority_check=lambda:None,session_factory=denied)
        denied.assert_not_called()

    def test_uncertain_failure_is_reported_and_never_replayed(self):
        session = Session()
        session.guard.failure = TimeoutError("PRIVATE")
        result = run(self.path,authority_check=lambda:None,session_factory=lambda:session)
        self.assertEqual(result["status"],"INCOMPLETE")
        self.assertNotIn("PRIVATE",str(result))
        self.assertTrue(result["diagnostic_reservation_retained"])
        with self.assertRaisesRegex(CampaignBlocked,"already_reserved"):
            run(self.path,authority_check=lambda:None,session_factory=lambda:Session())
        self.assertEqual(CampaignLedger(self.path,campaign_id=CAMPAIGN).totals()["requests"],12)

    def test_authority_denial_precedes_new_reservation_and_factory(self):
        factory = Mock()
        def deny():
            raise CampaignBlocked("authority_denied")
        with self.assertRaisesRegex(CampaignBlocked,"authority_denied"):
            run(self.path,authority_check=deny,session_factory=factory)
        factory.assert_not_called()
        self.assertEqual(CampaignLedger(self.path,campaign_id=CAMPAIGN).totals()["requests"],8)
