"""Offline controller for a future separately funded synthetic operation."""

from __future__ import annotations

import re
from decimal import Decimal
from pathlib import Path

from scripts.campaign_ledger import CampaignBlocked, CampaignLedger
from supportops_agents.accounted_live import AccountedCoreClient, WorkflowBinding
from supportops_agents.contracts import Ticket
from supportops_agents.core import CoreTriageRunner

CAMPAIGN = "local-operation-v1"
CAPS = {"requests": 8, "input_tokens": 16384, "output_tokens": 2048,
        "estimated_cost_usd": Decimal("0.0018432")}
WORKFLOW_COST = Decimal("0.0009216")


def run_fixture_operation(path: Path, request_id: str, text: str, *, lease, transport_factory):
    """Run only an injected fixture transport; no network or real allocation is enabled."""
    if (not isinstance(request_id, str) or not re.fullmatch(r"fixture-[A-Za-z0-9_-]{1,48}", request_id)
            or not isinstance(text, str) or not text.strip() or len(text.encode("utf-8")) > 512):
        raise CampaignBlocked("invalid_synthetic_request")
    with lease:
        ledger = CampaignLedger(path, campaign_id=CAMPAIGN)
        history = ledger.reserved_trials()
        latest = {}
        for row in history:
            latest[(row["case_id"], row["trial"])] = row
        if any(row["event"] != "completed" or row["outcome"] != "ok" for row in latest.values()):
            raise CampaignBlocked("prior_work_requires_review")
        ledger.reserve(case_id=request_id, trial=1, calls=4, input_tokens=8192,
                       output_tokens=1024, estimated_cost_usd=WORKFLOW_COST, caps=CAPS)
        transport = transport_factory()
        if getattr(transport, "provenance", None) != "fixture":
            raise CampaignBlocked("fixture_transport_required")
        client = AccountedCoreClient(transport, WorkflowBinding(CAMPAIGN, request_id, 1))
        try:
            result = CoreTriageRunner().run(Ticket(request_id, "Synthetic support request", text), llm=client)
            if not client.receipts or any(row["usage"] is None for row in client.receipts):
                raise CampaignBlocked("missing_accounted_receipt")
            input_tokens = sum(row["usage"]["input_tokens"] for row in client.receipts)
            output_tokens = sum(row["usage"]["output_tokens"] for row in client.receipts)
            cost = (Decimal(input_tokens) * Decimal("0.075") + Decimal(output_tokens) * Decimal("0.30")) / 1000000
            ledger.complete(case_id=request_id, trial=1, input_tokens=input_tokens, output_tokens=output_tokens,
                            actual_cost_usd=cost, outcome="ok", error_class=None)
            return {"status": "ok", "stop_reason": result.stop_reason, "calls": len(client.receipts)}
        finally:
            client.close()
