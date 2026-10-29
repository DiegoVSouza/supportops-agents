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
    max_provider_calls = 4

    def run(self, ticket: Ticket, *, llm: LLMClient, max_steps: int = 4,
            fixture_dispatcher=None, fixture_run_id=None, fixture_tenant=None) -> TriageResult:
        if not isinstance(ticket, Ticket):
            raise TypeError("ticket must be a Ticket")
        if isinstance(max_steps, bool) or not isinstance(max_steps, int) or max_steps < 1:
            raise ValueError("max_steps must be a positive integer")
        if max_steps > self.max_provider_calls:
            raise ValueError("max_steps cannot exceed four for the Core runner")
        if any(value is not None for value in (fixture_dispatcher, fixture_run_id, fixture_tenant)):
            from .fakes import FakeLLMClient
            from .accounted_live import AccountedCoreClient
            from .synthetic_dispatch import SyntheticDispatcher
            fixture_client = (type(llm) is FakeLLMClient or
                (type(llm) is AccountedCoreClient and llm.transport.provenance == "fixture"))
            if (not fixture_client or type(fixture_dispatcher) is not SyntheticDispatcher
                    or not isinstance(fixture_run_id, str) or not isinstance(fixture_tenant, str)):
                raise ValueError("fixture dispatch requires a fake client and explicit fixture context")

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
                if "read_plan" in output:
                    plan = output["read_plan"]
                    if fixture_dispatcher is None or not isinstance(plan, dict) or set(plan) != {"tools"}:
                        raise InvalidAgentResponse("invalid fixture read plan")
                    tools = plan["tools"]
                    try:
                        results = fixture_dispatcher.run(fixture_run_id, tools, {"tenant": fixture_tenant})
                    except BaseException:
                        close = getattr(llm, "close", None)
                        if callable(close):
                            close()
                        raise
                    evidence = dict(zip(tools, results, strict=True))
                    state.kb_context = evidence.get("search_knowledge", "")
                    state.billing_context = evidence.get("lookup_billing", "")
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
