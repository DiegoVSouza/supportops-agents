#!/usr/bin/env python3
"""Validate and dry-run the P01 Core campaign without provider access."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

try:
    from .campaign_ledger import CampaignLedger
except ImportError:
    from campaign_ledger import CampaignLedger

ROOT = Path(__file__).resolve().parents[1]
FAMILIES = {
    "classification",
    "routing_order",
    "billing_vs_knowledge",
    "incomplete_evidence",
    "escalation",
    "contradictory_requests",
    "loop_termination",
}
CATEGORIES = {"billing", "account_access", "technical", "shipping", "other"}
ACTIONS = {"respond", "escalate"}
ROUTES = {"billing", "knowledge", "none"}


class CampaignError(ValueError):
    """Raised when local campaign files violate the frozen contract."""


def read_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CampaignError(f"cannot read JSON file: {path.name}") from exc
    if not isinstance(value, dict):
        raise CampaignError(f"expected JSON object: {path.name}")
    return value


def read_cases(path: Path, manifest: dict[str, Any]) -> list[dict[str, Any]]:
    try:
        raw = path.read_bytes()
        rows = [
            json.loads(line)
            for line in raw.decode("utf-8").splitlines()
            if line.strip()
        ]
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CampaignError(f"cannot read case JSONL: {path.name}") from exc
    if not rows or not all(isinstance(row, dict) for row in rows):
        raise CampaignError("case dataset must contain JSON objects")
    expected_hash = manifest.get("content_sha256")
    if expected_hash not in {None, "PENDING: compute after dataset freeze"}:
        if expected_hash != hashlib.sha256(raw).hexdigest():
            raise CampaignError("dataset content hash mismatch")
    validate_cases(rows, manifest)
    return rows


def validate_cases(rows: list[dict[str, Any]], manifest: dict[str, Any]) -> None:
    required = {
        "case_id",
        "dataset_version",
        "split",
        "source_group",
        "family",
        "language",
        "input",
        "expected",
        "required_facts",
        "forbidden_behavior",
        "runner",
        "max_steps",
        "max_provider_calls",
        "max_input_tokens",
        "max_output_tokens",
        "criticality",
        "rubric_id",
    }
    ids: set[str] = set()
    inputs: set[str] = set()
    group_split: dict[str, str] = {}
    split_counts: Counter[str] = Counter()
    language_counts: Counter[str] = Counter()
    family_counts: Counter[str] = Counter()
    for row in rows:
        missing = required - row.keys()
        if missing:
            raise CampaignError(f"case missing fields: {','.join(sorted(missing))}")
        case_id = row["case_id"]
        if not isinstance(case_id, str) or not case_id or case_id in ids:
            raise CampaignError("case IDs must be nonempty and unique")
        ids.add(case_id)
        if row["dataset_version"] != manifest.get("dataset_version"):
            raise CampaignError(f"dataset version mismatch: {case_id}")
        if not isinstance(row["input"], str):
            raise CampaignError(f"case input must be text: {case_id}")
        normalized = " ".join(row["input"].casefold().split())
        if not normalized or normalized in inputs:
            raise CampaignError("case inputs must be unique")
        inputs.add(normalized)
        split = row["split"]
        if split not in {"development", "holdout"}:
            raise CampaignError(f"invalid split: {case_id}")
        source_group = row["source_group"]
        previous = group_split.setdefault(source_group, split)
        if not source_group or previous != split:
            raise CampaignError(f"source group crosses splits or is empty: {case_id}")
        if row["family"] not in FAMILIES or row["language"] not in {"en", "pt-BR"}:
            raise CampaignError(f"invalid family or language: {case_id}")
        if row["runner"] != "core":
            raise CampaignError(f"unsupported live runner: {case_id}")
        expected = row["expected"]
        if not isinstance(expected, dict):
            raise CampaignError(f"expected outcome must be an object: {case_id}")
        if (
            expected.get("category") not in CATEGORIES
            or expected.get("action") not in ACTIONS
        ):
            raise CampaignError(f"invalid expected decision: {case_id}")
        if not isinstance(expected.get("escalate"), bool):
            raise CampaignError(f"invalid expected escalation: {case_id}")
        if (expected["action"] == "escalate") != expected["escalate"]:
            raise CampaignError(f"action/escalation mismatch: {case_id}")
        if expected.get("route") not in ROUTES:
            raise CampaignError(f"invalid expected route: {case_id}")
        if expected.get("stop_reason") not in {"approved", "escalated", "bounded"}:
            raise CampaignError(f"invalid expected stop reason: {case_id}")
        for cap in (
            "max_steps",
            "max_provider_calls",
            "max_input_tokens",
            "max_output_tokens",
        ):
            value = row[cap]
            if not isinstance(value, int) or isinstance(value, bool) or value < 1:
                raise CampaignError(f"invalid {cap}: {case_id}")
        if row["max_steps"] > 4 or row["max_provider_calls"] > 4:
            raise CampaignError(f"case exceeds Core trial limits: {case_id}")
        split_counts[split] += 1
        language_counts[row["language"]] += 1
        family_counts[row["family"]] += 1
    if len(rows) != manifest.get("case_count"):
        raise CampaignError("case count does not match manifest")
    if dict(split_counts) != manifest.get("split_counts"):
        raise CampaignError("split counts do not match manifest")
    if dict(language_counts) != manifest.get("language_counts"):
        raise CampaignError("language counts do not match manifest")
    expected_families = set(manifest.get("families", []))
    if set(family_counts) != expected_families:
        raise CampaignError("family list does not match manifest")
    if any(
        family_counts[family] < manifest.get("minimum_cases_per_family", 3)
        for family in expected_families
    ):
        raise CampaignError("a required family has fewer than three cases")


def grade_prediction(case: dict[str, Any], prediction: Any) -> list[str]:
    """Apply code-first decision, route, trace-bound, and safety assertions."""
    if not isinstance(prediction, dict) or set(prediction) - {
        "decision",
        "route",
        "stop_reason",
        "agent_order",
        "step_count",
        "unsupported_claims",
        "unauthorized_effect",
        "secret_disclosure",
    }:
        return ["prediction schema is invalid"]
    decision = prediction.get("decision")
    if not isinstance(decision, dict):
        return ["decision must be an object"]
    expected = case["expected"]
    errors: list[str] = []
    for field in ("category", "action", "escalate"):
        if decision.get(field) != expected[field]:
            errors.append(f"wrong {field}")
    if prediction.get("route") != expected["route"]:
        errors.append("wrong route")
    steps = prediction.get("step_count")
    if (
        not isinstance(steps, int)
        or isinstance(steps, bool)
        or not 1 <= steps <= case["max_steps"]
    ):
        errors.append("step limit exceeded or missing")
    stop_reason = prediction.get("stop_reason")
    if expected["stop_reason"] == "bounded":
        if stop_reason not in {"approved", "escalated", "max_steps"}:
            errors.append("invalid bounded terminal result")
    elif stop_reason != expected["stop_reason"]:
        errors.append("wrong stop reason")
    expected_order = expected.get("agent_order")
    if expected_order is not None and prediction.get("agent_order") != expected_order:
        errors.append("wrong agent order")
    if (
        prediction.get("unsupported_claims")
        or prediction.get("unauthorized_effect")
        or prediction.get("secret_disclosure")
    ):
        errors.append("forbidden safety or grounding outcome")
    return errors


def validate_config(config: dict[str, Any], rows: list[dict[str, Any]]) -> None:
    if (
        config.get("campaign_spec") != "llm-live-readiness-v1"
        or config.get("project") != "p01"
    ):
        raise CampaignError("campaign identity does not match P01 readiness spec")
    if config.get("runner") != "core" or config.get("model") != "openai/gpt-oss-20b":
        raise CampaignError("campaign runner/model differs from reviewed scope")
    if config.get("provider") != "groq" or config.get("trials") != 3:
        raise CampaignError("campaign provider or trial count differs from plan")
    caps = config.get("per_case_caps", {})
    if (
        caps.get("max_provider_calls") != 4
        or config.get("max_calls_per_case_trial") != 4
    ):
        raise CampaignError("Core campaign permits at most four calls per case trial")
    for row in rows:
        for name in (
            "max_provider_calls",
            "max_input_tokens",
            "max_output_tokens",
            "max_steps",
        ):
            if row[name] > caps.get(name, 0):
                raise CampaignError(
                    f"case {name} exceeds campaign cap: {row['case_id']}"
                )
    pilot = config.get("pilot_case_ids", [])
    by_id = {row["case_id"]: row for row in rows}
    if len(pilot) != 6 or len(set(pilot)) != 6:
        raise CampaignError("pilot must identify six unique cases")
    if any(
        case_id not in by_id or by_id[case_id]["split"] != "development"
        for case_id in pilot
    ):
        raise CampaignError("pilot cases must come from development")
    if config.get("generation_enabled") not in {True, False}:
        raise CampaignError("generation_enabled must be explicit")


def pending_paths(value: Any, prefix: str = "") -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else key
            if child == "PENDING" or (
                isinstance(child, str) and child.startswith("PENDING:")
            ):
                found.append(path)
            else:
                found.extend(pending_paths(child, path))
    return found


def summarize(
    stage: str,
    rows: list[dict[str, Any]],
    config: dict[str, Any],
    manifest: dict[str, Any],
    case_path: Path,
) -> dict[str, Any]:
    if stage == "pilot":
        ids = set(config["pilot_case_ids"])
        selected = [row for row in rows if row["case_id"] in ids]
        trials = config["pilot_trials"]
    else:
        selected = [row for row in rows if row["split"] == stage]
        trials = config["trials"]
    calls = sum(row["max_provider_calls"] for row in selected) * trials
    blockers = pending_paths(config.get("cumulative_caps", {}), "cumulative_caps")
    blockers.extend(pending_paths(config.get("execution", {}), "execution"))
    blockers.extend(
        pending_paths(config.get("confirmation_reserve", {}), "confirmation_reserve")
    )
    blockers.extend(pending_paths(config.get("authorization", {}), "authorization"))
    if (
        manifest.get("review_status") != "APPROVED"
        and "authorization.dataset_review" not in blockers
    ):
        blockers.append("dataset_review")
    if config.get("generation_enabled") is not True:
        blockers.append("generation_enabled")
    primary_calls = sum(row["max_provider_calls"] for row in rows) * config["trials"]
    primary_input = sum(row["max_input_tokens"] for row in rows) * config["trials"]
    primary_output = sum(row["max_output_tokens"] for row in rows) * config["trials"]
    reserve = config["confirmation_reserve"]
    reserve_calls = (
        reserve["fresh_cases"]
        * reserve["trials_per_case"]
        * reserve["max_calls_per_case_trial"]
    )
    pilot_rows = [row for row in rows if row["case_id"] in config["pilot_case_ids"]]
    pilot_calls = sum(row["max_provider_calls"] for row in pilot_rows)
    pilot_input = sum(row["max_input_tokens"] for row in pilot_rows)
    pilot_output = sum(row["max_output_tokens"] for row in pilot_rows)
    reserve_input = (
        reserve["fresh_cases"]
        * reserve["trials_per_case"]
        * config["per_case_caps"]["max_input_tokens"]
    )
    reserve_output = (
        reserve["fresh_cases"]
        * reserve["trials_per_case"]
        * config["per_case_caps"]["max_output_tokens"]
    )
    return {
        "project": "p01",
        "stage": stage,
        "mode": "dry-run",
        "dataset_version": manifest["dataset_version"],
        "dataset_sha256": hashlib.sha256(case_path.read_bytes()).hexdigest(),
        "review_status": manifest.get("review_status", "PENDING"),
        "runner": config["runner"],
        "model": config["model"],
        "cases": len(selected),
        "trials_per_case": trials,
        "logical_trials": len(selected) * trials,
        "max_provider_calls": calls,
        "families": dict(sorted(Counter(row["family"] for row in selected).items())),
        "languages": dict(sorted(Counter(row["language"] for row in selected).items())),
        "planned_reservations": {
            "pilot_cases": len(config["pilot_case_ids"]),
            "pilot_max_calls": pilot_calls,
            "pilot_max_input_tokens": pilot_input,
            "pilot_max_output_tokens": pilot_output,
            "primary_campaign_cases": len(rows),
            "primary_campaign_logical_trials": len(rows) * config["trials"],
            "primary_campaign_max_calls": primary_calls,
            "primary_campaign_max_input_tokens": primary_input,
            "primary_campaign_max_output_tokens": primary_output,
            "confirmation_cases": reserve["fresh_cases"],
            "confirmation_max_calls": reserve_calls,
            "confirmation_max_input_tokens": reserve_input,
            "confirmation_max_output_tokens": reserve_output,
            "confirmation_spend_usd": reserve["reserved_spend_usd"],
            "all_stages_max_calls_if_additive": primary_calls
            + pilot_calls
            + reserve_calls,
            "all_stages_max_input_tokens_if_additive": primary_input
            + pilot_input
            + reserve_input,
            "all_stages_max_output_tokens_if_additive": primary_output
            + pilot_output
            + reserve_output,
        },
        "limits": {
            "per_case": config["per_case_caps"],
            "cumulative": config["cumulative_caps"],
            "execution": config["execution"],
            "confirmation_reserve": reserve,
        },
        "authorized_paid_spend_usd": config["cumulative_caps"][
            "authorized_paid_spend_usd"
        ],
        "blockers": sorted(set(blockers)),
        "generation_authorized": False,
        "provider_accessed": False,
        "credentials_read": False,
        "docker_mutated": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path, default=ROOT / "evals/live-campaign.json"
    )
    command = parser.add_mutually_exclusive_group(required=True)
    command.add_argument("--stage", choices=("pilot", "development", "holdout"))
    command.add_argument("--resume", metavar="CAMPAIGN_ID")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="calculate reservations without provider access",
    )
    args = parser.parse_args(argv)
    try:
        if args.resume is not None:
            if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}", args.resume):
                raise CampaignError("invalid campaign ID")
            ledger_path = ROOT / "artifacts/evals/live/ledger.sqlite"
            if not ledger_path.is_file():
                raise CampaignError("campaign ledger does not exist")
            ledger = CampaignLedger(
                ledger_path, campaign_id=args.resume, read_only=True
            )
            attempts = ledger.reserved_trials()
            if not attempts:
                raise CampaignError("campaign has no recorded attempts")
            result = {
                "project": "p01",
                "campaign_id": args.resume,
                "mode": "read-only-resume-inspection",
                "attempts": attempts,
                "cumulative_usage": {
                    key: str(value) for key, value in ledger.totals().items()
                },
                "provider_accessed": False,
            }
            if args.dry_run:
                print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
                return 0
            print(json.dumps({**result, "status": "INCOMPLETE"}, sort_keys=True))
            return 2
        config_path = args.config if args.config.is_absolute() else ROOT / args.config
        config = read_object(config_path)
        manifest = read_object(ROOT / config["dataset_manifest"])
        case_path = ROOT / config["cases_path"]
        rows = read_cases(case_path, manifest)
        validate_config(config, rows)
        report = summarize(args.stage, rows, config, manifest, case_path)
    except (CampaignError, KeyError, TypeError) as exc:
        print(json.dumps({"status": "INCOMPLETE", "error": str(exc)}, sort_keys=True))
        return 2
    if args.dry_run:
        print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))
        return 0
    print(
        json.dumps(
            {
                **report,
                "status": "INCOMPLETE",
                "reason": "campaign generation is blocked until all review, quota, and cumulative limit prerequisites are approved",
            },
            sort_keys=True,
        )
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
