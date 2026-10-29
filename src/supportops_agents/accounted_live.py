"""Accounted single-attempt boundary for the real Core worker loop.

The owning execution manifest stays disabled until durable campaign dispatch,
allocation and candidate provenance are completed in their owning phase.
"""

from __future__ import annotations

import json
import hashlib
import math
import os
import queue
import re
import subprocess
import sys
import sqlite3
import threading
from contextlib import closing, suppress
from decimal import Decimal
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

PROJECT = Path(__file__).resolve().parents[2]
MODEL = "openai/gpt-oss-20b"
WORKERS = ("classifier", "kb_researcher", "billing_agent", "responder")
CONTRACTS = {
    "classifier": {
        "category": "billing|account_access|technical|shipping|other",
        "summary": "nonempty text",
        "escalate": "reason or empty string",
    },
    "kb_researcher": {"context": "supported knowledge evidence or unavailable"},
    "billing_agent": {
        "context": "supported billing evidence or unavailable",
        "escalate": "reason or empty string",
    },
    "responder": {"response": "nonempty text", "approved": "boolean"},
}
REASONS = {
    "account_lease_busy",
    "account_policy_or_registry_changed",
    "registered_project_ledger_missing_or_replaced",
    "usage_exists_without_registry_reference",
    "cumulative_account_or_project_cap",
    "provider_model_mismatch_requires_review",
    "accounting_overrun_requires_reconciliation",
    "provider_cooldown_checkpoint",
    "provider_request_capacity_checkpoint",
    "provider_token_capacity_checkpoint",
    "uncertain_attempt_requires_reconciliation",
    "attempt_already_reserved_or_completed",
    "per_call_token_cap",
    "root_credentials_unavailable",
    "numbered_credentials_missing",
    "owning_project_execution_not_authorized",
    "owning_project_execution_manifest_missing",
    "full_request_input_bound_exceeds_cap",
    "original_output_cap_exceeded",
    "model_or_output_schema",
    "provider_protocol_failure",
    "transport",
    "quota",
    "rate_limit",
    "request_schema",
    "output_schema",
    "output_truncated",
    "tool_selection",
    "credential",
    "model_access",
    "accounting",
    "accounting_overrun",
    "free_token_minute_checkpoint",
    "free_request_minute_checkpoint",
    "free_request_day_checkpoint",
    "free_token_day_checkpoint",
    "project_request_cap_exceeded",
    "account_request_cap_exceeded",
    "guard_denied",
    "protocol_failure",
    "provider_timeout_uncertain",
    "call_limit",
    "worker_order",
    "worker_contract",
    "workflow_stopped",
    "configuration",
    "OTHER",
}
ERROR_CODES = {
    "json_validate_failed",
    "tool_use_failed",
    "context_length_exceeded",
    "invalid_request_error",
    "invalid_api_key",
    "authentication_error",
    "model_not_found",
    "model_permission_blocked",
    "rate_limit_exceeded",
    "insufficient_quota",
    "billing_hard_limit_reached",
    "blocked_api_access",
    "OTHER",
}


class BoundaryError(RuntimeError):
    """Only typed, allowlisted diagnostics cross this boundary."""

    def __init__(self, reason: str, result: Mapping[str, Any] | None = None):
        self.diagnostic = diagnostic({**(result or {}), "reason": reason})
        super().__init__(self.diagnostic["reason"])


def diagnostic(result: Mapping[str, Any]) -> dict[str, Any]:
    reason = result.get("reason")
    status = result.get("http_status")
    code = result.get("provider_error_code")
    attempt = result.get("attempt_id")
    return {
        "reason": reason if isinstance(reason, str) and reason in REASONS else "OTHER",
        "http_status": status if type(status) is int and 100 <= status <= 599 else None,
        "provider_error_code": code
        if isinstance(code, str) and code in ERROR_CODES
        else "OTHER"
        if code is not None
        else None,
        "attempt_id": attempt
        if isinstance(attempt, str) and re.fullmatch(r"[0-9a-f]{32}", attempt)
        else None,
    }


@dataclass(frozen=True)
class WorkflowBinding:
    campaign_id: str
    case_id: str
    trial: int

    def __post_init__(self):
        if any(
            not isinstance(value, str)
            or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}", value)
            for value in (self.campaign_id, self.case_id)
        ):
            raise BoundaryError("guard_denied")
        if type(self.trial) is not int or not 1 <= self.trial <= 3:
            raise BoundaryError("guard_denied")


