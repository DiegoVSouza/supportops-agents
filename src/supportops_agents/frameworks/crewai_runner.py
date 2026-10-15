"""CrewAI Flow adapter for deterministic fake-mode SupportOps triage."""

from __future__ import annotations

from typing import Any

from pydantic import PrivateAttr
from crewai.flow.flow import Flow, listen, start

from ..contracts import LLMClient, StepRecord, Ticket, TriageDecision, TriageResult, Usage
from ..core import _required_text


class _TriageFlow(Flow):
    _llm: Any = PrivateAttr()
    _ticket: Ticket = PrivateAttr()
    _max_steps: int = PrivateAttr(default=12)
    _trace: list[StepRecord] = PrivateAttr(default_factory=list)
    _category: str = PrivateAttr(default="unknown")
    _response: str = PrivateAttr(default="")
    _approved: bool = PrivateAttr(default=False)
    _reason: str = PrivateAttr(default="")
    _final: Any = PrivateAttr(default=None)

    @start()
    def classify(self) -> None:
        if not self._room("classifier"):
            return
        output = dict(self._llm.complete("classifier", _payload(self._ticket)))
        self._category = _required_text(output, "category", "classifier")
        summary = _required_text(output, "summary", "classifier")
        self._reason = str(output.get("escalate", ""))
        self._trace.append(StepRecord(len(self._trace) + 1, "classifier", "escalate" if self._reason else "classify", summary))

    @listen(classify)
    def research(self) -> None:
        if self._reason or not self._room("kb_researcher"):
            return
        output = dict(self._llm.complete("kb_researcher", _payload(self._ticket, category=self._category)))
        context = _required_text(output, "context", "kb_researcher")
        self._trace.append(StepRecord(len(self._trace) + 1, "kb_researcher", "search_kb", context))

    @listen(research)
    def billing(self) -> None:
        if self._reason or not self._room("billing_agent"):
            return
        output = dict(self._llm.complete("billing_agent", _payload(self._ticket, category=self._category)))
        context = _required_text(output, "context", "billing_agent")
        self._reason = str(output.get("escalate", ""))
        self._trace.append(StepRecord(len(self._trace) + 1, "billing_agent", "escalate" if self._reason else "check_billing", context))

    @listen(billing)
    def respond(self) -> TriageResult:
        if not self._reason:
            while self._room("responder"):
                output = dict(self._llm.complete("responder", _payload(self._ticket, category=self._category)))
                self._response = _required_text(output, "response", "responder")
                self._approved = output.get("approved") is True
                self._trace.append(StepRecord(len(self._trace) + 1, "responder", "approve" if self._approved else "revise", self._response))
                if self._approved:
                    break
        if self._reason.startswith("Supervisor reached max_steps"):
            stop = "max_steps"
        elif self._reason:
            stop = "escalated"
        elif self._approved:
            stop = "approved"
        else:
            stop = "max_steps"
            self._reason = "Supervisor reached max_steps before an approved response."
        self._final = _result(self._category, self._response, self._approved, self._reason, self._trace, stop)
        return self._final

    def _room(self, agent: str) -> bool:
        if len(self._trace) < self._max_steps:
            return True
        self._reason = self._reason or f"Supervisor reached max_steps before {agent}."
        return False


class CrewAITriageRunner:
    name = "crewai"

    def run(self, ticket: Ticket, *, llm: LLMClient, max_steps: int = 12) -> TriageResult:
        _validate(ticket, max_steps)
        flow = _TriageFlow(suppress_flow_events=True)
        flow._ticket, flow._llm, flow._max_steps = ticket, llm, max_steps
        flow.kickoff()
        return flow._final


def _validate(ticket: Ticket, max_steps: int) -> None:
    if not isinstance(ticket, Ticket):
        raise TypeError("ticket must be a Ticket")
    if isinstance(max_steps, bool) or not isinstance(max_steps, int) or max_steps < 1:
        raise ValueError("max_steps must be a positive integer")


def _payload(ticket: Ticket, **state: Any) -> dict[str, Any]:
    return {"ticket": {"id": ticket.id, "subject": ticket.subject, "description": ticket.description,
                        "customer_id": ticket.customer_id}, **state}


def _result(category: str, response: str, approved: bool, reason: str, trace: list[StepRecord], stop: str) -> TriageResult:
    return TriageResult(TriageDecision("respond" if stop == "approved" else "escalate", category, response,
                                       approved, reason), list(trace), Usage(), stop)
