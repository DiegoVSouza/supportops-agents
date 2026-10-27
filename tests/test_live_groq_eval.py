import os
import unittest
from unittest.mock import patch

from supportops_agents import get_runner, live_groq
from supportops_agents.contracts import Ticket
from supportops_agents.fakes import FakeLLMClient
from supportops_agents.live_groq import GroqAgentClient, keys, require_live_mode


class LiveGroqEvalTests(unittest.TestCase):
    def test_legacy_helpers_deny_before_credentials_or_sdk(self):
        with (
            patch(
                "pathlib.Path.read_text", side_effect=AssertionError("credential read forbidden")
            ),
            patch.object(
                live_groq, "_new_groq", side_effect=AssertionError("SDK forbidden")
            ) as sdk,
        ):
            for operation in (
                keys,
                live_groq.root_env,
                lambda: live_groq.preflight(["fixture-key"]),
            ):
                with (
                    self.subTest(operation=operation),
                    self.assertRaisesRegex(RuntimeError, "accounted_guard_required"),
                ):
                    operation()
            sdk.assert_not_called()

    def test_live_mode_is_explicit(self):
        for value in (None, "fake", "replay"):
            with self.assertRaisesRegex(RuntimeError, "LLM_MODE=live"):
                require_live_mode(value)
        require_live_mode("live")

    def test_live_client_rejects_unknown_agent_without_network(self):
        client = GroqAgentClient(["test-key"])
        with self.assertRaisesRegex(ValueError, "unknown agent"):
            client.complete("unknown", {})

    def test_offline_default_stays_fake(self):
        with patch.dict(os.environ):
            os.environ.pop("LLM_MODE", None)
            result = get_runner("core").run(
                Ticket("offline", "subject", "description"),
                llm=FakeLLMClient(),
                max_steps=4,
            )
        self.assertIs(result.decision.approved, True)
        self.assertEqual(len(result.trace), 4)

    def test_legacy_client_cannot_dispatch_or_rotate_any_key(self):
        with patch.object(
            live_groq, "_new_groq", side_effect=AssertionError("SDK forbidden")
        ) as sdk:
            client = GroqAgentClient(
                ["fixture-one", "fixture-two", "fixture-three", "fixture-four"]
            )
            for _ in range(2):
                with self.assertRaisesRegex(RuntimeError, "accounted_guard_required"):
                    client.complete("responder", {})
            sdk.assert_not_called()

    def test_legacy_errors_never_echo_keys_or_ticket_text(self):
        with patch.object(
            live_groq, "_new_groq", side_effect=AssertionError("SDK forbidden")
        ) as sdk:
            for budget in (0.01, 0.000000001):
                client = GroqAgentClient(["fixture-private-key"], budget_usd=budget)
                with self.assertRaisesRegex(RuntimeError, "accounted_guard_required") as error:
                    client.complete("responder", {"ticket": "private-content" * 10000})
                self.assertNotIn("fixture-private-key", str(error.exception))
                self.assertNotIn("private-content", str(error.exception))
            sdk.assert_not_called()