def build_payload(
    agent: str, state: Mapping[str, Any], *, project: Path = PROJECT
) -> dict[str, Any]:
    if agent not in CONTRACTS:
        raise BoundaryError("worker_contract")
    fields = {"ticket", "category", "classification", "kb_context", "billing_context", "response"}
    if not isinstance(state, Mapping) or set(state) - fields:
        raise BoundaryError("worker_contract")
    ticket = state.get("ticket", {})
    if not isinstance(ticket, Mapping) or set(ticket) - {
        "id",
        "subject",
        "description",
        "customer_id",
    }:
        raise BoundaryError("worker_contract")
    if any(not isinstance(value, str) for value in ticket.values()) or any(
        not isinstance(value, str) for name, value in state.items() if name != "ticket"
    ):
        raise BoundaryError("worker_contract")
    try:
        prompt = (project / "agent/prompts/live-core.md").read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError):
        raise BoundaryError("configuration") from None
    content = json.dumps(
        {"worker": agent, "contract": CONTRACTS[agent], "input": dict(state)},
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    )
    payload = {
        "model": MODEL,
        "messages": [{"role": "system", "content": prompt}, {"role": "user", "content": content}],
        "max_completion_tokens": 256,
        "temperature": 0,
        "reasoning_effort": "low",
        "include_reasoning": False,
    }
    input_bound(payload)
    return payload


