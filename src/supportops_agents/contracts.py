"""Local compatibility contracts until P00 publishes an approved domain package."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Mapping, Protocol


@dataclass(frozen=True)
class Ticket:
    id: str
    subject: str
    description: str
    customer_id: str = "synthetic-customer"


@dataclass(frozen=True)
class TriageDecision:
    action: Literal["respond", "escalate"]
    category: str
    response: str
    approved: bool
    reason: str = ""


@dataclass(frozen=True)
class StepRecord:
    step: int
    agent: str
    action: str
    detail: str


@dataclass(frozen=True)
class Usage:
    """Usage is intentionally unknown for deterministic local doubles."""

    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_usd: float | None = None


@dataclass(frozen=True)
class TriageResult:
    decision: TriageDecision
    trace: list[StepRecord]
    usage: Usage = field(default_factory=Usage)
    stop_reason: Literal["approved", "escalated", "max_steps"] = "approved"


class LLMClient(Protocol):
    """Small injectable boundary; implementations return agent-specific data."""

    def complete(self, agent: str, payload: Mapping[str, Any]) -> Mapping[str, Any]: ...


class TriageRunner(Protocol):
    name: str

    def run(self, ticket: Ticket, *, llm: LLMClient, max_steps: int = 12) -> TriageResult: ...
