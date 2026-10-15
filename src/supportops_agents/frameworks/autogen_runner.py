"""AutoGen classic Core runtime adapter for a deterministic fake LLM client."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

from autogen_core import AgentId, MessageContext, RoutedAgent, SingleThreadedAgentRuntime, message_handler

from ..contracts import LLMClient, StepRecord, Ticket, TriageDecision, TriageResult, Usage
from ..core import _required_text


@dataclass
class WorkerRequest:
    agent: str
    payload: dict[str, Any]


@dataclass
class WorkerResponse:
    output: dict[str, Any]


class _SupportOpsWorker(RoutedAgent):
    def __init__(self, llm: LLMClient):
        super().__init__("SupportOps specialist worker backed by the shared LLMClient contract")
        self._llm = llm

    @message_handler
    async def handle(self, message: WorkerRequest, context: MessageContext) -> WorkerResponse:
        return WorkerResponse(dict(self._llm.complete(message.agent, message.payload)))


class AutoGenTriageRunner:
    name = "autogen"

    def run(self, ticket: Ticket, *, llm: LLMClient, max_steps: int = 12) -> TriageResult:
        if not isinstance(ticket, Ticket):
            raise TypeError("ticket must be a Ticket")
        if isinstance(max_steps, bool) or not isinstance(max_steps, int) or max_steps < 1:
            raise ValueError("max_steps must be a positive integer")
        return asyncio.run(self._run(ticket, llm, max_steps))

    async def _run(self, ticket: Ticket, llm: LLMClient, max_steps: int) -> TriageResult:
        runtime = SingleThreadedAgentRuntime()
        await _SupportOpsWorker.register(runtime, "supportops_worker", lambda: _SupportOpsWorker(llm))
        runtime.start()
        trace: list[StepRecord] = []
        state: dict[str, Any] = {"ticket": {"id": ticket.id, "subject": ticket.subject,
                    "description": ticket.description, "customer_id": ticket.customer_id}, "category": "unknown"}
        response = ""
        approved = False
        reason = ""

        async def call(agent: str) -> dict[str, Any]:
            reply = await runtime.send_message(WorkerRequest(agent, dict(state)), AgentId("supportops_worker", "default"))
            return reply.output

        try:
            if len(trace) < max_steps:
                output = await call("classifier")
                category = _required_text(output, "category", "classifier")
                summary = _required_text(output, "summary", "classifier")
                state.update(category=category, classification=summary)
                reason = str(output.get("escalate", ""))
                trace.append(StepRecord(len(trace) + 1, "classifier", "escalate" if reason else "classify", summary))

            for agent, key, action in (("kb_researcher", "context", "search_kb"),
                                       ("billing_agent", "context", "check_billing")):
                if reason or len(trace) >= max_steps:
                    break
                output = await call(agent)
                detail = _required_text(output, key, agent)
                state["kb_context" if agent == "kb_researcher" else "billing_context"] = detail
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
            decision = TriageDecision("respond" if approved else "escalate", state.get("category", "unknown"),
                                      response, approved, reason)
            return TriageResult(decision, list(trace), Usage(), stop)
        finally:
            await runtime.stop_when_idle()
