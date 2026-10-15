import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from supportops_agents.contracts import Ticket
from supportops_agents.fakes import FakeLLMClient
from supportops_agents.frameworks.langgraph_runner import LangGraphTriageRunner


class LangGraphRunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database = Path(self.temp_dir.name) / "checkpoints.sqlite"
        self.ticket = Ticket("lg-001", "Duplicate charge", "I was charged twice.")

    def tearDown(self):
        self.temp_dir.cleanup()

    def runner(self):
        return LangGraphTriageRunner(self.database)

    def test_runs_kb_and_billing_branches_then_returns_common_contract(self):
        llm = FakeLLMClient()
        result = self.runner().run(self.ticket, llm=llm)
        self.assertEqual(result.stop_reason, "approved")
        self.assertEqual({name for name, _ in llm.calls}, {"classifier", "kb_researcher", "billing_agent", "responder"})
        self.assertEqual(len(result.trace), 4)
        self.assertTrue(self.database.exists())

    def test_classifier_escalation_stops_graph(self):
        llm = FakeLLMClient({"classifier": [{"category": "safety", "summary": "threat", "escalate": "review"}]})
        result = self.runner().run(self.ticket, llm=llm)
        self.assertEqual(result.stop_reason, "escalated")
        self.assertEqual([name for name, _ in llm.calls], ["classifier"])

    def test_budget_boundaries_never_exceed_agent_call_limit(self):
        for limit in (1, 2, 3, 4):
            with self.subTest(limit=limit):
                ticket = Ticket(f"lg-limit-{limit}", "Limit", "Test budget.")
                llm = FakeLLMClient()
                result = self.runner().run(ticket, llm=llm, max_steps=limit)
                self.assertLessEqual(len(llm.calls), limit)
                self.assertLessEqual(len(result.trace), limit)
                self.assertEqual(result.stop_reason, "approved" if limit == 4 else "max_steps")

    def test_interrupt_can_resume_after_constructing_a_new_runner(self):
        llm = FakeLLMClient({"billing_agent": [{"context": "refund found", "refund_amount": 250}]})
        result = self.runner().run(self.ticket, llm=llm)
        self.assertEqual(result.stop_reason, "escalated")
        self.assertIn("pending", result.decision.reason)

        resumed = self.runner().resume(self.ticket, llm=llm, approved=True)
        self.assertEqual(resumed.stop_reason, "approved")
        self.assertTrue(resumed.decision.approved)

    def test_human_denial_escalates_without_responder(self):
        llm = FakeLLMClient({"billing_agent": [{"context": "refund found", "refund_amount": 250}]})
        self.runner().run(self.ticket, llm=llm)
        resumed = self.runner().resume(self.ticket, llm=llm, approved=False)
        self.assertEqual(resumed.stop_reason, "escalated")
        self.assertIn("denied", resumed.decision.reason)

    def test_checkpoint_survives_process_exit_and_resumes_in_a_second_process(self):
        ticket_id = "lg-process-resume"
        source_root = Path(__file__).resolve().parents[1] / "src"
        env = os.environ.copy()
        env["PYTHONPATH"] = str(source_root)
        high_refund = "{'billing_agent': [{'context': 'refund found', 'refund_amount': 250}]}"
        first_code = (
            "from pathlib import Path; "
            "from supportops_agents.contracts import Ticket; "
            "from supportops_agents.fakes import FakeLLMClient; "
            "from supportops_agents.frameworks.langgraph_runner import LangGraphTriageRunner; "
            f"ticket=Ticket({ticket_id!r}, 'Refund', 'Review it'); "
            f"runner=LangGraphTriageRunner({str(self.database)!r}); "
            f"result=runner.run(ticket, llm=FakeLLMClient({high_refund})); "
            "print(result.stop_reason, result.decision.reason)"
        )
        first = subprocess.run([sys.executable, "-c", first_code], env=env, text=True,
                               encoding="utf-8", errors="replace", capture_output=True)
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertIn("escalated", first.stdout)

        second_code = (
            "from supportops_agents.contracts import Ticket; "
            "from supportops_agents.fakes import FakeLLMClient; "
            "from supportops_agents.frameworks.langgraph_runner import LangGraphTriageRunner; "
            f"ticket=Ticket({ticket_id!r}, 'Refund', 'Review it'); "
            f"runner=LangGraphTriageRunner({str(self.database)!r}); "
            f"result=runner.resume(ticket, llm=FakeLLMClient({high_refund}), approved=True); "
            "print(result.stop_reason)"
        )
        second = subprocess.run([sys.executable, "-c", second_code], env=env, text=True,
                                encoding="utf-8", errors="replace", capture_output=True)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertIn("approved", second.stdout)

    def test_retries_a_transient_node_failure(self):
        class FailOnce:
            def __init__(self):
                self.fake = FakeLLMClient()
                self.failed = False

            def complete(self, agent, payload):
                if agent == "classifier" and not self.failed:
                    self.failed = True
                    raise TimeoutError("temporary worker timeout")
                return self.fake.complete(agent, payload)

        llm = FailOnce()
        result = self.runner().run(self.ticket, llm=llm)
        self.assertEqual(result.stop_reason, "approved")
        self.assertTrue(llm.failed)


if __name__ == "__main__":
    unittest.main()
