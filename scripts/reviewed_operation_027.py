"""Single-use, explicitly authorized local synthetic revalidation for P01."""

from __future__ import annotations

import hashlib
import argparse
import json
import os
import subprocess
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any

from scripts.campaign_ledger import CampaignBlocked, CampaignLedger
from supportops_agents.accounted_live import (
    AccountedCoreClient,
    BoundaryError,
    WorkflowBinding,
)
from supportops_agents.contracts import Ticket
from supportops_agents.core import CoreTriageRunner

PROJECT = Path(__file__).resolve().parents[1]
LAB = PROJECT.parents[1]
CAMPAIGN = "local-reviewed-operation-027-v1"
CASE = "fixture-reviewed-operation-027"
AUTH_ID = "p01-p04-reviewed-revalidation-v1"
MANIFEST = f"artifacts/evals/live/{CAMPAIGN}/manifest.json"
START = "artifacts/evidence/reviewed-operation-027/attempt.json"
INVOCATION = "artifacts/evidence/reviewed-operation-027/invocation.json"
RESULT = "artifacts/evidence/reviewed-operation-027/live-result.json"
TEXT = (
    "Synthetic local revalidation: give a short general greeting for a support agent. "
    "No account, invoice, knowledge lookup, refund, customer data, or external tool is available or requested."
)
CAPS = {
    "requests": 16,
    "input_tokens": 32768,
    "output_tokens": 4096,
    "estimated_cost_usd": Decimal("0.0036864"),
}
WORKFLOW_RESERVE = {
    "calls": 4,
    "input_tokens": 8192,
    "output_tokens": 1024,
    "estimated_cost_usd": Decimal("0.0009216"),
}
ROOT_SOURCES = (
    "scripts/harness/live_free_account.py",
    "scripts/harness/live_provider_transport.py",
    "shared/policies/groq-free-campaign.json",
    ".planning/llm-live-readiness/phases/039-p01-p04-reviewed-revalidation/AUTHORIZATION.json",
)
OPERATION_OWN_SOURCES = (
    "scripts/reviewed_operation_027.py",
    "scripts/campaign_ledger.py",
    "scripts/run_live_campaign.py",
    "scripts/run_live_groq_eval.py",
    "agent/prompts/live-core.md",
    "evals/live-execution.json",
    "evals/live-campaign.json",
    "evals/datasets/live-v1/cases.jsonl",
    "evals/datasets/live-v1/manifest.json",
    "evals/rubrics/live-v1/rubric.md",
    "pyproject.toml",
    "uv.lock",
)


class RevalidationBlocked(RuntimeError):
    """A fixed, content-free stop reason for this single operation."""


def git(repository: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=repository, capture_output=True, timeout=15
    )
    if result.returncode:
        raise RevalidationBlocked("source_provenance")
    return result.stdout.decode("utf-8", errors="strict").strip()


def project_source_paths(project: Path = PROJECT) -> list[str]:
    tracked = git(project, "ls-files").splitlines()
    return sorted(
        path
        for path in tracked
        if path.startswith(("src/", "scripts/", "tests/", "agent/", "evals/"))
        or path in {"pyproject.toml", "uv.lock", "harness.yaml"}
    )


def require_clean_sources(project: Path = PROJECT, lab: Path = LAB) -> None:
    own = project_source_paths(project)
    for repository, paths in ((project, own), (lab, list(ROOT_SOURCES))):
        git(repository, "diff", "--quiet", "HEAD", "--", *paths)
        result = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=all", "--", *paths],
            cwd=repository,
            capture_output=True,
            timeout=15,
        )
        if result.returncode or result.stdout:
            raise RevalidationBlocked("source_provenance")


