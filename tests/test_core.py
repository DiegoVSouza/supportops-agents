import unittest

from supportops_agents.contracts import Ticket
from supportops_agents.core import CoreTriageRunner, InvalidAgentResponse
from supportops_agents.fakes import FakeLLMClient
from supportops_agents.registry import RunnerUnavailable, get_runner


TICKET = Ticket("t-001", "Duplicate charge", "I was charged twice.")


class CoreRunnerTests(unittest.TestCase):
    def test_approved_response_runs_all_workers_in_order(self):
        llm = FakeLLMClient()
        result = CoreTriageRunner().run(TICKET, llm=llm)
        self.assertEqual(result.stop_reason, "approved")
        self.assertTrue(result.decision.approved)
        self.assertEqual([row[0] for row in llm.calls], ["classifier", "kb_researcher", "billing_agent", "responder"])
        self.assertEqual(result.usage.cost_usd, None)

    def test_classifier_can_escalate_without_contacting_more_workers(self):
        llm = FakeLLMClient({"classifier": [{"category": "safety", "summary": "urgent", "escalate": "safety case"}]})
        result = CoreTriageRunner().run(TICKET, llm=llm)
        self.assertEqual(result.stop_reason, "escalated")
        self.assertEqual(result.decision.reason, "safety case")
        self.assertEqual(len(llm.calls), 1)

    def test_billing_can_escalate(self):
        llm = FakeLLMClient({"billing_agent": [{"context": "refund pending", "escalate": "refund needs approval"}]})
        result = CoreTriageRunner().run(TICKET, llm=llm)
        self.assertEqual(result.stop_reason, "escalated")
        self.assertEqual(len(llm.calls), 3)

    def test_never_approved_response_stops_at_exact_step_limit(self):
        llm = FakeLLMClient({"responder": [{"response": "Need more review.", "approved": False}] * 10})
        result = CoreTriageRunner().run(TICKET, llm=llm, max_steps=6)
        self.assertEqual(result.stop_reason, "max_steps")
        self.assertEqual(len(result.trace), 6)
        self.assertEqual(len(llm.calls), 6)
        self.assertEqual(result.decision.action, "escalate")

    def test_step_boundary_allows_final_step_approval(self):
        llm = FakeLLMClient()
        result = CoreTriageRunner().run(TICKET, llm=llm, max_steps=4)
        self.assertEqual(result.stop_reason, "approved")
        self.assertEqual(len(result.trace), 4)

    def test_rejects_zero_or_invalid_step_budget(self):
        for value in (0, -1, True, 1.5):
            with self.subTest(value=value), self.assertRaises(ValueError):
                CoreTriageRunner().run(TICKET, llm=FakeLLMClient(), max_steps=value)

    def test_rejects_malformed_worker_output(self):
        llm = FakeLLMClient({"classifier": [{"category": "billing", "summary": "  "}]})
        with self.assertRaises(InvalidAgentResponse):
            CoreTriageRunner().run(TICKET, llm=llm)

    def test_registry_does_not_impersonate_missing_framework(self):
        self.assertEqual(get_runner("core").name, "core")
        with self.assertRaises(RunnerUnavailable):
            get_runner("langgraph")
        with self.assertRaises(ValueError):
            get_runner("not-a-runner")


if __name__ == "__main__":
    unittest.main()
