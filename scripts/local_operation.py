"""Offline controller for a future separately funded synthetic operation."""

from __future__ import annotations

import re
import argparse
import json
import os
import sys
import sqlite3
from contextlib import closing
from decimal import Decimal
from pathlib import Path

from scripts.campaign_ledger import CampaignBlocked, CampaignLedger
from supportops_agents.accounted_live import AccountedCoreClient, BoundaryError, SubprocessGuard, WorkflowBinding
from supportops_agents.contracts import Ticket
from supportops_agents.core import CoreTriageRunner

CAMPAIGN = "local-operation-v1"
CAPS = {"requests": 8, "input_tokens": 16384, "output_tokens": 2048,
        "estimated_cost_usd": Decimal("0.0018432")}
WORKFLOW_COST = Decimal("0.0009216")
PROJECT = Path(__file__).resolve().parents[1]
LAB = PROJECT.parents[1]
CASES = {"fixture-local-01": "Synthetic ticket: explain how to check an invoice status.",
         "fixture-local-02": "Synthetic ticket: ask where to find a tracking link."}


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


def run_live_operation(request_id: str):
    if os.getenv("LLM_MODE") != "live" or request_id not in CASES:
        raise CampaignBlocked("explicit_synthetic_live_operation_required")
    sys.path.insert(0, str(LAB / "scripts/harness"))
    from live_free_account import machine_lease

    path = PROJECT / "artifacts/evals/live/ledger.sqlite"
    with machine_lease(LAB / ".runtime/llm-live-readiness/campaign.lock"):
        ledger = CampaignLedger(path, campaign_id=CAMPAIGN)
        latest = {}
        for row in ledger.reserved_trials():
            latest[(row["case_id"], row["trial"])] = row
        if any(row["event"] != "completed" or row["outcome"] != "ok" for row in latest.values()):
            raise CampaignBlocked("prior_work_requires_review")
        ledger.reserve(case_id=request_id, trial=1, calls=4, input_tokens=8192,
                       output_tokens=1024, estimated_cost_usd=WORKFLOW_COST, caps=CAPS)
        binding = WorkflowBinding(CAMPAIGN, request_id, 1)
        client = AccountedCoreClient(SubprocessGuard(binding), binding)
        try:
            result = CoreTriageRunner().run(Ticket(request_id, "Synthetic support request", CASES[request_id]), llm=client)
            if not client.receipts or any(row["usage"] is None for row in client.receipts):
                raise CampaignBlocked("missing_accounted_receipt")
            used_input = sum(row["usage"]["input_tokens"] for row in client.receipts)
            used_output = sum(row["usage"]["output_tokens"] for row in client.receipts)
            cost = (Decimal(used_input) * Decimal("0.075") + Decimal(used_output) * Decimal("0.30")) / 1000000
            ledger.complete(case_id=request_id, trial=1, input_tokens=used_input, output_tokens=used_output,
                            actual_cost_usd=cost, outcome="ok", error_class=None)
            return {"status": "ok", "stop_reason": result.stop_reason, "calls": len(client.receipts)}
        finally:
            client.close()


def reconcile_interrupted_fixture(*, ledger_path, provider_path, lease):
    """Finalize only the observed interrupted workflow, retaining its entire reservation."""
    with lease:
        ledger = CampaignLedger(ledger_path, campaign_id=CAMPAIGN, read_only=True)
        events = ledger.reserved_trials()
        if len(events) != 1 or events[0]["case_id"] != "fixture-local-01" or events[0]["trial"] != 1 or events[0]["event"] != "reserved":
            raise CampaignBlocked("unexpected_logical_history")
        with closing(sqlite3.connect(Path(ledger_path).resolve().as_uri() + "?mode=ro", uri=True)) as db:
            reservation = db.execute("SELECT reserved_calls,reserved_input_tokens,reserved_output_tokens,reserved_cost_usd FROM events WHERE campaign_id=? AND case_id=? AND trial=1 AND event='reserved'", (CAMPAIGN, "fixture-local-01")).fetchone()
        if reservation != (4, 8192, 1024, "0.0009216"):
            raise CampaignBlocked("unexpected_logical_reservation")
        with closing(sqlite3.connect(Path(provider_path).resolve().as_uri() + "?mode=ro", uri=True)) as db:
            if db.execute("SELECT COUNT(*) FROM usage_events WHERE campaign != ? OR case_id != ? OR trial != 1", (CAMPAIGN, "fixture-local-01")).fetchone()[0]:
                raise CampaignBlocked("unexpected_provider_history")
            rows = db.execute("SELECT call_index,event,status,actual_input,actual_output FROM usage_events WHERE campaign=? AND case_id=? AND trial=1 ORDER BY ordinal", (CAMPAIGN, "fixture-local-01")).fetchall()
        if rows != [(1, "reserved", None, None, None), (1, "completed", "ok", 235, 46),
                    (2, "reserved", None, None, None), (2, "completed", "ok", 228, 183)]:
            raise CampaignBlocked("unexpected_provider_history")
        writable = CampaignLedger(ledger_path, campaign_id=CAMPAIGN)
        writable.complete(case_id="fixture-local-01", trial=1, input_tokens=None, output_tokens=None,
                          actual_cost_usd=None, outcome="incomplete", error_class="unknown")
        return {"status": "INCOMPLETE", "reason": "failure_category_not_preserved",
                "reservation_retained": True, "provider_calls": 2}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request-id", required=True, choices=sorted(CASES))
    args = parser.parse_args()
    try:
        print(json.dumps(run_live_operation(args.request_id)))
        return 0
    except BoundaryError as error:
        print(json.dumps({"status": "INCOMPLETE", "diagnostic": error.diagnostic}))
        return 2
    except Exception:
        print(json.dumps({"status": "INCOMPLETE", "reason": "operation_blocked_or_uncertain"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
