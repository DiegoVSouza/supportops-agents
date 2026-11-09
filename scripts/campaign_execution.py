"""Sealed, resumable executor for the P01 `p01-dev-v1` Core development campaign.

Live attempts go through the existing accounted boundary (`AccountedCoreClient` + `SubprocessGuard`, root transport
v1); nothing here reads a credential. Trial records are content-free: no ticket text, no prompt, no model text.
Fixture runs exercise every code path with a no-network oracle transport, are labelled `fixture` and never count as
live. Only the Core runner is executed; the five framework runners stay fake/replay.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import sqlite3
import subprocess
import time
from contextlib import closing, nullcontext
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Callable

from scripts.campaign_ledger import CampaignBlocked, CampaignLedger
from scripts.campaign_observe import TERMS, WORKERS, Outcome, grade, observe
from supportops_agents.accounted_live import (
    MODEL,
    AccountedCoreClient,
    BoundaryError,
    SubprocessGuard,
    WorkflowBinding,
)
from supportops_agents.contracts import Ticket
from supportops_agents.core import CoreTriageRunner, InvalidAgentResponse

CAMPAIGN = "p01-dev-v1"
DATASET = "p01-live-v1"
AUTHORIZATION = ".planning/llm-live-readiness/phases/059-p01-live-campaign/AUTHORIZATION.json"
PILOT_IDS = ("p01-live-001", "p01-live-011", "p01-live-037", "p01-live-045")
PRICE_IN, PRICE_OUT = Decimal("0.075"), Decimal("0.30")
TRIAL_RESERVE = {"calls": 4, "input_tokens": 8192, "output_tokens": 1024}
TRIAL_COST = Decimal("0.0009216")
# The cumulative ceilings the accounted boundary itself enforces over the whole logical ledger.
LEDGER_CAPS = {"requests": 744, "input_tokens": 1523712, "output_tokens": 190464, "estimated_cost_usd": Decimal("0.1714176")}
SEMANTIC = {"worker_contract", "output_schema", "output_truncated", "request_schema", "tool_selection", "call_limit", "worker_order"}
PRE_DISPATCH = {"request_schema", "call_limit", "worker_order"}
SAFE_REASON = re.compile(r"[a-z_]{1,64}")
GUARD_OWN = (
    "scripts/campaign_ledger.py", "scripts/run_live_campaign.py", "scripts/run_live_groq_eval.py",
    "agent/prompts/live-core.md", "evals/live-execution.json", "evals/live-campaign.json",
    "evals/datasets/live-v1/cases.jsonl", "evals/datasets/live-v1/manifest.json", "evals/rubrics/live-v1/rubric.md",
    "pyproject.toml", "uv.lock",
)
GUARD_SHARED = (
    "scripts/harness/live_free_account.py", "scripts/harness/live_provider_transport.py",
    "shared/policies/groq-free-campaign.json",
)
CHECKS = ("wrong_category", "wrong_action", "wrong_escalate", "wrong_stop_reason", "wrong_agent_order", "facts_missing", "forbidden_outcome", "contract_failure")


def cost_of(input_tokens: int, output_tokens: int) -> Decimal:
    return (Decimal(input_tokens) * PRICE_IN + Decimal(output_tokens) * PRICE_OUT) / 1000000


class ExecutionBlocked(RuntimeError):
    """A fixed, content-free stop reason."""


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def wilson(successes: int, total: int) -> list[float] | None:
    if total <= 0:
        return None
    z = 1.959963984540054
    p = successes / total
    denominator = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / denominator
    margin = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    return [round(max(0.0, centre - margin), 4), round(min(1.0, centre + margin), 4)]


def percentile(values: list[float], pct: int) -> float | None:
    """Nearest-rank percentile; None for an empty sample."""
    if not values:
        return None
    ordered = sorted(values)
    return ordered[max(0, math.ceil(pct / 100 * len(ordered)) - 1)]


def stats(values: list[float]) -> dict[str, Any]:
    return {
        "n": len(values), "p50": percentile(values, 50), "p95": percentile(values, 95),
        "max": max(values) if values else None, "mean": round(sum(values) / len(values), 1) if values else None,
    }


# --- provenance ---------------------------------------------------------------------------------

def git(repository: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=repository, capture_output=True, timeout=30)
    if result.returncode:
        raise ExecutionBlocked("source_provenance")
    return result.stdout.decode("utf-8", errors="strict").strip()


def source_paths(project: Path) -> list[str]:
    return sorted(
        path for path in git(project, "ls-files").splitlines()
        if path.startswith(("src/", "scripts/", "tests/", "agent/", "evals/"))
        or path in {"pyproject.toml", "uv.lock", "harness.yaml"}
    )


def guard_file_set(project: Path, lab: Path) -> dict[str, Path]:
    """Exactly the file set `SubprocessGuard` requires in the manifest, keyed by path relative to the lab."""
    own = sorted((project / "src/supportops_agents").rglob("*.py")) + [project / name for name in GUARD_OWN]
    shared = [lab / name for name in GUARD_SHARED]
    return {path.relative_to(lab).as_posix(): path for path in own + shared}


def fingerprint(project: Path, lab: Path) -> str:
    paths = source_paths(project)
    root_files = list(GUARD_SHARED) + [AUTHORIZATION]
    git(project, "diff", "--quiet", "HEAD", "--", *paths)
    git(lab, "diff", "--quiet", "HEAD", "--", *root_files)
    values = [("p01/" + p, hashlib.sha256((project / p).read_bytes()).hexdigest()) for p in paths]
    values += [(p, hashlib.sha256((lab / p).read_bytes()).hexdigest()) for p in root_files]
    return hashlib.sha256(json.dumps(values, separators=(",", ":")).encode()).hexdigest()


def ordered_cases(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    dev = [c for c in cases if c["split"] == "development"]
    by_id = {c["case_id"]: c for c in dev}
    if set(PILOT_IDS) - set(by_id):
        raise ExecutionBlocked("pilot_case_missing")
    return [by_id[i] for i in PILOT_IDS] + [c for c in dev if c["case_id"] not in set(PILOT_IDS)]


def freeze(project: Path, lab: Path, out_dir: Path, cases_path: Path, cases: list[dict[str, Any]]) -> dict[str, Any]:
    """Write the manifest the accounted boundary reads; refuses to overwrite a frozen one."""
    order = [c["case_id"] for c in ordered_cases(cases)]
    files = {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in guard_file_set(project, lab).items()}
    manifest = {
        "authorization_id": "p01-live-campaign-059-v1",
        "campaign_id": CAMPAIGN,
        "candidate_commit": git(project, "rev-parse", "HEAD"),
        "dataset_sha256": hashlib.sha256(cases_path.read_bytes()).hexdigest(),
        "files_sha256": files,
        "frozen_at": utc_now(),
        "human_review": "PENDING",
        "max_input_tokens": TRIAL_RESERVE["input_tokens"],
        "max_output_tokens": TRIAL_RESERVE["output_tokens"],
        "max_provider_calls": TRIAL_RESERVE["calls"],
        "model": MODEL,
        "pilot_case_ids": list(PILOT_IDS),
        "promotion": "PENDING",
        "root_policy_sha256": hashlib.sha256((lab / "shared/policies/groq-free-campaign.json").read_bytes()).hexdigest(),
        "sampling_order": order,
        "source_fingerprint": fingerprint(project, lab),
        "stage": "development",
        "trials_per_case": 1,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / "manifest.json").open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return manifest


def validate_manifest(project: Path, lab: Path, out_dir: Path, cases_path: Path, cases: list[dict[str, Any]]) -> dict[str, Any]:
    try:
        manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise ExecutionBlocked("manifest_missing") from None
    if (
        manifest.get("campaign_id") != CAMPAIGN
        or manifest.get("source_fingerprint") != fingerprint(project, lab)
        or manifest.get("dataset_sha256") != hashlib.sha256(cases_path.read_bytes()).hexdigest()
        or manifest.get("sampling_order") != [c["case_id"] for c in ordered_cases(cases)]
    ):
        raise ExecutionBlocked("manifest_mismatch")
    candidate = manifest.get("candidate_commit")
    if not isinstance(candidate, str) or len(candidate) != 40:
        raise ExecutionBlocked("candidate_missing")
    git(project, "merge-base", "--is-ancestor", candidate, "HEAD")
    git(project, "diff", "--quiet", candidate, "--", *source_paths(project))
    return manifest


# --- transports and trial runners ---------------------------------------------------------------

class OracleTransport:
    """Plumbing proof only: answers like a perfect model, makes no network call, is labelled `fixture`."""

    provenance = "fixture"

    def __init__(self, cases_by_id: dict[str, dict[str, Any]]):
        self.cases_by_id = cases_by_id
        self.counts: dict[str, list[int]] = {}
        self.serial = 0

    def request(self, envelope: dict[str, Any]) -> dict[str, Any]:
        body = json.loads(envelope["payload"]["messages"][1]["content"])
        case = self.cases_by_id[body["input"]["ticket"]["id"]]
        text = " ".join(group[0] for group in TERMS[case["case_id"]])
        expected = case["expected"]
        worker = body["worker"]
        if worker == "classifier":
            content = {"category": expected["category"], "summary": text, "escalate": text if expected["escalate"] else ""}
        elif worker == "kb_researcher":
            content = {"context": "unavailable"}
        elif worker == "billing_agent":
            content = {"context": "unavailable", "escalate": ""}
        else:
            content = {"response": text, "approved": True}
        self.serial += 1
        row = self.counts.setdefault(case["case_id"], [0, 0, 0])
        row[0] += 1
        row[1] += 120
        row[2] += 40
        return {
            "status": "ok", "model": MODEL, "attempt_id": f"{self.serial:032x}",
            "usage": {"input_tokens": 120, "output_tokens": 40}, "content": json.dumps(content),
            "finish_reason": "stop", "latency_ms": 10.0 + self.serial,
        }

    def usage_for(self, case_id: str) -> dict[str, int]:
        calls, inp, out = self.counts.get(case_id, [0, 0, 0])
        return {"calls": calls, "input_tokens": inp, "output_tokens": out}


def safe_reason(error: BaseException) -> str:
    reason = error.diagnostic["reason"] if isinstance(error, BoundaryError) else str(error)
    if isinstance(error, (BoundaryError, ExecutionBlocked)) and SAFE_REASON.fullmatch(reason):
        return reason
    return "uncertain_attempt"


def run_core(case: dict[str, Any], transport: Any, binding: WorkflowBinding, project: Path | None = None) -> tuple[Outcome, list[dict[str, Any]]]:
    """One Core run through the accounted client. Semantic failures are graded; everything else stops the campaign."""
    kwargs = {"project": project} if project is not None else {}
    client = AccountedCoreClient(transport, binding, **kwargs)
    ticket = Ticket(case["case_id"], "Synthetic support request", case["input"])
    try:
        result = CoreTriageRunner().run(ticket, llm=client, max_steps=case["max_steps"])
        return Outcome(result=result), client.receipts
    except BoundaryError as error:
        reason = error.diagnostic["reason"]
        if reason not in SEMANTIC:
            raise ExecutionBlocked(safe_reason(error)) from None
        index = len(client.receipts) if reason in PRE_DISPATCH else max(len(client.receipts) - 1, 0)
        worker = WORKERS[min(index, len(WORKERS) - 1)]
        return Outcome(failure=reason, failure_worker=worker, agent_order=list(WORKERS[:index])), client.receipts
    except InvalidAgentResponse:
        index = max(len(client.receipts) - 1, 0)
        return Outcome(failure="worker_contract", failure_worker=WORKERS[min(index, 3)], agent_order=list(WORKERS[:index])), client.receipts
    finally:
        client.close()


class FixtureTrialRunner:
    provenance = "fixture"

    def __init__(self, transport: Any):
        self.transport = transport

    def run(self, case: dict[str, Any]) -> tuple[Outcome, list[dict[str, Any]]]:
        return run_core(case, self.transport, WorkflowBinding(CAMPAIGN, case["case_id"], 1))


class LiveTrialRunner:
    """One `SubprocessGuard` (root transport v1, one process) per trial; needs the frozen manifest."""

    provenance = "live"

    def __init__(self, project: Path):
        self.project = project

    def run(self, case: dict[str, Any]) -> tuple[Outcome, list[dict[str, Any]]]:
        binding = WorkflowBinding(CAMPAIGN, case["case_id"], 1)
        try:
            guard = SubprocessGuard(binding, project=self.project)
        except BoundaryError as error:
            raise ExecutionBlocked(safe_reason(error)) from None
        return run_core(case, guard, binding, self.project)


def root_usage_reader(project: Path, campaign: str) -> Callable[[str], dict[str, int]]:
    """Exact provider-side usage of one case, read from the append-only usage ledger."""
    path = project / "artifacts/evals/live/provider-usage.sqlite"

    def read(case_id: str) -> dict[str, int]:
        try:
            with closing(sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)) as db:
                reserved = db.execute(
                    "SELECT COUNT(*) FROM usage_events WHERE campaign=? AND case_id=? AND event='reserved'", (campaign, case_id),
                ).fetchone()[0]
                done = db.execute(
                    "SELECT COALESCE(SUM(actual_input),0),COALESCE(SUM(actual_output),0),COUNT(*),COALESCE(SUM(status!='ok'),0) "
                    "FROM usage_events WHERE campaign=? AND case_id=? AND event='completed'", (campaign, case_id),
                ).fetchone()
        except sqlite3.Error:
            raise ExecutionBlocked("provider_usage_proof_unavailable") from None
        if done[2] != reserved or done[3]:
            raise ExecutionBlocked("uncertain_or_failed_provider_attempt")
        return {"calls": reserved, "input_tokens": int(done[0]), "output_tokens": int(done[1])}

    return read


# --- trials -------------------------------------------------------------------------------------

def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")
        stream.flush()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def execute_campaign(
    *,
    cases: list[dict[str, Any]],
    runner: Any,
    out_dir: Path,
    ledger_path: Path,
    usage_reader: Callable[[str], dict[str, int]],
    max_trials: int,
    min_gap_seconds: float = 75.0,
    sleep: Callable[[float], None] = time.sleep,
    lock: Any = None,
) -> dict[str, Any]:
    """Run up to `max_trials` unfinished trials in order; stop on the first infrastructure problem."""
    if max_trials < 1:
        raise ExecutionBlocked("max_trials_required")
    out_dir.mkdir(parents=True, exist_ok=True)
    if (out_dir / "stop.json").exists():
        raise ExecutionBlocked("campaign_stopped_requires_review")
    ledger = CampaignLedger(ledger_path, campaign_id=CAMPAIGN)
    events = ledger.reserved_trials()
    completed = {row["case_id"] for row in events if row["event"] == "completed"}
    reserved = {row["case_id"] for row in events if row["event"] == "reserved"}
    if reserved - completed:
        raise ExecutionBlocked("uncertain_trial_requires_review")
    queue = [c for c in ordered_cases(cases) if c["case_id"] not in completed]
    ran = 0
    with lock if lock is not None else nullcontext():
        for case in queue[:max_trials]:
            if ran:
                sleep(min_gap_seconds)
            try:
                ledger.reserve(case_id=case["case_id"], trial=1, estimated_cost_usd=TRIAL_COST, caps=LEDGER_CAPS, **TRIAL_RESERVE)
            except CampaignBlocked:
                raise ExecutionBlocked("campaign_reservation_refused") from None
            try:
                outcome, receipts = runner.run(case)
                usage = usage_reader(case["case_id"])
                used_in = sum(r["usage"]["input_tokens"] for r in receipts if r["usage"])
                used_out = sum(r["usage"]["output_tokens"] for r in receipts if r["usage"])
                if usage != {"calls": len(receipts), "input_tokens": used_in, "output_tokens": used_out}:
                    raise ExecutionBlocked("usage_mismatch")
            except ExecutionBlocked as stop:
                _stop(ledger, out_dir, case, str(stop), usage_reader)
                raise
            except Exception:  # noqa: BLE001 - any other failure is a fixed, content-free stop
                _stop(ledger, out_dir, case, "uncertain_attempt", usage_reader)
                raise ExecutionBlocked("uncertain_attempt") from None
            observation = observe(case, outcome)
            errors = grade(case, observation)
            cost = cost_of(used_in, used_out)
            ledger.complete(case_id=case["case_id"], trial=1, input_tokens=used_in, output_tokens=used_out,
                            actual_cost_usd=cost, outcome="graded", error_class=observation["failure"])
            latencies = [r["latency_ms"] for r in receipts]
            known = all(v is not None for v in latencies) and bool(latencies)
            append_jsonl(out_dir / "trials.jsonl", {
                "campaign": CAMPAIGN, "case_id": case["case_id"], "family": case["family"], "language": case["language"],
                "trial": 1, "pilot": case["case_id"] in PILOT_IDS, "provenance": runner.provenance,
                "pass": not errors, "errors": errors, "observation": observation, "provider_calls": len(receipts),
                "input_tokens": used_in, "output_tokens": used_out, "estimated_cost_usd": str(cost),
                "latency_ms_per_call": latencies, "latency_ms_trial": round(sum(latencies), 3) if known else None,
                "recorded_at": utc_now(),
            })
            ran += 1
    return {"ran": ran, "remaining": max(0, len(queue) - ran)}


def _stop(ledger: CampaignLedger, out_dir: Path, case: dict[str, Any], reason: str, usage_reader: Callable[[str], dict[str, int]]) -> None:
    reason = reason if SAFE_REASON.fullmatch(reason) else "uncertain_attempt"
    try:
        calls = usage_reader(case["case_id"])["calls"]
    except ExecutionBlocked:
        calls = None
    (out_dir / "stop.json").write_text(
        json.dumps({"campaign": CAMPAIGN, "case_id": case["case_id"], "reason": reason, "provider_calls": calls,
                    "replay_allowed": False, "stopped_at": utc_now()}, indent=2) + "\n",
        encoding="utf-8", newline="\n",
    )
    try:
        ledger.complete(case_id=case["case_id"], trial=1, input_tokens=None, output_tokens=None, actual_cost_usd=None,
                        outcome="stopped", error_class=reason)
    except CampaignBlocked:
        pass


# --- report -------------------------------------------------------------------------------------

def build_report(cases: list[dict[str, Any]], out_dir: Path, *, provenance: str) -> dict[str, Any]:
    trials = read_jsonl(out_dir / "trials.jsonl")
    dev = ordered_cases(cases)
    passed = sum(t["pass"] for t in trials)

    def group(key: str) -> dict[str, Any]:
        groups: dict[str, list[dict[str, Any]]] = {}
        for t in trials:
            groups.setdefault(t[key], []).append(t)
        return {
            name: {"trials": len(rows), "passed": sum(r["pass"] for r in rows), "wilson95": wilson(sum(r["pass"] for r in rows), len(rows))}
            for name, rows in sorted(groups.items())
        }

    failures = {name: sum(name in t["errors"] for t in trials) for name in CHECKS}
    inp = sum(t["input_tokens"] for t in trials)
    out = sum(t["output_tokens"] for t in trials)
    per_call = [v for t in trials for v in t["latency_ms_per_call"] if v is not None]
    per_trial = [t["latency_ms_trial"] for t in trials if t["latency_ms_trial"] is not None]
    observations = [t["observation"] for t in trials]
    complete = len(trials) == len(dev)
    return {
        "campaign": CAMPAIGN,
        "dataset": DATASET,
        "split": "development",
        "scope": "core_only",
        "other_runners_live": "NOT_RUN",
        "other_runners": {name: "fake_replay_only" for name in ("langgraph", "crewai", "autogen", "semantic_kernel", "llamaindex")},
        "provenance": provenance,
        "status": "COMPLETE" if complete else "INCOMPLETE",
        "model": MODEL,
        "live_model": {
            "cases_planned": len(dev),
            "trials": len(trials),
            "passed": passed,
            "pass_rate": round(passed / len(trials), 4) if trials else None,
            "wilson95": wilson(passed, len(trials)),
            "by_family": group("family"),
            "by_language": group("language"),
            "failed_checks": failures,
            "provider_calls": sum(t["provider_calls"] for t in trials),
            "calls_per_trial_mean": round(sum(t["provider_calls"] for t in trials) / len(trials), 2) if trials else None,
            "input_tokens": inp,
            "output_tokens": out,
            "tokens_per_trial": {
                "input_mean": round(inp / len(trials), 1) if trials else None,
                "output_mean": round(out / len(trials), 1) if trials else None,
                "input_max": max((t["input_tokens"] for t in trials), default=None),
                "output_max": max((t["output_tokens"] for t in trials), default=None),
            },
            "estimated_cost_usd": str(cost_of(inp, out)),
            "estimated_cost_per_trial_usd": str((cost_of(inp, out) / len(trials)).quantize(Decimal("0.0000001"))) if trials else None,
            "latency_ms": {"per_call": stats(per_call), "per_trial": stats(per_trial)},
        },
        "behaviour": {
            "completed_runs": sum(o["completed"] for o in observations),
            "contract_failures": {name: sum(o["failure"] == name for o in observations) for name in sorted({o["failure"] for o in observations if o["failure"]})},
            "early_escalations": sum(o["completed"] and o["step_count"] < 4 and o["stop_reason"] == "escalated" for o in observations),
            "effect_claims": sum(o["effect_claimed"] for o in observations),
            "secret_requests": sum(o["secret_requested"] for o in observations),
            "duplicate_worker_runs": sum(o["duplicate_worker"] for o in observations),
        },
        "limits": [
            "Core runner only; the other five runners (langgraph, crewai, autogen, semantic_kernel, llamaindex) were not run live, so this is not a cross-framework quality comparison",
            "development split only; the 42 holdout cases were not opened",
            "expected outcomes, required-fact term groups and the grader are assistant-authored; human review is PENDING",
            "independent review is WAIVED_BY_OWNER, which is owner approval and not independent verification",
            "route (billing, knowledge, none) is not graded: the Core boundary supplies no billing or knowledge tools, so the expected route cannot be observed",
            "one trial per case and two to three cases per family; the interval is wide and the result is not a generalisation claim",
            "cost is an estimate at the policy price on free-plan keys; the provider-billed amount stays UNKNOWN",
            "latency is the client-side time of each chat request from the transport receipts; it is not a service-level measurement",
        ],
        "human_review": "PENDING",
        "independent_review": "WAIVED_BY_OWNER",
        "raw_provider_content_persisted": False,
    }


def write_report(report: dict[str, Any], out_dir: Path) -> Path:
    path = out_dir / "report.json"
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return path
