"""LangGraph adapter with parallel workers, SQLite persistence, retries, and HITL."""

from __future__ import annotations

import operator
import os
import sqlite3
from hashlib import sha256
from pathlib import Path
from typing import Annotated, Any, TypedDict
from uuid import uuid4

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, RetryPolicy, interrupt

from ..contracts import LLMClient, StepRecord, Ticket, TriageDecision, TriageResult, Usage
from ..core import InvalidAgentResponse, _required_text


class GraphState(TypedDict, total=False):
    ticket: dict[str, str]
    category: str
    classification: str
    kb_context: str
    billing_context: str
    refund_amount: float
    escalation_reason: str
    response: str
    approved: bool
    max_steps: int
    trace: Annotated[list[dict[str, Any]], operator.add]


class LangGraphTriageRunner:
    name = "langgraph"

    def __init__(self, checkpoint_path: str | Path | None = None, refund_limit: float = 100.0):
        self.checkpoint_path = Path(checkpoint_path or os.environ.get(
            "SUPPORTOPS_LANGGRAPH_DB", "artifacts/langgraph-checkpoints.sqlite"
        ))
        self.refund_limit = refund_limit
        self._threads: dict[str, str] = {}

    def run(self, ticket: Ticket, *, llm: LLMClient, max_steps: int = 12,
            resume_key: str | None = None) -> TriageResult:
        _validate_run(ticket, max_steps)
        if resume_key is not None and (not isinstance(resume_key, str) or not resume_key.strip()):
            raise ValueError("resume_key must be a non-empty string")
        thread = _resume_thread_id(ticket.id, resume_key) if resume_key is not None else f"run:{uuid4().hex}"
        self._threads[ticket.id] = thread
        state = _initial_state(ticket, max_steps)
        result = self._invoke(state, llm, thread)
        if result.get("__interrupt__"):
            return _result(result, "escalated", "Human approval is pending; resume this runner with resume().")
        return _finish(result)

    def resume(self, ticket: Ticket, *, llm: LLMClient, approved: bool,
               resume_key: str | None = None) -> TriageResult:
        """Resume a pending interrupt using its explicit key or this runner's latest run."""
        if not isinstance(ticket, Ticket):
            raise TypeError("ticket must be a Ticket")
        if not isinstance(approved, bool):
            raise TypeError("approved must be bool")
        if resume_key is not None and (not isinstance(resume_key, str) or not resume_key.strip()):
            raise ValueError("resume_key must be a non-empty string")
        thread = (_resume_thread_id(ticket.id, resume_key) if resume_key is not None
                  else self._threads.get(ticket.id))
        if thread is None:
            raise ValueError("no run is available to resume; supply its resume_key")
        state = self._invoke(Command(resume=approved), llm, thread)
        return _finish(state)

    def _invoke(self, state: GraphState | Command, llm: LLMClient, thread: str) -> dict[str, Any]:
        self.checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        with SqliteSaver.from_conn_string(str(self.checkpoint_path)) as saver:
            graph = _build_graph(llm, self.refund_limit, saver)
            return graph.invoke(state, {"configurable": {"thread_id": thread}})


