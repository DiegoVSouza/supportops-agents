"""Deterministic supervisor-worker triage runner."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .contracts import LLMClient, StepRecord, Ticket, TriageDecision, TriageResult, Usage


class InvalidAgentResponse(ValueError):
    """Raised when an injected agent returns data outside its contract."""


@dataclass
class SharedState:
    ticket: Ticket
    category: str = "unknown"
    classification: str = ""
    kb_context: str = ""
    billing_context: str = ""
    response: str = ""
    approved: bool = False
    escalation_reason: str = ""
    trace: list[StepRecord] = field(default_factory=list)

    def as_payload(self) -> dict[str, Any]:
        return {
            "ticket": {"id": self.ticket.id, "subject": self.ticket.subject, "description": self.ticket.description,
                       "customer_id": self.ticket.customer_id},
            "category": self.category,
            "classification": self.classification,
            "kb_context": self.kb_context,
            "billing_context": self.billing_context,
            "response": self.response,
        }


class CoreTriageRunner:
    name = "core"

    def run(self, ticket: Ticket, *, llm: LLMClient, max_steps: int = 12) -> TriageResult:
        if not isinstance(ticket, Ticket):
            raise TypeError("ticket must be a Ticket")
        if isinstance(max_steps, bool) or not isinstance(max_steps, int) or max_steps < 1:
            raise ValueError("max_steps must be a positive integer")

        state = SharedState(ticket=ticket)
        workers = ("classifier", "kb_researcher", "billing_agent", "responder")
        while len(state.trace) < max_steps:
            agent = workers[min(len(state.trace), len(workers) - 1)]
            output = llm.complete(agent, state.as_payload())
            if not isinstance(output, dict):
                raise InvalidAgentResponse(f"{agent} must return a dictionary")
            step = len(state.trace) + 1

            if agent == "classifier":
                state.category = _required_text(output, "category", agent)
                state.classification = _required_text(output, "summary", agent)
                reason = output.get("escalate")
                if reason:
                    state.escalation_reason = str(reason)
                    state.trace.append(StepRecord(step, agent, "escalate", state.escalation_reason))
                    return _result(state, "escalated")
                state.trace.append(StepRecord(step, agent, "classify", state.classification))
            elif agent == "kb_researcher":
                state.kb_context = _required_text(output, "context", agent)
                state.trace.append(StepRecord(step, agent, "search_kb", state.kb_context))
            elif agent == "billing_agent":
                state.billing_context = _required_text(output, "context", agent)
                reason = output.get("escalate")
                if reason:
                    state.escalation_reason = str(reason)
                    state.trace.append(StepRecord(step, agent, "escalate", state.escalation_reason))
                    return _result(state, "escalated")
                state.trace.append(StepRecord(step, agent, "check_billing", state.billing_context))
            else:
                state.response = _required_text(output, "response", agent)
                state.approved = output.get("approved") is True
                state.trace.append(StepRecord(step, agent, "approve" if state.approved else "revise", state.response))
                if state.approved:
                    return _result(state, "approved")

        state.escalation_reason = "Supervisor reached max_steps before an approved response."
        return _result(state, "max_steps")


def _required_text(output: dict[str, Any], key: str, agent: str) -> str:
    value = output.get(key)
    if not isinstance(value, str) or not value.strip():
        raise InvalidAgentResponse(f"{agent} must return non-empty string '{key}'")
    return value.strip()


def _result(state: SharedState, stop_reason: str) -> TriageResult:
    action = "escalate" if stop_reason != "approved" else "respond"
    decision = TriageDecision(action=action, category=state.category, response=state.response,
                              approved=state.approved, reason=state.escalation_reason)
    return TriageResult(decision=decision, trace=list(state.trace), usage=Usage(), stop_reason=stop_reason)
