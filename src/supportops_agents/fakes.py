"""Scriptable fake LLM boundary for deterministic local behavior tests."""

from collections import defaultdict, deque
from typing import Any, Mapping


DEFAULTS: dict[str, dict[str, Any]] = {
    "classifier": {"category": "billing", "summary": "Customer asks about a duplicate charge."},
    "kb_researcher": {"context": "Billing policy: verify a charge before promising a refund."},
    "billing_agent": {"context": "One duplicate charge was found; refund requires review."},
    "responder": {"response": "We found the duplicate charge and will review it.", "approved": True},
}


class FakeLLMClient:
    def __init__(self, responses: Mapping[str, list[dict[str, Any]]] | None = None):
        self._responses = {name: deque(items) for name, items in (responses or {}).items()}
        self._last_responses = {name: items[-1] for name, items in (responses or {}).items() if items}
        self.calls: list[tuple[str, Mapping[str, Any]]] = []

    def complete(self, agent: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        self.calls.append((agent, payload))
        queued = self._responses.get(agent)
        if queued:
            response = queued.popleft()
            self._last_responses[agent] = response
            return response
        if agent in self._last_responses:
            return dict(self._last_responses[agent])
        return dict(DEFAULTS[agent])
