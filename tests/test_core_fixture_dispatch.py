import tempfile
import unittest
from pathlib import Path

from supportops_agents.contracts import Ticket
from supportops_agents.core import CoreTriageRunner, InvalidAgentResponse
from supportops_agents.fakes import FakeLLMClient
from supportops_agents.synthetic_dispatch import SyntheticDispatcher, DispatchBlocked


class CoreFixtureDispatchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.calls = []
        self.dispatcher = SyntheticDispatcher(Path(self.tmp.name) / 'dispatch.sqlite', {
            'search_knowledge': lambda context: self.calls.append(context) or 'fixture evidence'
        })
        self.ticket = Ticket('fixture-ticket', 'question', 'synthetic request')

    def client(self, tools):
        return FakeLLMClient({'classifier': [{'category': 'technical', 'summary': 'fixture',
                                               'read_plan': {'tools': tools}}]})

    def run_core(self, client, run_id='fixture-run'):
        return CoreTriageRunner().run(self.ticket, llm=client, fixture_dispatcher=self.dispatcher,
                                      fixture_run_id=run_id, fixture_tenant='fixture-a')

    def test_dispatch_uses_caller_identity_and_four_call_limit(self):
        client = self.client(['search_knowledge'])
        result = self.run_core(client)
        self.assertEqual(result.stop_reason, 'approved')
        self.assertEqual(self.calls, [{'tenant': 'fixture-a'}])
        self.assertEqual(client.calls[1][1]['kb_context'], 'fixture evidence')
        self.assertEqual(len(client.calls), 4)
        self.run_core(self.client(['search_knowledge']))
        self.assertEqual(len(self.calls), 1)

    def test_invalid_and_effectful_plans_never_dispatch(self):
        for plan in ([], ['issue_refund'], ['search_knowledge', 'search_knowledge']):
            with self.subTest(plan=plan), self.assertRaises((InvalidAgentResponse, DispatchBlocked)):
                self.run_core(self.client(plan), run_id='run-invalid')
        self.assertEqual(self.calls, [])

    def test_unknown_dispatch_stops_before_later_workers(self):
        def fail(context):
            raise RuntimeError('fixture failure')
        self.dispatcher = SyntheticDispatcher(Path(self.tmp.name) / 'uncertain.sqlite', {'search_knowledge': fail})
        client = self.client(['search_knowledge'])
        with self.assertRaises(DispatchBlocked):
            self.run_core(client)
        self.assertEqual(len(client.calls), 1)
        with self.assertRaises(DispatchBlocked):
            self.run_core(self.client(['search_knowledge']))

    def test_non_fake_client_is_rejected_before_dispatch(self):
        class ExternalClient:
            def complete(self, agent, payload):
                raise AssertionError('must not call')
        with self.assertRaises(ValueError):
            self.run_core(ExternalClient())
        self.assertEqual(self.calls, [])


if __name__ == '__main__':
    unittest.main()
class AccountedFixtureDispatchTests(unittest.TestCase):
    def test_accounted_fixture_dispatch_uses_explicit_tenant_once(self):
        from test_accounted_core import FixtureGuard
        from supportops_agents.accounted_live import AccountedCoreClient, WorkflowBinding

        guard = FixtureGuard()
        guard.outputs["classifier"]["read_plan"] = {"tools": ["search_knowledge"]}
        with tempfile.TemporaryDirectory() as directory:
            calls = []
            dispatcher = SyntheticDispatcher(Path(directory) / "runs.sqlite", {
                "search_knowledge": lambda context: calls.append(context) or "fixture evidence"
            })
            client = AccountedCoreClient(guard, WorkflowBinding("fixture", "case", 1))
            result = CoreTriageRunner().run(Ticket("fixture-ticket", "question", "synthetic"),
                llm=client, fixture_dispatcher=dispatcher, fixture_run_id="run-1", fixture_tenant="fixture-a")
            self.assertEqual(result.stop_reason, "approved")
            self.assertEqual(calls, [{"tenant": "fixture-a"}])
            self.assertEqual(len(client.receipts), 4)
            self.assertEqual(dispatcher.run("run-1", ["search_knowledge"], {"tenant": "fixture-a"}), ["fixture evidence"])
            self.assertEqual(len(calls), 1)

    def test_live_provenance_is_rejected_before_any_request(self):
        from test_accounted_core import FixtureGuard
        from supportops_agents.accounted_live import AccountedCoreClient, WorkflowBinding

        guard = FixtureGuard()
        guard.provenance = "live"
        with tempfile.TemporaryDirectory() as directory:
            dispatcher = SyntheticDispatcher(Path(directory) / "runs.sqlite", {"search_knowledge": lambda _: "fixture"})
            client = AccountedCoreClient(guard, WorkflowBinding("fixture", "case", 1))
            with self.assertRaisesRegex(ValueError, "fixture dispatch"):
                CoreTriageRunner().run(Ticket("fixture-ticket", "question", "synthetic"), llm=client,
                    fixture_dispatcher=dispatcher, fixture_run_id="run-1", fixture_tenant="fixture-a")
        self.assertEqual(guard.requests, [])

    def test_failed_fixture_read_stops_before_next_worker_and_cannot_replay(self):
        from test_accounted_core import FixtureGuard
        from supportops_agents.accounted_live import AccountedCoreClient, WorkflowBinding

        guard = FixtureGuard()
        guard.outputs["classifier"]["read_plan"] = {"tools": ["search_knowledge"]}
        with tempfile.TemporaryDirectory() as directory:
            def fail(_context):
                raise RuntimeError("fixture failure")
            dispatcher = SyntheticDispatcher(Path(directory) / "runs.sqlite", {"search_knowledge": fail})
            client = AccountedCoreClient(guard, WorkflowBinding("fixture", "case", 1))
            with self.assertRaisesRegex(DispatchBlocked, "unknown_work"):
                CoreTriageRunner().run(Ticket("fixture-ticket", "question", "synthetic"), llm=client,
                    fixture_dispatcher=dispatcher, fixture_run_id="run-1", fixture_tenant="fixture-a")
            with self.assertRaisesRegex(DispatchBlocked, "mismatch_or_unknown_work"):
                dispatcher.run("run-1", ["search_knowledge"], {"tenant": "fixture-a"})
        self.assertEqual(len(guard.requests), 1)
        self.assertTrue(client.stopped)

    def test_classifier_read_plan_is_rejected_for_live_or_malformed_fixture(self):
        from supportops_agents.accounted_live import BoundaryError, validate_output

        output = {"category": "billing", "summary": "synthetic", "escalate": "",
                  "read_plan": {"tools": ["search_knowledge"]}}
        with self.assertRaises(BoundaryError):
            validate_output("classifier", output)
        output["read_plan"] = {"tools": [], "extra": True}
        with self.assertRaises(BoundaryError):
            validate_output("classifier", output, fixture_plan=True)
