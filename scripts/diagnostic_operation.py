"""Explicitly reviewed single-use diagnostic; original operation remains blocked."""
import hashlib
import json
import os
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

from scripts.campaign_ledger import CampaignBlocked, CampaignLedger
from supportops_agents.accounted_live import AccountedCoreClient, BoundaryError, WorkflowBinding
from supportops_agents.contracts import Ticket
from supportops_agents.core import CoreTriageRunner

PROJECT = Path(__file__).resolve().parents[1]
LAB = PROJECT.parents[1]
CAMPAIGN = "local-diagnostic-v1"
CASE = "fixture-diagnostic-01"
MANIFEST = "artifacts/evals/live/local-diagnostic-v1/manifest.json"
TEXT = "Synthetic diagnostic only: provide a short general greeting for a support agent. No account, invoice, knowledge lookup, refund or external tool is available or requested."
CAPS = {"requests": 8, "input_tokens": 16384, "output_tokens": 2048, "estimated_cost_usd": Decimal("0.0018432")}


def git(project, *args):
    result = subprocess.run(["git", *args], cwd=project, capture_output=True, timeout=15)
    if result.returncode:
        raise CampaignBlocked("source_provenance")
    return result.stdout.decode().strip()


def paths(project):
    return sorted(p for p in git(project, "ls-files").splitlines()
                  if p.startswith(("src/", "scripts/", "tests/", "agent/", "evals/"))
                  or p in {"pyproject.toml", "uv.lock", "harness.yaml"})


def fingerprint(project=PROJECT, lab=LAB):
    own = paths(project)
    git(project, "diff", "--quiet", "HEAD", "--", *own)
    shared = ["scripts/harness/live_free_account.py", "scripts/harness/live_provider_transport.py",
              "shared/policies/groq-free-campaign.json",
              ".planning/llm-live-readiness/phases/033-p01-reviewed-diagnostic/AUTHORIZATION.json"]
    git(lab, "diff", "--quiet", "HEAD", "--", *shared)
    values = [("p01/" + p, hashlib.sha256((project / p).read_bytes()).hexdigest()) for p in own]
    values += [(p, hashlib.sha256((lab / p).read_bytes()).hexdigest()) for p in shared]
    return hashlib.sha256(json.dumps(values, separators=(",", ":")).encode()).hexdigest()


def validate(project=PROJECT, lab=LAB):
    try:
        manifest = json.loads((project / MANIFEST).read_text())
        owner = json.loads((project / "evals/live-execution.json").read_text())
    except (OSError, ValueError):
        raise CampaignBlocked("manifest_missing") from None
    if (manifest.get("campaign") != CAMPAIGN or manifest.get("case") != CASE
            or manifest.get("source_fingerprint") != fingerprint(project, lab)
            or CAMPAIGN not in owner.get("approved_campaigns", [])
            or manifest.get("authorization_id") != "p01-reviewed-diagnostic-v1"):
        raise CampaignBlocked("manifest_mismatch")
    candidate = manifest.get("candidate")
    if not isinstance(candidate, str) or len(candidate) != 40:
        raise CampaignBlocked("candidate_missing")
    git(project, "merge-base", "--is-ancestor", candidate, "HEAD")
    git(project, "diff", "--quiet", candidate, "--", *paths(project))


class Bridge:
    def __init__(self, factory, provenance):
        self.factory, self.session, self.provenance = factory, None, provenance

    def request(self, envelope):
        if self.session is None:
            self.session = self.factory()
        self.session.preview(envelope)
        return self.session.complete(envelope)

    def close(self):
        pass


def run(path, *, authority_check, session_factory, provenance="fixture", project=PROJECT):
    authority_check()
    ledger = CampaignLedger(path, campaign_id=CAMPAIGN)
    # The exact original history is checked by authority_check. Any diagnostic
    # reservation, completed or not, consumes the single approved invocation.
    if ledger.reserved_trials():
        raise CampaignBlocked("diagnostic_already_reserved")
    ledger.reserve(case_id=CASE, trial=1, calls=4, input_tokens=8192, output_tokens=1024,
                   estimated_cost_usd=Decimal("0.0009216"), caps=CAPS)
    client = AccountedCoreClient(Bridge(session_factory, provenance), WorkflowBinding(CAMPAIGN, CASE, 1), project=project)
    try:
        result = CoreTriageRunner().run(Ticket(CASE, "Synthetic greeting diagnostic", TEXT), llm=client)
        if not client.receipts or any(row["usage"] is None for row in client.receipts):
            raise CampaignBlocked("missing_accounted_receipt")
        inp = sum(row["usage"]["input_tokens"] for row in client.receipts)
        out = sum(row["usage"]["output_tokens"] for row in client.receipts)
        cost = (Decimal(inp) * Decimal("0.075") + Decimal(out) * Decimal("0.30")) / 1000000
        outcome = "ok" if result.stop_reason == "approved" else "incomplete"
        ledger.complete(case_id=CASE, trial=1, input_tokens=inp, output_tokens=out,
                        actual_cost_usd=cost, outcome=outcome, error_class=None if outcome == "ok" else "semantic")
        return {"status": "ok" if outcome == "ok" else "INCOMPLETE", "stop_reason": result.stop_reason,
                "calls": len(client.receipts), "input_tokens": inp, "output_tokens": out,
                "receipts": client.receipts, "original_reservation_retained": True}
    except (BoundaryError, CampaignBlocked) as error:
        # Preserve the entire reservation on any uncertain or invalid response.
        report = {"status": "INCOMPLETE", "calls": len(client.receipts), "receipts": client.receipts,
                  "diagnostic": error.diagnostic if isinstance(error, BoundaryError) else {"reason": "accounting"},
                  "original_reservation_retained": True, "diagnostic_reservation_retained": True}
        return report
    finally:
        client.close()


def main():
    if os.getenv("LLM_MODE", "fake") != "live":
        print(json.dumps({"status": "INCOMPLETE", "reason": "explicit_live_required"}))
        return 2
    try:
        validate()
        sys.path.insert(0, str(LAB / "scripts/harness"))
        from live_free_account import SharedAccount, machine_lease
        from live_provider_transport import ProviderSession
        policy = json.loads((LAB / "shared/policies/groq-free-campaign.json").read_text())
        account = SharedAccount(LAB, policy)
        with machine_lease(LAB / ".runtime/llm-live-readiness/campaign.lock"):
            def authority():
                validate()
                account._reviewed_p01_diagnostic(account._history(), CASE, 1)
            result = run(PROJECT / "artifacts/evals/live/ledger.sqlite", authority_check=authority,
                         session_factory=lambda: ProviderSession(LAB, "p01", policy), provenance="live")
        print(json.dumps(result))
        return 0 if result["status"] == "ok" else 2
    except Exception:
        print(json.dumps({"status": "INCOMPLETE", "reason": "diagnostic_blocked_or_uncertain"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