def _build_graph(llm: LLMClient, refund_limit: float, checkpointer: SqliteSaver):
    def classifier(state: GraphState) -> dict[str, Any]:
        output = llm.complete("classifier", state)
        category = _required_text(dict(output), "category", "classifier")
        summary = _required_text(dict(output), "summary", "classifier")
        escalation = str(output.get("escalate", ""))
        return {"category": category, "classification": summary, "escalation_reason": escalation,
                "trace": [_record(1, "classifier", "escalate" if escalation else "classify", summary)]}

    def researcher(state: GraphState) -> dict[str, Any]:
        output = llm.complete("kb_researcher", state)
        context = _required_text(dict(output), "context", "kb_researcher")
        return {"kb_context": context, "trace": [_record(2, "kb_researcher", "search_kb", context)]}

    def billing(state: GraphState) -> dict[str, Any]:
        output = llm.complete("billing_agent", state)
        context = _required_text(dict(output), "context", "billing_agent")
        amount = output.get("refund_amount", 0)
        if isinstance(amount, bool) or not isinstance(amount, (int, float)) or amount < 0:
            raise InvalidAgentResponse("billing_agent refund_amount must be a non-negative number")
        escalation = str(output.get("escalate", ""))
        if amount > refund_limit:
            approved = interrupt({"kind": "refund_approval", "ticket_id": state["ticket"]["id"],
                                  "refund_amount": amount, "limit": refund_limit})
            if not approved:
                escalation = "Human denied refund approval."
            else:
                escalation = ""
        return {"billing_context": context, "refund_amount": amount, "escalation_reason": escalation,
                "trace": [_record(3, "billing_agent", "escalate" if escalation else "check_billing", context)]}

    def limited_research(state: GraphState) -> dict[str, Any]:
        output = llm.complete("kb_researcher", state)
        context = _required_text(dict(output), "context", "kb_researcher")
        return {"kb_context": context, "trace": [_record(2, "kb_researcher", "search_kb", context)]}

    def responder(state: GraphState) -> dict[str, Any]:
        output = llm.complete("responder", state)
        response = _required_text(dict(output), "response", "responder")
        approved = output.get("approved") is True
        step = len(state.get("trace", [])) + 1
        return {"response": response, "approved": approved,
                "trace": [_record(step, "responder", "approve" if approved else "revise", response)]}

    def budget_end(state: GraphState) -> dict[str, Any]:
        if state.get("escalation_reason"):
            return {}
        return {"escalation_reason": "Supervisor reached max_steps before an approved response."}

    def after_workers_node(state: GraphState) -> dict[str, Any]:
        return {}

    builder = StateGraph(GraphState)
    retry = RetryPolicy(max_attempts=2, retry_on=(TimeoutError, ConnectionError))
    builder.add_node("classifier", classifier, retry_policy=retry)
    builder.add_node("kb_researcher", researcher, retry_policy=retry)
    builder.add_node("billing_agent", billing, retry_policy=retry)
    builder.add_node("limited_research", limited_research, retry_policy=retry)
    builder.add_node("responder", responder, retry_policy=retry)
    builder.add_node("budget_end", budget_end)
    builder.add_node("after_workers", after_workers_node)
    builder.add_edge(START, "classifier")

    def after_classifier(state: GraphState) -> str:
        if state.get("escalation_reason"):
            return "budget_end"
        remaining = state["max_steps"] - len(state.get("trace", []))
        if remaining <= 0:
            return "budget_end"
        return "limited_research" if remaining == 1 else "parallel_workers"

    builder.add_conditional_edges("classifier", after_classifier,
                                  {"budget_end": "budget_end", "limited_research": "limited_research",
                                   "parallel_workers": "fanout"})
    builder.add_node("fanout", lambda state: {}, defer=True)
    builder.add_edge("fanout", "kb_researcher")
    builder.add_edge("fanout", "billing_agent")
    builder.add_edge(["kb_researcher", "billing_agent"], "after_workers")
    builder.add_edge("limited_research", "budget_end")

    def after_workers(state: GraphState) -> str:
        if state.get("escalation_reason") or len(state.get("trace", [])) >= state["max_steps"]:
            return "budget_end"
        return "responder"

    builder.add_conditional_edges("after_workers", after_workers,
                                  {"budget_end": "budget_end", "responder": "responder"})

    builder.add_conditional_edges("responder", lambda state: "approved" if state.get("approved") else
                                  ("budget_end" if len(state.get("trace", [])) >= state["max_steps"] else "responder"),
                                  {"approved": END, "budget_end": "budget_end", "responder": "responder"})
    builder.add_edge("budget_end", END)
    return builder.compile(checkpointer=checkpointer)


def _validate_run(ticket: Ticket, max_steps: int) -> None:
    if not isinstance(ticket, Ticket):
        raise TypeError("ticket must be a Ticket")
    if isinstance(max_steps, bool) or not isinstance(max_steps, int) or max_steps < 1:
        raise ValueError("max_steps must be a positive integer")


def _resume_thread_id(ticket_id: str, resume_key: str) -> str:
    identity = sha256(f"{ticket_id}\0{resume_key}".encode("utf-8")).hexdigest()
    return f"resume:{identity}"


def _initial_state(ticket: Ticket, max_steps: int) -> GraphState:
    return {"ticket": {"id": ticket.id, "subject": ticket.subject, "description": ticket.description,
                        "customer_id": ticket.customer_id}, "category": "unknown", "classification": "",
            "kb_context": "", "billing_context": "", "escalation_reason": "", "response": "",
            "approved": False, "max_steps": max_steps, "trace": []}


def _finish(state: dict[str, Any]) -> TriageResult:
    if state.get("escalation_reason") == "Supervisor reached max_steps before an approved response.":
        return _result(state, "max_steps", str(state["escalation_reason"]))
    if state.get("escalation_reason"):
        return _result(state, "escalated", str(state["escalation_reason"]))
    if state.get("approved"):
        return _result(state, "approved", "")
    return _result(state, "max_steps", "Supervisor reached max_steps before an approved response.")


def _result(state: dict[str, Any], stop_reason: str, reason: str) -> TriageResult:
    decision = TriageDecision(action="respond" if stop_reason == "approved" else "escalate",
                              category=state.get("category", "unknown"), response=state.get("response", ""),
                              approved=state.get("approved", False), reason=reason)
    trace = tuple(StepRecord(**item) if isinstance(item, dict) else item for item in state.get("trace", []))
    return TriageResult(decision=decision, trace=list(trace), usage=Usage(), stop_reason=stop_reason)


def _record(step: int, agent: str, action: str, detail: str) -> dict[str, Any]:
    return {"step": step, "agent": agent, "action": action, "detail": detail}
