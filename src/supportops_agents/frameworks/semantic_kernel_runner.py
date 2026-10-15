"""Semantic Kernel classic adapter using a registered triage worker plugin."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from semantic_kernel import Kernel
from semantic_kernel.functions import kernel_function

from ..contracts import LLMClient, StepRecord, Ticket, TriageDecision, TriageResult, Usage
from ..core import _required_text


class _TriagePlugin:
    def __init__(self, llm: LLMClient):
        self._llm = llm

    @kernel_function(name="invoke_worker", description="Invoke one named SupportOps worker using the injected LLM client.")
    def invoke_worker(self, agent: str, payload_json: str) -> str:
        payload = json.loads(payload_json)
        return json.dumps(dict(self._llm.complete(agent, payload)))


class SemanticKernelTriageRunner:
    name = "semantic_kernel"

    def run(self, ticket: Ticket, *, llm: LLMClient, max_steps: int = 12) -> TriageResult:
        if not isinstance(ticket, Ticket):
            raise TypeError("ticket must be a Ticket")
        if isinstance(max_steps, bool) or not isinstance(max_steps, int) or max_steps < 1:
            raise ValueError("max_steps must be a positive integer")
        return asyncio.run(self._run(ticket, llm, max_steps))

    async def _run(self, ticket: Ticket, llm: LLMClient, max_steps: int) -> TriageResult:
        kernel = Kernel()
        plugin = kernel.add_plugin(_TriagePlugin(llm), plugin_name="supportops")
        worker = plugin["invoke_worker"]
        trace: list[StepRecord] = []
        state: dict[str, Any] = {"ticket": {"id": ticket.id, "subject": ticket.subject,
                    "description": ticket.description, "customer_id": ticket.customer_id}}

        async def call(agent: str) -> dict[str, Any]:
            result = await kernel.invoke(worker, agent=agent, payload_json=json.dumps(state))
            return json.loads(str(result.value))

        category, response, reason = "unknown", "", ""
        approved = False
        if len(trace) < max_steps:
            output = await call("classifier")
            category = _required_text(output, "category", "classifier")
            summary = _required_text(output, "summary", "classifier")
            state.update(category=category, classification=summary)
            reason = str(output.get("escalate", ""))
            trace.append(StepRecord(len(trace) + 1, "classifier", "escalate" if reason else "classify", summary))

        for agent, state_key, action in (("kb_researcher", "kb_context", "search_kb"),
                                         ("billing_agent", "billing_context", "check_billing")):
            if reason or len(trace) >= max_steps:
                break
            output = await call(agent)
            detail = _required_text(output, "context", agent)
            state[state_key] = detail
            reason = str(output.get("escalate", ""))
            trace.append(StepRecord(len(trace) + 1, agent, "escalate" if reason else action, detail))

        while not reason and len(trace) < max_steps:
            output = await call("responder")
            response = _required_text(output, "response", "responder")
            approved = output.get("approved") is True
            trace.append(StepRecord(len(trace) + 1, "responder", "approve" if approved else "revise", response))
            if approved:
                break

        stop = "escalated" if reason else "approved" if approved else "max_steps"
        if stop == "max_steps":
            reason = "Supervisor reached max_steps before an approved response."
        decision = TriageDecision("respond" if approved else "escalate", category, response, approved, reason)
        return TriageResult(decision, list(trace), Usage(), stop)
