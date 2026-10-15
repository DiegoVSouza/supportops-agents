"""LlamaIndex Workflows adapter with typed events and bounded responder loop."""

from __future__ import annotations

import asyncio
from typing import Any

from llama_index.core.workflow import Context, Event, StartEvent as WorkflowStartEvent, StopEvent, Workflow, step
from pydantic import PrivateAttr

from ..contracts import LLMClient, StepRecord, Ticket, TriageDecision, TriageResult, Usage
from ..core import _required_text


class TriageStart(WorkflowStartEvent):
    ticket_id: str
    subject: str
    description: str
    customer_id: str
    max_steps: int


class ResearchEvent(Event):
    ticket: dict[str, str]
    max_steps: int
    trace: list[dict[str, Any]]
    category: str
    classification: str


class BillingEvent(ResearchEvent):
    kb_context: str


class RespondEvent(BillingEvent):
    billing_context: str


class _TriageWorkflow(Workflow):
    _llm: Any = PrivateAttr()

    @step
    async def classify(self, ev: TriageStart) -> ResearchEvent | StopEvent:
        ticket = {"id": ev.ticket_id, "subject": ev.subject, "description": ev.description,
                  "customer_id": ev.customer_id}
        if ev.max_steps < 1:
            raise ValueError("max_steps must be a positive integer")
        output = dict(self._llm.complete("classifier", {"ticket": ticket}))
        category = _required_text(output, "category", "classifier")
        summary = _required_text(output, "summary", "classifier")
        escalation = str(output.get("escalate", ""))
        trace = [{"step": 1, "agent": "classifier", "action": "escalate" if escalation else "classify", "detail": summary}]
        if escalation:
            return StopEvent(result=_make_result(category, "", False, escalation, trace, "escalated"))
        if len(trace) >= ev.max_steps:
            return StopEvent(result=_make_result(category, "", False, "Supervisor reached max_steps before an approved response.", trace, "max_steps"))
        return ResearchEvent(ticket=ticket, max_steps=ev.max_steps, trace=trace, category=category, classification=summary)

    @step
    async def research(self, ev: ResearchEvent) -> BillingEvent | StopEvent:
        if len(ev.trace) >= ev.max_steps:
            return StopEvent(result=_make_result(ev.category, "", False, "Supervisor reached max_steps before a KB lookup.", ev.trace, "max_steps"))
        output = dict(self._llm.complete("kb_researcher", {"ticket": ev.ticket, "category": ev.category,
                                                              "classification": ev.classification}))
        context = _required_text(output, "context", "kb_researcher")
        trace = ev.trace + [{"step": len(ev.trace) + 1, "agent": "kb_researcher", "action": "search_kb", "detail": context}]
        return BillingEvent(ticket=ev.ticket, max_steps=ev.max_steps, trace=trace, category=ev.category,
                            classification=ev.classification, kb_context=context)

    @step
    async def billing(self, ev: BillingEvent) -> RespondEvent | StopEvent:
        if len(ev.trace) >= ev.max_steps:
            return StopEvent(result=_make_result(ev.category, "", False, "Supervisor reached max_steps before billing review.", ev.trace, "max_steps"))
        output = dict(self._llm.complete("billing_agent", {"ticket": ev.ticket, "category": ev.category,
                                                              "classification": ev.classification,
                                                              "kb_context": ev.kb_context}))
        context = _required_text(output, "context", "billing_agent")
        reason = str(output.get("escalate", ""))
        trace = ev.trace + [{"step": len(ev.trace) + 1, "agent": "billing_agent",
                             "action": "escalate" if reason else "check_billing", "detail": context}]
        if reason:
            return StopEvent(result=_make_result(ev.category, "", False, reason, trace, "escalated"))
        return RespondEvent(ticket=ev.ticket, max_steps=ev.max_steps, trace=trace, category=ev.category,
                            classification=ev.classification, kb_context=ev.kb_context, billing_context=context)

    @step
    async def respond(self, ev: RespondEvent) -> RespondEvent | StopEvent:
        if len(ev.trace) >= ev.max_steps:
            return StopEvent(result=_make_result(ev.category, "", False, "Supervisor reached max_steps before responding.", ev.trace, "max_steps"))
        state = {"ticket": ev.ticket, "category": ev.category, "classification": ev.classification,
                 "kb_context": ev.kb_context, "billing_context": ev.billing_context}
        output = dict(self._llm.complete("responder", state))
        response = _required_text(output, "response", "responder")
        approved = output.get("approved") is True
        trace = ev.trace + [{"step": len(ev.trace) + 1, "agent": "responder",
                             "action": "approve" if approved else "revise", "detail": response}]
        if approved:
            return StopEvent(result=_make_result(ev.category, response, True, "", trace, "approved"))
        if len(trace) >= ev.max_steps:
            return StopEvent(result=_make_result(ev.category, response, False,
                "Supervisor reached max_steps before an approved response.", trace, "max_steps"))
        return RespondEvent(ticket=ev.ticket, max_steps=ev.max_steps, trace=trace, category=ev.category,
                            classification=ev.classification, kb_context=ev.kb_context, billing_context=ev.billing_context)


class LlamaIndexTriageRunner:
    name = "llamaindex"

    def run(self, ticket: Ticket, *, llm: LLMClient, max_steps: int = 12) -> TriageResult:
        if not isinstance(ticket, Ticket):
            raise TypeError("ticket must be a Ticket")
        if isinstance(max_steps, bool) or not isinstance(max_steps, int) or max_steps < 1:
            raise ValueError("max_steps must be a positive integer")
        workflow = _TriageWorkflow(timeout=60)
        workflow._llm = llm
        event = TriageStart(ticket_id=ticket.id, subject=ticket.subject, description=ticket.description,
                            customer_id=ticket.customer_id, max_steps=max_steps)
        result = asyncio.run(self._invoke(workflow, event))
        return result

    async def _invoke(self, workflow: _TriageWorkflow, event: TriageStart) -> TriageResult:
        result = await workflow.run(start_event=event)
        return result


def _make_result(category: str, response: str, approved: bool, reason: str,
                 trace_rows: list[dict[str, Any]], stop: str) -> TriageResult:
    trace = [StepRecord(**row) for row in trace_rows]
    decision = TriageDecision("respond" if approved else "escalate", category, response, approved, reason)
    return TriageResult(decision, trace, Usage(), stop)
