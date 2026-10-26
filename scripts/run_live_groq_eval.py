"""One budget-capped synthetic Core runner evaluation against Groq."""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path

from supportops_agents.contracts import Ticket
from supportops_agents.core import CoreTriageRunner
from supportops_agents.live_groq import (
    MODEL,
    GroqAgentClient,
    keys,
    preflight,
    require_live_mode,
)

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "evidence"
CAP = 0.01


def write_result(result: dict[str, object], code: int) -> None:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    suffix = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    (ARTIFACTS / f"phase-004-groq-live-{suffix}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (ARTIFACTS / f"phase-004-groq-live-{suffix}.txt").write_text(
        f"Command: LLM_MODE=live uv run --extra live python scripts/run_live_groq_eval.py\nExit code: {code}\nSanitized result: {json.dumps(result, sort_keys=True)}\n",
        encoding="utf-8",
    )


def main() -> int:
    result = {
        "provider": "groq",
        "model": MODEL,
        "started_at_utc": datetime.now(UTC).isoformat(),
        "budget_cap_usd": CAP,
        "status": "INCOMPLETE",
        "exit_code": 1,
    }
    code = 1
    client: GroqAgentClient | None = None
    try:
        require_live_mode(os.getenv("LLM_MODE"))
        credentials = keys()
        result["credential_count"] = len(credentials)
        result["model_available_key_count"] = preflight(credentials)
        client = GroqAgentClient(credentials)
        ticket = Ticket(
            id="synthetic-p01-001",
            subject="How are duplicate charges reviewed?",
            description="Please explain the support process for checking a possible duplicate charge. I am asking about the policy, not requesting a refund.",
        )
        run = CoreTriageRunner().run(ticket, llm=client, max_steps=4)
        decision = run.decision
        checks = {
            "approved": decision.approved is True,
            "action": decision.action == "respond",
            "category": bool(decision.category),
            "four_steps": len(run.trace) == 4,
            "step_order": [x.agent for x in run.trace]
            == ["classifier", "kb_researcher", "billing_agent", "responder"],
        }
        result.update(
            status="PASS" if all(checks.values()) else "FAIL",
            failure_category=None
            if all(checks.values())
            else "domain_assertion_mismatch",
            assertions=checks,
            action=decision.action,
            category=decision.category,
            step_count=len(run.trace),
            agent_order=[x.agent for x in run.trace],
            api_calls=client.calls,
            input_tokens=client.input_tokens,
            output_tokens=client.output_tokens,
            estimated_cost_usd=round(client.estimated_cost_usd, 8),
        )
        code = 0 if all(checks.values()) else 1
    except Exception as exc:
        safe_error = {"class": type(exc).__name__}
        if client is not None and client.last_failure:
            safe_error.update(client.last_failure)
        elif type(exc).__name__ == "InvalidAgentResponse":
            safe_error["category"] = "agent_contract"
            safe_error["contract_issue"] = str(exc)
        elif "budget preflight" in str(exc):
            safe_error["category"] = "budget_preflight"
        result["error"] = safe_error
        code = 1
    result.update(exit_code=code, finished_at_utc=datetime.now(UTC).isoformat())
    write_result(result, code)
    print(json.dumps(result, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