def input_bound(payload: dict[str, Any]) -> int:
    if (
        not isinstance(payload, dict)
        or set(payload)
        != {
            "model",
            "messages",
            "max_completion_tokens",
            "temperature",
            "reasoning_effort",
            "include_reasoning",
        }
        or payload.get("model") != MODEL
        or payload.get("include_reasoning") is not False
        or type(payload.get("temperature")) not in (int, float)
        or payload.get("temperature") != 0
        or payload.get("reasoning_effort") != "low"
    ):
        raise BoundaryError("request_schema")
    messages = payload["messages"]
    if (
        not isinstance(messages, list)
        or len(messages) != 2
        or any(
            not isinstance(message, dict)
            or set(message) != {"role", "content"}
            or message.get("role") != role
            or not isinstance(message.get("content"), str)
            for message, role in zip(messages, ("system", "user"))
        )
    ):
        raise BoundaryError("request_schema")
    normalized = {
        **payload,
        "model": MODEL,
        "stream": False,
        "include_reasoning": False,
        "reasoning_effort": payload.get("reasoning_effort", "low"),
    }
    try:
        encoded = json.dumps(
            normalized, ensure_ascii=False, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")
    except (ValueError, TypeError, UnicodeError):
        raise BoundaryError("request_schema") from None
    bound = (
        len(encoded)
        + 256
        + 64 * len(normalized["messages"])
        + 128 * len(normalized.get("tools", []))
    )
    if (
        bound > 2048
        or type(payload.get("max_completion_tokens")) is not int
        or not 1 <= payload["max_completion_tokens"] <= 256
    ):
        raise BoundaryError("request_schema")
    return bound


def validate_output(agent: str, output: Any, *, fixture_plan: bool = False) -> dict[str, Any]:
    fields = set(CONTRACTS[agent])
    if fixture_plan and agent == "classifier" and isinstance(output, dict) and "read_plan" in output:
        fields.add("read_plan")
    if not isinstance(output, dict) or set(output) != fields:
        raise BoundaryError("worker_contract")
    for field, value in output.items():
        if field == "read_plan":
            if not isinstance(value, dict) or set(value) != {"tools"}:
                raise BoundaryError("worker_contract")
        elif field == "approved":
            if type(value) is not bool:
                raise BoundaryError("worker_contract")
        elif not isinstance(value, str) or (field != "escalate" and not value.strip()):
            raise BoundaryError("worker_contract")
    if agent == "classifier" and output["category"] not in {
        "billing",
        "account_access",
        "technical",
        "shipping",
        "other",
    }:
        raise BoundaryError("worker_contract")
    return output


class AccountedCoreClient:
    """Actual Core LLMClient with stable call indexes and no replay or retries."""

    def __init__(self, transport, binding: WorkflowBinding, *, project: Path = PROJECT):
        if getattr(transport, "provenance", None) not in {"live", "fixture"}:
            raise BoundaryError("guard_denied")
        self.transport, self.binding, self.project = transport, binding, project
        self.started = 0
        self.stopped = False
        self.receipts: list[dict[str, Any]] = []
        self.last_failure: dict[str, Any] | None = None

    def close(self):
        self.stopped = True
        close = getattr(self.transport, "close", None)
        if callable(close):
            with suppress(Exception):
                close()

    def complete(self, agent: str, state: Mapping[str, Any]) -> Mapping[str, Any]:
        try:
            if self.stopped:
                raise BoundaryError("workflow_stopped")
            if self.started >= 4:
                raise BoundaryError("call_limit")
            if agent != WORKERS[self.started]:
                raise BoundaryError("worker_order")
            payload = build_payload(agent, state, project=self.project)
            self.started += 1  # Never roll back a possibly dispatched call index.
            result = self.transport.request(
                {
                    "operation": "complete",
                    "campaign_id": self.binding.campaign_id,
                    "case_id": self.binding.case_id,
                    "trial": self.binding.trial,
                    "call_index": self.started,
                    "payload": payload,
                    "timeout_seconds": 20,
                }
            )
            if not isinstance(result, dict):
                raise BoundaryError("protocol_failure")
            safe = diagnostic(result)
            if safe["attempt_id"]:
                observed = result.get("usage")
                usage_copy = (
                    {name: observed[name] for name in ("input_tokens", "output_tokens")}
                    if isinstance(observed, dict)
                    and all(
                        type(observed.get(name)) is int and observed[name] >= 0
                        for name in ("input_tokens", "output_tokens")
                    )
                    else None
                )
                latency = result.get("latency_ms")
                self.receipts.append(
                    {
                        **safe,
                        "call_index": self.started,
                        "worker": agent,
                        "provenance": self.transport.provenance,
                        "usage": usage_copy,
                        "latency_ms": latency
                        if type(latency) in (int, float)
                        and math.isfinite(latency)
                        and 0 <= latency <= 60000
                        else None,
                    }
                )
            if result.get("status") != "ok":
                raise BoundaryError(safe["reason"], result)
            usage = result.get("usage")
            if not isinstance(usage, dict) or any(
                type(usage.get(name)) is not int or usage[name] < 0
                for name in ("input_tokens", "output_tokens")
            ):
                raise BoundaryError("accounting", result)
            if (
                not safe["attempt_id"]
                or result.get("model") != MODEL
                or usage["input_tokens"] > input_bound(payload)
                or usage["output_tokens"] > 256
            ):
                raise BoundaryError("accounting", result)
            if result.get("tool_calls"):
                raise BoundaryError("tool_selection", result)
            if result.get("finish_reason") != "stop":
                raise BoundaryError("output_truncated", result)
            content = result.get("content")
            if not isinstance(content, str) or len(content.encode("utf-8")) > 8192:
                raise BoundaryError("output_schema", result)
            try:
                output = validate_output(agent, json.loads(content), fixture_plan=self.transport.provenance == "fixture")
            except (ValueError, TypeError):
                raise BoundaryError("output_schema", result) from None
            if output.get("escalate") or agent == "responder":
                self.close()
            return output
        except BoundaryError as error:
            self.close()
            self.last_failure = error.diagnostic
            raise
        except (KeyboardInterrupt, SystemExit):
            self.close()
            self.last_failure = diagnostic({"reason": "provider_timeout_uncertain"})
            raise
        except Exception:
            self.close()
            error = BoundaryError("provider_timeout_uncertain")
            self.last_failure = error.diagnostic
            raise error from None


class SubprocessGuard:
    """Documented root transport v1, fixed to P01; never handles provider keys."""

    provenance = "live"

    def __init__(self, binding: WorkflowBinding, *, project: Path = PROJECT):
        self.project, self.binding = project, binding
        self.process = None
        self.stopped = False
        self.next_index = 1
        try:
            owner = json.loads((project / "evals/live-execution.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            raise BoundaryError("guard_denied") from None
        if (
            not isinstance(owner, dict)
            or owner.get("project") != "p01"
            or owner.get("execution_enabled") is not True
            or owner.get("synthetic_only") is not True
            or owner.get("protocol_version") != 1
            or owner.get("account_policy") != "groq-free-live-readiness-v1"
            or owner.get("provider_timeout_seconds") != 20
            or type(owner.get("provider_timeout_seconds")) not in (int, float)
            or owner.get("authorized_paid_spend_usd") != "0.00"
            or not isinstance(owner.get("approved_campaigns"), list)
            or binding.campaign_id not in owner.get("approved_campaigns", [])
        ):
            raise BoundaryError("guard_denied")
        self._verify_dispatch_binding(owner)

    def _verify_dispatch_binding(self, owner):
        """Read-only prerequisites; missing/future campaign work cannot authorize a call."""
        root = self.project.parents[1]
        try:
            allocation = owner["allocations"][self.binding.campaign_id]
            if (
                allocation["stage"] not in {"pilot", "development", "holdout"}
                or self.binding.case_id not in allocation["case_ids"]
                or self.binding.trial > allocation["trials_per_case"]
            ):
                raise ValueError
            manifest_path = (
                self.project / "artifacts/evals/live" / self.binding.campaign_id / "manifest.json"
            )
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            candidate = manifest["candidate_commit"]
            if (
                not isinstance(candidate, str)
                or not re.fullmatch(r"[0-9a-f]{40}", candidate)
                or manifest["campaign_id"] != self.binding.campaign_id
                or manifest["stage"] != allocation["stage"]
                or manifest["sampling_order"] != allocation["case_ids"]
                or manifest["trials_per_case"] != allocation["trials_per_case"]
            ):
                raise ValueError
            own = list((self.project / "src/supportops_agents").rglob("*.py"))
            own += [
                self.project / name
                for name in (
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
            ]
            shared = [
                root / name
                for name in (
                    "scripts/harness/live_free_account.py",
                    "scripts/harness/live_provider_transport.py",
                    "shared/policies/groq-free-campaign.json",
                )
            ]
            expected = {path.relative_to(root).as_posix(): path for path in own + shared}
            if set(manifest["files_sha256"]) != set(expected):
                raise ValueError
            for name, path in expected.items():
                if (
                    path.is_symlink()
                    or not path.resolve().is_relative_to(root.resolve())
                    or hashlib.sha256(path.read_bytes()).hexdigest()
                    != manifest["files_sha256"][name]
                ):
                    raise ValueError
            for repository, paths in ((self.project, own), (root, shared)):
                relative = [path.relative_to(repository).as_posix() for path in paths]
                for command in (
                    ["git", "ls-files", "--error-unmatch", "--", *relative],
                    ["git", "diff", "--quiet", "HEAD", "--", *relative],
                ):
                    if subprocess.run(
                        command, cwd=repository, capture_output=True, timeout=10
                    ).returncode:
                        raise ValueError
            relative = [path.relative_to(self.project).as_posix() for path in own]
            if subprocess.run(
                ["git", "diff", "--quiet", candidate, "HEAD", "--", *relative],
                cwd=self.project,
                capture_output=True,
                timeout=10,
            ).returncode:
                raise ValueError
            ledger_path = self.project / "artifacts/evals/live/ledger.sqlite"
            with closing(
                sqlite3.connect(ledger_path.resolve().as_uri() + "?mode=ro", uri=True)
            ) as db:
                db.row_factory = sqlite3.Row
                latest = {}
                for row in db.execute("SELECT * FROM events ORDER BY sequence"):
                    latest[(row["campaign_id"], row["case_id"], row["trial"])] = row
            reservation = latest[
                (self.binding.campaign_id, self.binding.case_id, self.binding.trial)
            ]
            if (
                reservation["event"] != "reserved"
                or (
                    reservation["reserved_calls"],
                    reservation["reserved_input_tokens"],
                    reservation["reserved_output_tokens"],
                )
                != (4, 8192, 1024)
                or Decimal(reservation["reserved_cost_usd"]) < Decimal("0.0009216")
            ):
                raise ValueError
            if sum(row["reserved_calls"] for row in latest.values()) > 744:
                raise ValueError
            if (
                sum(
                    row["actual_input_tokens"]
                    if row["actual_input_tokens"] is not None
                    else row["reserved_input_tokens"]
                    for row in latest.values()
                )
                > 1523712
                or sum(
                    row["actual_output_tokens"]
                    if row["actual_output_tokens"] is not None
                    else row["reserved_output_tokens"]
                    for row in latest.values()
                )
                > 190464
                or sum(
                    Decimal(
                        row["actual_cost_usd"]
                        if row["actual_cost_usd"] is not None
                        else row["reserved_cost_usd"]
                    )
                    for row in latest.values()
                )
                > Decimal("0.1714176")
            ):
                raise ValueError
            if (
                sum(row["campaign_id"] == self.binding.campaign_id for row in latest.values())
                > allocation["max_trials"]
            ):
                raise ValueError
            usage_path = self.project / "artifacts/evals/live/provider-usage.sqlite"
            if usage_path.exists():
                with closing(
                    sqlite3.connect(usage_path.resolve().as_uri() + "?mode=ro", uri=True)
                ) as db:
                    if db.execute(
                        "SELECT 1 FROM usage_events WHERE campaign=? AND case_id=? AND trial=? LIMIT 1",
                        (self.binding.campaign_id, self.binding.case_id, self.binding.trial),
                    ).fetchone():
                        raise ValueError
        except Exception:
            raise BoundaryError("guard_denied") from None

    def _read(self) -> dict[str, Any]:
        replies = queue.Queue(maxsize=1)

        def read_one():
            try:
                replies.put(self.process.stdout.readline(131073))
            except Exception:
                replies.put(b"")

        threading.Thread(target=read_one, daemon=True).start()
        try:
            line = replies.get(timeout=35)
        except queue.Empty:
            self.close()
            raise BoundaryError("provider_timeout_uncertain") from None
        if not line.endswith(b"\n") or len(line) > 131072:
            self.close()
            raise BoundaryError("protocol_failure")
        try:
            result = json.loads(line.decode("utf-8", errors="strict"))
        except (ValueError, UnicodeError):
            self.close()
            raise BoundaryError("protocol_failure") from None
        if not isinstance(result, dict):
            self.close()
            raise BoundaryError("protocol_failure")
        return result

    def _start(self):
        if self.stopped:
            raise BoundaryError("workflow_stopped")
        root = self.project.parents[1]
        allowed_env = (
            "PATH",
            "SystemRoot",
            "WINDIR",
            "TEMP",
            "TMP",
            "USERPROFILE",
            "APPDATA",
            "LOCALAPPDATA",
        )
        env = {name: os.environ[name] for name in allowed_env if name in os.environ}
        env.update(LLM_MODE="live", PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
        self.process = subprocess.Popen(
            [
                sys.executable,
                "-u",
                str(root / "scripts/harness/live_provider_transport.py"),
                "--project",
                "p01",
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            env=env,
        )
        ready = self._read()
        if ready.get("protocol_version") != 1 or ready.get("status") != "ready":
            self.close()
            raise BoundaryError("guard_denied", ready)

    def request(self, envelope: dict[str, Any]) -> dict[str, Any]:
        if self.stopped:
            raise BoundaryError("workflow_stopped")
        if (envelope.get("campaign_id"), envelope.get("case_id"), envelope.get("trial")) != (
            self.binding.campaign_id,
            self.binding.case_id,
            self.binding.trial,
        ):
            self.close()
            raise BoundaryError("guard_denied")
        try:
            if (
                set(envelope)
                != {
                    "operation",
                    "campaign_id",
                    "case_id",
                    "trial",
                    "call_index",
                    "payload",
                    "timeout_seconds",
                }
                or envelope["operation"] != "complete"
                or type(envelope["call_index"]) is not int
                or envelope["call_index"] != self.next_index
                or not 1 <= self.next_index <= 4
                or envelope["timeout_seconds"] != 20
            ):
                raise BoundaryError("guard_denied")
            input_bound(envelope["payload"])
            line = (
                json.dumps(
                    envelope, ensure_ascii=False, separators=(",", ":"), allow_nan=False
                ).encode("utf-8")
                + b"\n"
            )
            if len(line) > 131072:
                raise BoundaryError("request_schema")
            if self.process is None:
                self._start()
            self.next_index += 1
            self.process.stdin.write(line)
            self.process.stdin.flush()
            result = self._read()
            if result.get("status") != "ok":
                self.close()
            return result
        except BoundaryError:
            self.close()
            raise
        except (KeyboardInterrupt, SystemExit):
            self.close()
            raise
        except Exception:
            self.close()
            raise BoundaryError("provider_timeout_uncertain") from None

    def close(self):
        self.stopped = True
        if self.process is not None:
            if self.process.stdin:
                with suppress(OSError):
                    self.process.stdin.close()
            try:
                self.process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=2)
            if self.process.stdout:
                with suppress(OSError):
                    self.process.stdout.close()
