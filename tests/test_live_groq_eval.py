import os
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from supportops_agents import get_runner, live_groq
from supportops_agents.contracts import Ticket
from supportops_agents.fakes import FakeLLMClient
from supportops_agents.live_groq import GroqAgentClient, keys, require_live_mode


class LiveGroqEvalTests(unittest.TestCase):
    def test_credential_selection_uses_only_four_numbered_variables(self):
        with (
            patch("supportops_agents.live_groq.root_env"),
            patch.dict(
                "os.environ",
                {
                    "GROQ_API_KEY": "legacy-extra",
                    "GROQ_API_KEY_1": "one",
                    "GROQ_API_KEY_2": "two",
                    "GROQ_API_KEY_3": "three",
                    "GROQ_API_KEY_4": "four",
                },
                clear=True,
            ),
        ):
            self.assertEqual(keys(), ["one", "two", "three", "four"])

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

    def test_rotation_retries_only_transient_errors_with_next_key(self):
        error = RuntimeError("transient fixture")
        error.status_code = 503
        first_client = Mock()
        first_client.chat.completions.create.side_effect = error
        second_client = Mock()
        second_client.chat.completions.create.return_value = SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content='{"response":"Policy guidance","approved":true}'
                    )
                )
            ],
            usage=SimpleNamespace(prompt_tokens=20, completion_tokens=8),
        )

        with (
            patch.object(
                live_groq, "_new_groq", side_effect=[first_client, second_client]
            ) as factory,
            patch.object(live_groq.time, "sleep"),
        ):
            client = GroqAgentClient(["key-one", "key-two"])
            self.assertEqual(
                client.complete("responder", {}),
                {"response": "Policy guidance", "approved": True},
            )
        self.assertEqual(
            [call.kwargs["api_key"] for call in factory.call_args_list],
            ["key-one", "key-two"],
        )
        self.assertEqual(client.calls, 1)

    def test_budget_blocks_before_network_and_errors_do_not_echo_secrets(self):
        client = GroqAgentClient(["secret-test-key"], budget_usd=0.000000001)
        with patch.object(
            live_groq, "_new_groq", side_effect=AssertionError("network must not run")
        ):
            with self.assertRaisesRegex(RuntimeError, "budget preflight"):
                client.complete("responder", {"ticket": "x" * 10000})

        def fail(**_kwargs):
            raise RuntimeError("secret-test-key must not be echoed")

        with patch.object(live_groq, "_new_groq", side_effect=fail):
            with self.assertRaises(RuntimeError) as error:
                GroqAgentClient(["secret-test-key"]).complete("responder", {})
        self.assertNotIn("secret-test-key", str(error.exception))
