"""Legacy live names retained behind the mandatory accounted boundary.

The direct SDK/key-rotation path is intentionally unavailable. New Core callers
use AccountedCoreClient with the shared account transport; fake stays offline.
"""

from __future__ import annotations

from typing import Any, Mapping

MODEL = "openai/gpt-oss-20b"
CAP_USD = 0.01
INPUT_RATE = 0.075
OUTPUT_RATE = 0.30
AGENT_FIELDS = {
    "classifier": {"category": "billing", "summary": "...", "escalate": ""},
    "kb_researcher": {"context": "..."},
    "billing_agent": {"context": "...", "escalate": ""},
    "responder": {"response": "...", "approved": True},
}


def _guard_required():
    raise RuntimeError("accounted_guard_required; legacy direct provider access is disabled")


def _new_groq(**kwargs):
    return _guard_required()


def root_env() -> None:
    _guard_required()


def keys() -> list[str]:
    return _guard_required()


def require_live_mode(value: str | None) -> None:
    if (value or "").strip().lower() != "live":
        raise RuntimeError("explicit LLM_MODE=live required")


def retry_delay(attempt: int, status: int | None, retry_after) -> float:
    return _guard_required()


class GroqAgentClient:
    """Compatibility name that refuses unaccounted provider calls."""

    def __init__(
        self,
        api_keys: list[str],
        *,
        max_output_tokens: int = 256,
        budget_usd: float = CAP_USD,
    ) -> None:
        if not api_keys or max_output_tokens < 1:
            raise ValueError("keys and a positive completion limit are required")
        # Do not retain credentials, load .env, or initialize any SDK.
        self.calls = 0
        self.input_tokens = 0
        self.output_tokens = 0
        self.estimated_cost_usd = 0.0
        self.last_failure: dict[str, Any] | None = None

    def complete(self, agent: str, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        if agent not in AGENT_FIELDS:
            raise ValueError("unknown agent contract")
        return _guard_required()


def preflight(api_keys: list[str], model: str = MODEL) -> int:
    if model != MODEL:
        raise ValueError("only the approved evaluation model is configured")
    return _guard_required()