def fingerprint(project: Path = PROJECT, lab: Path = LAB) -> str:
    own = project_source_paths(project)
    values = [
        ("p01/" + path, hashlib.sha256((project / path).read_bytes()).hexdigest())
        for path in own
    ]
    values.extend(
        (path, hashlib.sha256((lab / path).read_bytes()).hexdigest())
        for path in ROOT_SOURCES
    )
    return hashlib.sha256(
        json.dumps(values, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def manifest_file_hashes(project: Path = PROJECT, lab: Path = LAB) -> dict[str, str]:
    own = list((project / "src/supportops_agents").rglob("*.py"))
    own.extend(project / name for name in OPERATION_OWN_SOURCES)
    shared = [
        lab / "scripts/harness/live_free_account.py",
        lab / "scripts/harness/live_provider_transport.py",
        lab / "shared/policies/groq-free-campaign.json",
    ]
    return {
        path.relative_to(lab).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in own + shared
    }


def require_applied_root_migration(lab: Path = LAB) -> dict[str, Any]:
    result = subprocess.run(
        [
            sys.executable,
            str(lab / "scripts/harness/migrate_p01_p04_revalidation.py"),
            "--dry-run",
        ],
        cwd=lab,
        capture_output=True,
        text=True,
        timeout=45,
    )
    try:
        report = json.loads(result.stdout)
    except (ValueError, TypeError):
        raise RevalidationBlocked("root_migration_unverified") from None
    if result.returncode or report.get("status") != "ALREADY_APPLIED":
        raise RevalidationBlocked("root_migration_unverified")
    return report


def owner_allocation(project: Path = PROJECT) -> dict[str, Any]:
    try:
        owner = json.loads(
            (project / "evals/live-execution.json").read_text(encoding="utf-8")
        )
        allocation = owner["allocations"][CAMPAIGN]
    except (OSError, ValueError, KeyError, TypeError):
        raise RevalidationBlocked("owner_allocation_invalid") from None
    if (
        owner.get("project") != "p01"
        or owner.get("execution_enabled") is not True
        or owner.get("synthetic_only") is not True
        or owner.get("authorized_paid_spend_usd") != "0.00"
        or CAMPAIGN not in owner.get("approved_campaigns", [])
        or allocation
        != {
            "stage": "operation",
            "case_ids": [CASE],
            "trials_per_case": 1,
            "max_trials": 1,
        }
    ):
        raise RevalidationBlocked("owner_allocation_invalid")
    return owner


def freeze_manifest(project: Path = PROJECT, lab: Path = LAB) -> dict[str, Any]:
    require_applied_root_migration(lab)
    owner_allocation(project)
    require_clean_sources(project, lab)
    manifest_path = project / MANIFEST
    if manifest_path.exists() or manifest_path.is_symlink():
        raise RevalidationBlocked("manifest_already_frozen")
    policy = json.loads(
        (lab / "shared/policies/groq-free-campaign.json").read_text(encoding="utf-8")
    )
    if policy.get("projects", {}).get("p01", {}).get("requests") != 1000:
        raise RevalidationBlocked("root_policy_mismatch")
    candidate = git(project, "rev-parse", "HEAD")
    manifest = {
        "campaign_id": CAMPAIGN,
        "stage": "operation",
        "sampling_order": [CASE],
        "trials_per_case": 1,
        "candidate_commit": candidate,
        "authorization_id": AUTH_ID,
        "source_fingerprint": fingerprint(project, lab),
        "root_policy_sha256": hashlib.sha256(
            json.dumps(policy, sort_keys=True).encode("utf-8")
        ).hexdigest(),
        "max_provider_calls": 4,
        "max_input_tokens": 8192,
        "max_output_tokens": 1024,
        "estimated_cost_usd": "0.0009216",
        "aggregate_logical_ceiling": {
            "requests": 16,
            "input_tokens": 32768,
            "output_tokens": 4096,
            "estimated_cost_usd": "0.0036864",
        },
        "files_sha256": manifest_file_hashes(project, lab),
        "human_review": "PENDING",
        "promotion": "PENDING",
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    return manifest


def validate(
    project: Path = PROJECT,
    lab: Path = LAB,
    *,
    check_root_migration: bool = True,
) -> dict[str, Any]:
    if check_root_migration:
        require_applied_root_migration(lab)
    owner = owner_allocation(project)
    require_clean_sources(project, lab)
    try:
        manifest = json.loads(
            (project / MANIFEST).read_text(encoding="utf-8")
        )
    except (OSError, ValueError):
        raise RevalidationBlocked("manifest_missing") from None
    if (
        manifest.get("campaign_id") != CAMPAIGN
        or manifest.get("stage") != "operation"
        or manifest.get("sampling_order") != [CASE]
        or manifest.get("trials_per_case") != 1
        or manifest.get("authorization_id") != AUTH_ID
        or manifest.get("source_fingerprint") != fingerprint(project, lab)
        or manifest.get("files_sha256") != manifest_file_hashes(project, lab)
        or manifest.get("human_review") != "PENDING"
        or manifest.get("promotion") != "PENDING"
        or manifest.get("max_provider_calls") != 4
        or manifest.get("max_input_tokens") != 8192
        or manifest.get("max_output_tokens") != 1024
        or manifest.get("estimated_cost_usd") != "0.0009216"
        or manifest.get("aggregate_logical_ceiling")
        != {
            "requests": 16,
            "input_tokens": 32768,
            "output_tokens": 4096,
            "estimated_cost_usd": "0.0036864",
        }
    ):
        raise RevalidationBlocked("manifest_mismatch")
    candidate = manifest.get("candidate_commit")
    if not isinstance(candidate, str) or len(candidate) != 40:
        raise RevalidationBlocked("candidate_missing")
    git(project, "merge-base", "--is-ancestor", candidate, "HEAD")
    git(project, "diff", "--quiet", candidate, "HEAD", "--", *project_source_paths(project))
    policy = json.loads(
        (lab / "shared/policies/groq-free-campaign.json").read_text(encoding="utf-8")
    )
    if manifest.get("root_policy_sha256") != hashlib.sha256(
        json.dumps(policy, sort_keys=True).encode("utf-8")
    ).hexdigest():
        raise RevalidationBlocked("root_policy_mismatch")
    return manifest


class Bridge:
    def __init__(self, factory, provenance: str):
        self.factory = factory
        self.session = None
        self.provenance = provenance

    def request(self, envelope: dict[str, Any]) -> dict[str, Any]:
        try:
            if envelope.get("operation") != "complete":
                raise BoundaryError("protocol_failure")
            envelope = {key: value for key, value in envelope.items() if key != "operation"}
            if self.session is None:
                self.session = self.factory()
            self.session.preview(envelope)
            return self.session.complete(envelope)
        except BoundaryError:
            raise
        except Exception as error:
            categories = {
                "explicit_live_mode_required": "guard_denied",
                "authenticated_model_catalog_incomplete": "model_access",
                "provider_token_capacity": "quota",
                "provider_request_capacity": "quota",
                "reviewed_revalidation_authority_or_history_invalid": "guard_denied",
                "account_policy_or_registry_changed": "guard_denied",
                "uncertain_attempt_requires_reconciliation": "guard_denied",
            }
            raise BoundaryError(categories.get(str(error), "protocol_failure")) from None

    def close(self):
        pass


def run(
    path: Path,
    *,
    authority_check,
    session_factory,
    provenance: str = "fixture",
    project: Path = PROJECT,
) -> dict[str, Any]:
    authority_check()
    ledger = CampaignLedger(path, campaign_id=CAMPAIGN)
    if ledger.reserved_trials():
        raise CampaignBlocked("revalidation_already_reserved")
    ledger.reserve(
        case_id=CASE,
        trial=1,
        calls=WORKFLOW_RESERVE["calls"],
        input_tokens=WORKFLOW_RESERVE["input_tokens"],
        output_tokens=WORKFLOW_RESERVE["output_tokens"],
        estimated_cost_usd=WORKFLOW_RESERVE["estimated_cost_usd"],
        caps=CAPS,
    )
    client = AccountedCoreClient(
        Bridge(session_factory, provenance),
        WorkflowBinding(CAMPAIGN, CASE, 1),
        project=project,
    )
    try:
        result = CoreTriageRunner().run(
            Ticket(CASE, "Synthetic greeting revalidation", TEXT), llm=client
        )
        if not client.receipts or any(row["usage"] is None for row in client.receipts):
            raise CampaignBlocked("missing_accounted_receipt")
        input_tokens = sum(row["usage"]["input_tokens"] for row in client.receipts)
        output_tokens = sum(row["usage"]["output_tokens"] for row in client.receipts)
        actual_cost = (
            Decimal(input_tokens) * Decimal("0.075")
            + Decimal(output_tokens) * Decimal("0.30")
        ) / 1000000
        outcome = "ok" if result.stop_reason == "approved" else "incomplete"
        ledger.complete(
            case_id=CASE,
            trial=1,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            actual_cost_usd=actual_cost,
            outcome=outcome,
            error_class=None if outcome == "ok" else "semantic",
        )
        return {
            "status": "ok" if outcome == "ok" else "INCOMPLETE",
            "stop_reason": result.stop_reason,
            "calls": len(client.receipts),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "receipts": client.receipts,
            "historical_calls_retained": 12,
            "aggregate_logical_ceiling": CAPS["requests"],
            "provider_content_saved": False,
        }
    except (BoundaryError, CampaignBlocked) as error:
        ledger.complete(
            case_id=CASE,
            trial=1,
            input_tokens=None,
            output_tokens=None,
            actual_cost_usd=None,
            outcome="incomplete",
            error_class="unknown",
        )
        return {
            "status": "INCOMPLETE",
            "calls": len(client.receipts),
            "receipts": client.receipts,
            "diagnostic": (
                error.diagnostic
                if isinstance(error, BoundaryError)
                else {"reason": "accounting"}
            ),
            "historical_calls_retained": 12,
            "revalidation_reserve_retained": True,
            "provider_content_saved": False,
        }
    finally:
        client.close()


def write_once(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(value, indent=2, sort_keys=True) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
    except FileExistsError:
        raise RevalidationBlocked("invocation_already_started") from None


def live_main() -> int:
    if os.getenv("LLM_MODE", "fake") != "live":
        print(json.dumps({"status": "INCOMPLETE", "reason": "explicit_live_required"}))
        return 2
    try:
        write_once(PROJECT / START, {"campaign": CAMPAIGN, "case": CASE,
                                     "single_invocation": True, "state": "started"})
    except RevalidationBlocked:
        print(json.dumps({"status": "INCOMPLETE", "reason": "invocation_already_started"}))
        return 2
    try:
        validate()
        sys.path.insert(0, str(LAB / "scripts/harness"))
        from live_free_account import (
            SharedAccount,
            bounded_catalog_preflight,
            machine_lease,
        )
        from live_provider_transport import ProviderSession

        policy = json.loads(
            (LAB / "shared/policies/groq-free-campaign.json").read_text(encoding="utf-8")
        )
        account = SharedAccount(LAB, policy)
        with machine_lease(LAB / ".runtime/llm-live-readiness/campaign.lock"):
            # The migration dry-run takes the same campaign lock. It already passed
            # immediately before lease acquisition; the locked history and policy
            # checks below revalidate the authority without recursively taking it.
            validate(check_root_migration=False)
            account._reviewed_revalidation(
                account._history(), "p01", CAMPAIGN, CASE, 1, 1, False
            )
            frozen = json.loads((PROJECT / MANIFEST).read_text(encoding="utf-8"))
            write_once(
                PROJECT / INVOCATION,
                {
                    "campaign": CAMPAIGN,
                    "case": CASE,
                    "trial": 1,
                    "candidate_commit": frozen["candidate_commit"],
                    "source_fingerprint": frozen["source_fingerprint"],
                    "root_policy_sha256": frozen["root_policy_sha256"],
                    "single_invocation": True,
                    "generation_calls_max": 4,
                    "paid_authorized_usd": "0.00",
                },
            )
            preflight = bounded_catalog_preflight()
            if (
                preflight.get("status") != "PASS"
                or preflight.get("model") != "openai/gpt-oss-20b"
                or preflight.get("generation_calls") != 0
            ):
                result = {
                    "status": "INCOMPLETE",
                    "reason": "model_access_preflight",
                    "generation_calls": 0,
                    "workflow_reservation_created": False,
                    "invocation_consumed": True,
                }
                write_once(PROJECT / RESULT, result)
                print(json.dumps(result, sort_keys=True))
                return 2
            result = run(
                PROJECT / "artifacts/evals/live/ledger.sqlite",
                authority_check=lambda: account._reviewed_revalidation(
                    account._history(), "p01", CAMPAIGN, CASE, 1, 1, False
                ),
                session_factory=lambda: ProviderSession(LAB, "p01", policy),
                provenance="live",
            )
        write_once(PROJECT / RESULT, result)
        print(json.dumps(result, sort_keys=True))
        return 0 if result["status"] == "ok" else 2
    except Exception:
        invocation = PROJECT / START
        result_path = PROJECT / RESULT
        if invocation.exists() and not result_path.exists():
            try:
                write_once(
                    result_path,
                    {
                        "status": "INCOMPLETE",
                        "reason": "revalidation_blocked_or_uncertain",
                        "invocation_consumed": True,
                        "provider_content_saved": False,
                    },
                )
            except RevalidationBlocked:
                pass
        print(json.dumps({"status": "INCOMPLETE", "reason": "revalidation_blocked_or_uncertain"}))
        return 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--freeze-manifest", action="store_true")
    group.add_argument("--validate", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.freeze_manifest:
            manifest = freeze_manifest()
            print(json.dumps({"status": "FROZEN", **manifest}, sort_keys=True))
            return 0
        if args.validate:
            manifest = validate()
            print(json.dumps({"status": "PASS", "manifest": manifest}, sort_keys=True))
            return 0
    except Exception:
        print(json.dumps({"status": "INCOMPLETE", "reason": "candidate_binding_invalid"}))
        return 2
    return live_main()


if __name__ == "__main__":
    raise SystemExit(main())
