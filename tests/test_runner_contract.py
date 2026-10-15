import tempfile
import unittest
from pathlib import Path

from supportops_agents.contracts import Ticket
from supportops_agents.fakes import FakeLLMClient
from supportops_agents.registry import RUNNER_NAMES, get_runner


class SharedRunnerContractTests(unittest.TestCase):
    def test_all_runners_approve_the_common_synthetic_case(self):
        for name in RUNNER_NAMES:
            with self.subTest(runner=name):
                if name == "langgraph":
                    with tempfile.TemporaryDirectory() as directory:
                        runner = get_runner(name)
                        runner.checkpoint_path = Path(directory) / "state.sqlite"
                        result = runner.run(Ticket(f"contract-{name}", "Test", "Synthetic."),
                                            llm=FakeLLMClient(), max_steps=12)
                else:
                    result = get_runner(name).run(Ticket(f"contract-{name}", "Test", "Synthetic."),
                                                  llm=FakeLLMClient(), max_steps=12)
                self.assertEqual(result.stop_reason, "approved")
                self.assertTrue(result.decision.approved)
                self.assertEqual(result.decision.action, "respond")
                self.assertEqual(len(result.trace), 4)

    def test_all_runners_stop_at_the_shared_step_boundary(self):
        for name in RUNNER_NAMES:
            with self.subTest(runner=name):
                if name == "langgraph":
                    with tempfile.TemporaryDirectory() as directory:
                        runner = get_runner(name)
                        runner.checkpoint_path = Path(directory) / "state.sqlite"
                        result = runner.run(Ticket(f"limit-{name}", "Test", "Synthetic."),
                                            llm=FakeLLMClient(), max_steps=3)
                else:
                    result = get_runner(name).run(Ticket(f"limit-{name}", "Test", "Synthetic."),
                                                  llm=FakeLLMClient(), max_steps=3)
                self.assertEqual(result.stop_reason, "max_steps")
                self.assertLessEqual(len(result.trace), 3)

    def test_all_runners_propagate_worker_escalations(self):
        for name in RUNNER_NAMES:
            with self.subTest(runner=name):
                llm = FakeLLMClient({"billing_agent": [{"context": "refund over limit", "escalate": "human review required"}]})
                if name == "langgraph":
                    with tempfile.TemporaryDirectory() as directory:
                        runner = get_runner(name)
                        runner.checkpoint_path = Path(directory) / "state.sqlite"
                        result = runner.run(Ticket(f"escalate-{name}", "Refund", "Review needed."), llm=llm)
                else:
                    result = get_runner(name).run(Ticket(f"escalate-{name}", "Refund", "Review needed."), llm=llm)
                self.assertEqual(result.stop_reason, "escalated")
                self.assertIn("human review", result.decision.reason)
                self.assertNotIn("responder", [agent for agent, _ in llm.calls])


if __name__ == "__main__":
    unittest.main()
