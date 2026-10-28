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
