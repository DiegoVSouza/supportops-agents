"""Sealed one-trial live smoke for the five non-Core framework adapters."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from decimal import Decimal
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
LAB = PROJECT.parents[1]
CAMPAIGN = "p01-framework-smoke-v3"
AUTH = ".planning/llm-live-readiness/phases/069-p01-framework-smoke-completion/AUTHORIZATION.json"
CASE_IDS = [
    "p01-framework-crewai",
    "p01-framework-autogen",
    "p01-framework-semantic-kernel",
    "p01-framework-llamaindex",
]
RUNNERS = ["crewai", "autogen", "semantic_kernel", "llamaindex"]
OWN = [p for p in (PROJECT / "src/supportops_agents").rglob("*.py")]
OWN += [PROJECT / name for name in (
    "scripts/campaign_ledger.py", "scripts/run_live_campaign.py", "scripts/run_live_groq_eval.py",
    "scripts/framework_smoke.py", "agent/prompts/live-core.md", "evals/live-execution.json",
    "evals/live-campaign.json", "evals/datasets/live-v1/cases.jsonl",
    "evals/datasets/live-v1/manifest.json", "evals/rubrics/live-v1/rubric.md", "pyproject.toml", "uv.lock",
)]
SHARED = [LAB / name for name in (
    "scripts/harness/live_free_account.py", "scripts/harness/live_provider_transport.py",
    "shared/policies/groq-free-campaign.json", AUTH,
)]


class SmokeBlocked(RuntimeError):
    pass


def git(repository: Path, *args: str) -> str:
    import subprocess

    result = subprocess.run(["git", *args], cwd=repository, capture_output=True, timeout=20)
    if result.returncode:
        raise SmokeBlocked("source_provenance")
    return result.stdout.decode().strip()


def candidate_cases() -> list[dict[str, str]]:
    source = PROJECT / "evals/datasets/live-v1/cases.jsonl"
    rows = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines() if line]
    development = [row for row in rows if row["split"] == "development"]
    if len(development) < len(RUNNERS):
        raise SmokeBlocked("development_cases_missing")
    return [
        {"case_id": case_id, "input": row["input"], "runner": runner, "max_steps": 4}
        for case_id, runner, row in zip(CASE_IDS, RUNNERS, development[: len(RUNNERS)], strict=True)
    ]


def source_paths() -> dict[str, Path]:
    paths = {"projects/p01/" + path.relative_to(PROJECT).as_posix(): path for path in OWN}
    paths.update({path.relative_to(LAB).as_posix(): path for path in SHARED})
    return paths


def freeze() -> dict:
    import subprocess

    sys.path.insert(0, str(LAB / "scripts/harness"))
    from live_free_account import SharedAccount

    policy = json.loads((LAB / "shared/policies/groq-free-campaign.json").read_text(encoding="utf-8"))
    account = SharedAccount(LAB, policy)
    if account._p01_campaigns().get(CAMPAIGN) != 20:
        raise SmokeBlocked("campaign_authorization_missing")
    history = account._history()
    if any(row["event"] == "reserved" for row in history):
        raise SmokeBlocked("uncertain_attempt_requires_reconciliation")
    if any(row["project"] == "p01" and row["campaign"] == CAMPAIGN for row in history):
        raise SmokeBlocked("campaign_already_started_no_replay")

    for repository, paths in ((PROJECT, OWN), (LAB, SHARED)):
        relative = [path.relative_to(repository).as_posix() for path in paths]
        for command in (["git", "ls-files", "--error-unmatch", "--", *relative],
                        ["git", "diff", "--quiet", "HEAD", "--", *relative]):
            if subprocess.run(command, cwd=repository, capture_output=True, timeout=20).returncode:
                raise SmokeBlocked("source_not_committed_or_modified")
    candidate = git(PROJECT, "rev-parse", "HEAD")
    manifest = {
        "campaign_id": CAMPAIGN,
        "candidate_commit": candidate,
        "stage": "development",
        "sampling_order": CASE_IDS,
        "trials_per_case": 1,
        "files_sha256": {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in source_paths().items()},
    }
    directory = PROJECT / "artifacts/evals/live" / CAMPAIGN
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / "manifest.json"
    if target.exists():
        previous = json.loads(target.read_text(encoding="utf-8"))
        comparable = {key: value for key, value in manifest.items() if key != "frozen_at"}
        prior_comparable = {key: value for key, value in previous.items() if key != "frozen_at"}
        if comparable == prior_comparable:
            return previous
        project_ledger = PROJECT / "artifacts/evals/live/ledger.sqlite"
        if project_ledger.exists():
            import sqlite3
            with sqlite3.connect(project_ledger.resolve().as_uri() + "?mode=ro", uri=True) as db:
                if db.execute("SELECT 1 FROM events WHERE campaign_id=? LIMIT 1", (CAMPAIGN,)).fetchone():
                    raise SmokeBlocked("campaign_already_started_no_replay")
        usage_ledger = PROJECT / "artifacts/evals/live/provider-usage.sqlite"
        if usage_ledger.exists():
            import sqlite3
            with sqlite3.connect(usage_ledger.resolve().as_uri() + "?mode=ro", uri=True) as db:
                if db.execute("SELECT 1 FROM usage_events WHERE campaign=? LIMIT 1", (CAMPAIGN,)).fetchone():
                    raise SmokeBlocked("campaign_already_started_no_replay")
        backup = directory / f"manifest-pre-dispatch-{previous.get('candidate_commit', 'unknown')[:12]}.json"
        if backup.exists():
            raise SmokeBlocked("prior_manifest_backup_exists")
        target.rename(backup)
    with target.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(manifest, stream, indent=2, sort_keys=True)
        stream.write("\n")
    return manifest


def validate_manifest() -> None:
    directory = PROJECT / "artifacts/evals/live" / CAMPAIGN
    try:
        manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise SmokeBlocked("manifest_missing") from None
    expected = {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in source_paths().items()}
    if (manifest.get("campaign_id") != CAMPAIGN or manifest.get("stage") != "development"
            or manifest.get("sampling_order") != CASE_IDS or manifest.get("trials_per_case") != 1
            or manifest.get("candidate_commit") != git(PROJECT, "rev-parse", "HEAD")
            or manifest.get("files_sha256") != expected):
        raise SmokeBlocked("manifest_mismatch")


def run(max_workflows: int = 4) -> int:
    import os
    for path in (PROJECT, PROJECT / "src", LAB / "scripts/harness"):
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))
    from scripts.campaign_ledger import CampaignLedger, CampaignLease, CampaignBlocked
    from supportops_agents.accounted_live import BoundaryError, WorkflowBinding
    from supportops_agents.accounted_frameworks import run_live
    from live_free_account import AccountBlocked, SharedAccount, machine_lease

    if max_workflows != len(RUNNERS) or os.getenv("LLM_MODE") != "live":
        raise SmokeBlocked("explicit_live_mode_or_fixed_scope_required")
    policy = json.loads((LAB / "shared/policies/groq-free-campaign.json").read_text(encoding="utf-8"))
    account = SharedAccount(LAB, policy)
    with machine_lease(account.lock):
        if account._p01_campaigns().get(CAMPAIGN) != 20:
            raise SmokeBlocked("campaign_authorization_missing")
    owner = json.loads((PROJECT / "evals/live-execution.json").read_text(encoding="utf-8"))
    allocation = owner.get("allocations", {}).get(CAMPAIGN, {})
    if (CAMPAIGN not in owner.get("approved_campaigns", []) or allocation.get("stage") != "development"
            or allocation.get("case_ids") != CASE_IDS or allocation.get("max_trials") != len(RUNNERS)):
        raise SmokeBlocked("owner_allocation_mismatch")
    validate_manifest()
    cases = candidate_cases()
    ledger = CampaignLedger(PROJECT / "artifacts/evals/live/ledger.sqlite", campaign_id=CAMPAIGN)
    out = PROJECT / "artifacts/evals/live" / CAMPAIGN
    # CampaignLedger is shared by all P01 operations; retain its original product-wide ceiling.
    cap = {"requests": 744, "input_tokens": 1523712, "output_tokens": 190464,
           "estimated_cost_usd": Decimal("0.1714176")}
    totals = ledger.totals()
    planned_calls = len(RUNNERS) * 4
    planned = {"requests": planned_calls, "input_tokens": planned_calls * 2048,
               "output_tokens": planned_calls * 256,
               "estimated_cost_usd": planned_calls * Decimal("0.0002304")}
    if any(totals[field] + planned[field] > cap[field] for field in cap):
        raise SmokeBlocked("project_campaign_capacity_insufficient")
    report = {"campaign_id": CAMPAIGN, "status": "INCOMPLETE", "max_provider_calls": planned_calls, "trials": []}
    if ledger.reserved_trials():
        raise SmokeBlocked("campaign_already_started_no_replay")
    try:
        with CampaignLease(PROJECT / "artifacts/evals/live/campaign.lock", campaign_id=CAMPAIGN):
            for item in cases:
                case_id = item["case_id"]
                try:
                    ledger.reserve(case_id=case_id, trial=1, input_tokens=8192, output_tokens=1024,
                                   estimated_cost_usd=Decimal("0.0009216"), caps=cap, calls=4)
                except CampaignBlocked:
                    raise SmokeBlocked("project_campaign_capacity_exhausted") from None
                receipts = []
                try:
                    binding = WorkflowBinding(CAMPAIGN, case_id, 1)
                    _result, receipts = run_live(item["runner"], item, PROJECT, binding)
                    from supportops_agents.accounted_frameworks import valid_live_receipts
                    if not valid_live_receipts(receipts):
                        raise SmokeBlocked("workflow_receipt_incomplete")
                    usage = [receipt["usage"] for receipt in receipts if isinstance(receipt.get("usage"), dict)]
                    input_tokens = sum(row["input_tokens"] for row in usage)
                    output_tokens = sum(row["output_tokens"] for row in usage)
                    if len(receipts) > 4 or input_tokens > 8192 or output_tokens > 1024:
                        raise SmokeBlocked("workflow_usage_cap_exceeded")
                    cost = (Decimal(input_tokens) * Decimal("0.075") + Decimal(output_tokens) * Decimal("0.30")) / Decimal(1000000)
                    ledger.complete(case_id=case_id, trial=1, input_tokens=input_tokens, output_tokens=output_tokens,
                                    actual_cost_usd=cost, outcome="ok", error_class=None)
                    report["trials"].append({"case_id": case_id, "runner": item["runner"], "status": "ok",
                                             "provider_calls": len(receipts), "input_tokens": input_tokens,
                                             "output_tokens": output_tokens})
                except (BoundaryError, AccountBlocked, CampaignBlocked, SmokeBlocked) as error:
                    safe = error.diagnostic.get("reason", "workflow_incomplete") if isinstance(error, BoundaryError) else str(error)
                    usage = [receipt.get("usage") for receipt in receipts if isinstance(receipt.get("usage"), dict)]
                    input_tokens = sum(row["input_tokens"] for row in usage)
                    output_tokens = sum(row["output_tokens"] for row in usage)
                    cost = (Decimal(input_tokens) * Decimal("0.075") + Decimal(output_tokens) * Decimal("0.30")) / Decimal(1000000)
                    ledger.complete(case_id=case_id, trial=1, input_tokens=input_tokens or None,
                                    output_tokens=output_tokens or None, actual_cost_usd=cost if usage else None,
                                    outcome="incomplete", error_class=safe if safe.isascii() and safe.replace("_", "").isalnum() else "workflow_incomplete")
                    report["trials"].append({"case_id": case_id, "runner": item["runner"], "status": "incomplete"})
                    break
    finally:
        report["provider_calls"] = sum(row.get("provider_calls", 0) for row in report["trials"])
        report["status"] = "COMPLETE" if len(report["trials"]) == len(RUNNERS) and all(row["status"] == "ok" for row in report["trials"]) else "INCOMPLETE"
        (out / "framework-smoke-report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0 if report["status"] == "COMPLETE" else 2


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--freeze", action="store_true")
    group.add_argument("--execute-free", action="store_true")
    args = parser.parse_args()
    try:
        if args.freeze:
            manifest = freeze()
            print(json.dumps({"status": "FROZEN", "campaign_id": CAMPAIGN, "candidate_commit": manifest["candidate_commit"]}))
            return 0
        return run()
    except (SmokeBlocked, OSError, ValueError) as error:
        print(json.dumps({"status": "INCOMPLETE", "reason": str(error) if isinstance(error, SmokeBlocked) else "preflight_unavailable"}, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
