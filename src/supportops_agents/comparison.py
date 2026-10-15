"""Run identical synthetic cases and make missing framework coverage explicit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import tempfile
from time import perf_counter

from .contracts import Ticket
from .fakes import FakeLLMClient
from .registry import RUNNER_NAMES, RunnerUnavailable, get_runner


GOLDEN_CASES = (
    {"id": "duplicate-charge", "ticket": Ticket("g-001", "Duplicate charge", "I was charged twice."),
     "expected": "respond", "responses": {}},
    {"id": "safety-escalation", "ticket": Ticket("g-002", "Account threat", "Someone is threatening me."),
     "expected": "escalate", "responses": {"classifier": [{"category": "safety", "summary": "Threat reported", "escalate": "safety escalation"}]}},
    {"id": "refund-review", "ticket": Ticket("g-003", "Large refund", "Please refund my full annual plan."),
     "expected": "escalate", "responses": {"billing_agent": [{"context": "Refund exceeds authority", "escalate": "human billing approval required"}]}},
)

COMPARISON_PROFILES = {
    "core": {"ease": "Low setup; manual loop", "flow": "Custom generic supervisor loop",
             "state": "In-memory typed state", "maturity": "Project-owned core",
             "observability": "Common per-step trace"},
    "langgraph": {"ease": "Graph concepts required", "flow": "Native graph fan-out, conditional edges, node retry",
                  "state": "SQLite checkpoint and resumable interrupt", "maturity": "LangGraph 1.1.10 pinned",
                  "observability": "Graph checkpoints plus common trace"},
    "crewai": {"ease": "Flow decorator API", "flow": "Native Flow events; worker orchestration is custom Python",
               "state": "Per-run Flow object", "maturity": "CrewAI 1.15.28 pinned",
               "observability": "Common trace; Flow events not exported"},
    "autogen": {"ease": "Runtime registration and message types", "flow": "Native Core runtime/messages; supervisor sequencing is custom",
                "state": "Runtime-local; no durable checkpoint", "maturity": "AutoGen 0.7.5 classic; successor noted in ADR-001",
                "observability": "Common trace; framework event logs not exported"},
    "semantic_kernel": {"ease": "Kernel and plugin registration", "flow": "Native Kernel/plugin invocation around a generic sequential supervisor",
                         "state": "Per-run Kernel", "maturity": "Semantic Kernel 1.45.0 classic; successor noted in ADR-001",
                         "observability": "Common trace; no telemetry exporter configured"},
    "llamaindex": {"ease": "Typed event workflow API", "flow": "Native typed Workflow steps; sequencing and responder loop are custom",
                    "state": "Event-carried state", "maturity": "LlamaIndex 0.14.25 Workflows; QueryPipeline deprecated",
                    "observability": "Workflow events plus common trace"},
}


def run_comparison(output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    golden_cases, p00_provenance = _load_golden_cases()
    results = []
    for name in RUNNER_NAMES:
        try:
            if name == "langgraph":
                from .frameworks.langgraph_runner import LangGraphTriageRunner
                checkpoint_tmp = tempfile.TemporaryDirectory(prefix="p01-langgraph-")
                runner = LangGraphTriageRunner(Path(checkpoint_tmp.name) / "checkpoints.sqlite")
            else:
                checkpoint_tmp = None
                runner = get_runner(name)
        except RunnerUnavailable as error:
            results.append({"runner": name, "status": "INCOMPLETE", "reason": str(error), "metrics": _pending_metrics()})
            continue

        started = perf_counter()
        cases = []
        for case in golden_cases:
            ticket = case["ticket"]
            actual = runner.run(ticket, llm=FakeLLMClient(case["responses"]), max_steps=12)
            expected_action = case["expected"]
            category_match = (case["expected_category"] is None
                              or actual.decision.category == case["expected_category"])
            cases.append({"case_id": case["id"], "expected_action": expected_action,
                          "expected_p00_action": case["expected_p00_action"],
                          "observed_action": actual.decision.action,
                          "contract_match": (None if expected_action is None else
                                             actual.decision.action == expected_action and category_match),
                          "unsupported_semantics": case["unsupported_semantics"],
                          "stop_reason": actual.stop_reason, "steps": len(actual.trace)})
        elapsed = perf_counter() - started
        source_files = {
            "core": "core.py",
            "langgraph": "frameworks/langgraph_runner.py",
            "crewai": "frameworks/crewai_runner.py",
            "autogen": "frameworks/autogen_runner.py",
            "semantic_kernel": "frameworks/semantic_kernel_runner.py",
            "llamaindex": "frameworks/llamaindex_runner.py",
        }
        source_lines = len((Path(__file__).parent / source_files[name]).read_text(encoding="utf-8").splitlines())
        results.append({"runner": name, "status": "EXECUTED",
                        "profile": COMPARISON_PROFILES[name],
                        "cases": cases,
                        "implementation_source_lines": source_lines,
                        "metrics": {**_pending_metrics(), "fake_control_wall_time_seconds": elapsed},
                        "note": "Case outcomes check deterministic control behavior; they are not model-quality evaluation."})
        if checkpoint_tmp is not None:
            checkpoint_tmp.cleanup()

    coverage_complete = bool(p00_provenance) and len(golden_cases) == 60 and all(
        len(row.get("cases", [])) == 60 for row in results if row["status"] == "EXECUTED"
    ) and all(row["status"] == "EXECUTED" for row in results)
    payload = {"mode": "fake", "run_kind": "p00_golden_contract_comparison" if p00_provenance else "p01_local_synthetic_smoke",
               "evaluation_metrics": "PENDING", "golden_case_count": len(golden_cases),
               "required_p00_golden_case_count": 60,
               "golden_case_coverage": "COMPLETE" if coverage_complete else "INCOMPLETE",
               "p00_package_consumer": p00_provenance or "not installed; local P01 fixtures used",
               "runners": results}
    (output_dir / "results.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    lines = ["# Framework comparison", "", "Run kind: synthetic fake-mode contract smoke. This is not a model-quality evaluation.",
             "Qualitative fit columns describe this implementation and current official framework docs; they are not measured user-study results.", "",
             "| Runner | Status | Ease (qualitative) | Control flow | State | Maturity | Observability | Source LOC | Cases matched | Fake steps | Accuracy | Tokens | Cost | Model latency |",
             "|---|---|---|---|---|---|---|---:|---:|---:|---|---|---|---|"]
    for item in results:
        n_cases = len(item.get("cases", []))
        cases = item.get("cases", [])
        mean_steps = f"{sum(case['steps'] for case in cases) / n_cases:.1f}" if n_cases else "PENDING"
        matched = sum(case["contract_match"] is True for case in cases)
        eligible = sum(case["contract_match"] is not None for case in cases)
        profile = item.get("profile", {})
        lines.append(f"| {item['runner']} | {item['status']} | {profile.get('ease', 'PENDING')} | {profile.get('flow', 'PENDING')} | {profile.get('state', 'PENDING')} | {profile.get('maturity', 'PENDING')} | {profile.get('observability', 'PENDING')} | {item.get('implementation_source_lines', 'PENDING')} | {matched}/{eligible} eligible ({n_cases} cases) | {mean_steps} | PENDING | PENDING | PENDING | PENDING |")
    coverage_text = (f"60 P00 cases from installed wheel {p00_provenance['version']} (source commit "
                     f"{p00_provenance['source_commit']}, SHA-256 {p00_provenance['wheel_sha256']}).") if p00_provenance else (
                     f"{len(golden_cases)} P01-local cases; the P00 wheel fixture is unavailable.")
    lines += ["", "## Coverage and implementation boundaries", "",
              f"This run covers {coverage_text} P00 decision fields that P01 cannot represent are listed under `unsupported_semantics`; eligible action/category behavior is checked per case. Case outcomes are control-flow checks, not a representative benchmark.", "",
              "The adapters do not delegate every orchestration concern to their framework. LangGraph uses native graph nodes, conditional edges, retries, checkpointing, and interrupts. CrewAI uses native Flow start/listener events but custom Python workers and supervisor logic. AutoGen uses its native Core runtime and routed messages while the supervisor sequences worker calls. Semantic Kernel supplies native Kernel/plugin invocation around a custom sequential supervisor. LlamaIndex uses native typed Workflow steps and events while the ordering and responder loop remain custom. Only the framework-specific capabilities listed in each row were exercised; other behavior is supplied by the shared adapter code.",
              "", "## Selection notes", "", "- `core`: use for minimal dependency footprint and explicit deterministic stop conditions.",
              "- `langgraph`: choose when graph retries, SQLite checkpoint recovery, and HITL interrupts are the main requirements.",
              "- `crewai`: choose role/task organization with structured Flow control.",
              "- `autogen`: use the classic runtime for compatibility with existing AutoGen Core applications; see ADR-001.",
              "- `semantic_kernel`: use the classic plugin/kernel model when integrating with existing Semantic Kernel code; see ADR-001.",
              "- `llamaindex`: use Workflows when orchestration centers on retrieval and data components.",
              "", "Fake step counts are observed worker calls from this synthetic run. Accuracy, tokens, cost, and model latency remain `PENDING`; fake mode does not measure model quality.", ""]
    (output_dir / "COMPARISON.md").write_text("\n".join(lines), encoding="utf-8")
    return payload


def _load_golden_cases() -> tuple[list[dict], dict | None]:
    fixture = Path(__file__).resolve().parents[2] / "artifacts/fixtures/p00-golden-1.0.1.json"
    if not fixture.is_file():
        return list(GOLDEN_CASES), None
    payload = json.loads(fixture.read_text(encoding="utf-8"))
    provenance = {key: payload[key] for key in ("package", "version", "source_commit", "wheel_sha256", "seed")}
    cases = []
    for row in payload["cases"]:
        source_ticket = row["ticket"]
        expected = row["expected"]
        p00_action = expected["action"]
        mapped = "escalate" if expected["escalate"] or p00_action == "escalate" else "respond"
        supported = p00_action in {"answer", "request_info", "escalate"}
        unsupported = ["priority", "rationale"]
        if p00_action in {"answer", "request_info"}:
            unsupported.append(f"P00 action distinction {p00_action!r} maps to P01 'respond'")
        elif not supported:
            unsupported.append(f"P00 action {p00_action!r} has no P01 equivalent")
        classifier = {"category": expected["category"], "summary": f"Golden fixture {row['id']}"}
        if mapped == "escalate":
            classifier["escalate"] = "Golden expected escalation"
        ticket = Ticket(source_ticket["id"], source_ticket["subject"], source_ticket["body"],
                        source_ticket["customer_id"])
        cases.append({"id": row["id"], "ticket": ticket,
                      "expected": mapped if supported else None,
                      "expected_p00_action": p00_action, "expected_category": expected["category"],
                      "unsupported_semantics": unsupported,
                      "responses": {"classifier": [classifier]}})
    if len(cases) != payload.get("case_count"):
        raise ValueError("P00 golden fixture case count does not match its payload")
    return cases, provenance


def _pending_metrics() -> dict:
    return {"accuracy": "PENDING", "steps": "PENDING", "tokens": "PENDING", "cost_usd": "PENDING", "latency": "PENDING"}


def main() -> None:
    import os
    import sys

    os.environ.setdefault("LLM_MODE", "fake")
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="artifacts/runs/latest")
    args = parser.parse_args()
    payload = run_comparison(Path(args.output))
    print(json.dumps({"run_kind": payload["run_kind"], "runners": [(r["runner"], r["status"]) for r in payload["runners"]]}, indent=2))


if __name__ == "__main__":
    main()
