import unittest
from types import SimpleNamespace
from unittest.mock import patch
from supportops_agents.live_groq import GroqAgentClient, require_live_mode, keys

class LiveGroqEvalTests(unittest.TestCase):
 def test_credential_selection_uses_only_four_numbered_variables(self):
    from unittest.mock import patch
    with patch("supportops_agents.live_groq.root_env"), patch.dict("os.environ",{"GROQ_API_KEY":"legacy-extra","GROQ_API_KEY_1":"one","GROQ_API_KEY_2":"two","GROQ_API_KEY_3":"three","GROQ_API_KEY_4":"four"},clear=True):
     self.assertEqual(keys(),["one","two","three","four"])

 def test_live_mode_is_explicit(self):
    for value in (None,"fake","replay"):
        with self.assertRaisesRegex(RuntimeError,"LLM_MODE=live"):
            require_live_mode(value)
    require_live_mode("live")

 def test_live_client_rejects_unknown_agent_without_network(self):
    client=GroqAgentClient(["test-key"])
    with self.assertRaisesRegex(ValueError,"unknown agent"):
        client.complete("unknown",{})

 def test_offline_default_stays_fake(self):
    import os
    os.environ.pop("LLM_MODE",None)
    from supportops_agents import get_runner
    from supportops_agents.contracts import Ticket
    from supportops_agents.fakes import FakeLLMClient
    result=get_runner("core").run(Ticket("offline","subject","description"),llm=FakeLLMClient(),max_steps=4)
    self.assertIs(result.decision.approved,True)
    self.assertEqual(len(result.trace),4)

 def test_rotation_retries_only_transient_errors_with_next_key(self):
    from supportops_agents import live_groq
    keys=[]
    def factory(**kwargs):
     keys.append(kwargs["api_key"])
     key=kwargs.pop("api_key")
     return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **payload: complete(key,payload))))
    def complete(key,payload):
     if len(keys)==1:
      error=RuntimeError("transient fixture"); error.status_code=503; raise error
     return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content='{"response":"Policy guidance","approved":true}'))],usage=SimpleNamespace(prompt_tokens=20,completion_tokens=8))
    with patch("supportops_agents.live_groq._new_groq",side_effect=factory), patch("supportops_agents.live_groq.time.sleep",lambda _delay:None):
     client=GroqAgentClient(["key-one","key-two"])
     self.assertEqual(client.complete("responder",{}),{"response":"Policy guidance","approved":True})
    self.assertEqual(keys[:2],["key-one","key-two"])
    self.assertEqual(client.calls,1)

 def test_budget_blocks_before_network_and_errors_do_not_echo_secrets(self):
    from supportops_agents import live_groq
    client=GroqAgentClient(["secret-test-key"],budget_usd=0.000000001)
    with patch.object(live_groq,"_new_groq",side_effect=AssertionError("network must not run")):
     with self.assertRaisesRegex(RuntimeError,"budget preflight"):
      client.complete("responder",{"ticket":"x"*10000})
    def fail(**_kwargs):
     raise RuntimeError("secret-test-key must not be echoed")
    with patch.object(live_groq,"_new_groq",side_effect=fail):
     with self.assertRaises(RuntimeError) as error:
      GroqAgentClient(["secret-test-key"]).complete("responder",{})
    self.assertNotIn("secret-test-key",str(error.exception))
