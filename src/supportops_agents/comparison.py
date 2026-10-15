"""Run identical synthetic cases and make missing framework coverage explicit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import tempfile
from time import perf_counter
from uuid import uuid4

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
    "core": {"ease": "Low setup; manual loop", "flow": "Explicit bounded supervisor loop",
             "state": "In-memory typed state", "maturity": "Project-owned core",
             "observability": "Common per-step trace"},
    "langgraph": {"ease": "Graph concepts required", "flow": "Parallel fan-out, conditional edges, node retry",
                  "state": "SQLite checkpoint and resumable interrupt", "maturity": "LangGraph 1.1.10 pinned",
                  "observability": "Graph checkpoints plus common trace"},
    "crewai": {"ease": "Flow decorator API", "flow": "Start/listener Flow methods",
               "state": "Per-run Flow object", "maturity": "CrewAI 1.15.28 pinned",
               "observability": "Common trace; Flow events not exported"},
    "autogen": {"ease": "Runtime registration and message types", "flow": "Routed AutoGen Core messages",
                "state": "Runtime-local; no durable checkpoint", "maturity": "AutoGen 0.7.5 classic; successor noted in ADR-001",
                "observability": "Common trace; framework event logs not exported"},
    "semantic_kernel": {"ease": "Kernel and plugin registration", "flow": "Sequential plugin invocation",
                         "state": "Per-run Kernel", "maturity": "Semantic Kernel 1.45.0 classic; successor noted in ADR-001",
                         "observability": "Common trace; no telemetry exporter configured"},
    "llamaindex": {"ease": "Typed event workflow API", "flow": "Workflow steps and responder loop",
                    "state": "Event-carried state", "maturity": "LlamaIndex 0.14.25 Workflows; QueryPipeline deprecated",
                    "observability": "Workflow events plus common trace"},
}


def run_comparison(output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
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
        for case in GOLDEN_CASES:
            ticket = case["ticket"]
            if name == "langgraph":
                ticket = Ticket(f"{ticket.id}-{uuid4().hex}", ticket.subject, ticket.description, ticket.customer_id)
            actual = runner.run(ticket, llm=FakeLLMClient(case["responses"]), max_steps=12)
            cases.append({"case_id": case["id"], "expected_action": case["expected"],
                          "observed_action": actual.decision.action, "contract_match": actual.decision.action == case["expected"],
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

    payload = {"mode": "fake", "run_kind": "synthetic_contract_smoke", "evaluation_metrics": "PENDING",
               "golden_case_count": len(GOLDEN_CASES), "runners": results}
    (output_dir / "results.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    lines = ["# Framework comparison", "", "Run kind: synthetic fake-mode contract smoke. This is not a model-quality evaluation.",
             "Qualitative fit columns describe this implementation and current official framework docs; they are not measured user-study results.", "",
             "| Runner | Status | Ease (qualitative) | Control flow | State | Maturity | Observability | Source LOC | Cases matched | Fake steps | Accuracy | Tokens | Cost | Model latency |",
             "|---|---|---|---|---|---|---|---:|---:|---:|---|---|---|---|"]
    for item in results:
        n_cases = len(item.get("cases", []))
        cases = item.get("cases", [])
        mean_steps = f"{sum(case['steps'] for case in cases) / n_cases:.1f}" if n_cases else "PENDING"
        matched = sum(case["contract_match"] for case in cases)
        profile = item.get("profile", {})
        lines.append(f"| {item['runner']} | {item['status']} | {profile.get('ease', 'PENDING')} | {profile.get('flow', 'PENDING')} | {profile.get('state', 'PENDING')} | {profile.get('maturity', 'PENDING')} | {profile.get('observability', 'PENDING')} | {item.get('implementation_source_lines', 'PENDING')} | {matched}/{n_cases} | {mean_steps} | PENDING | PENDING | PENDING | PENDING |")
    lines += ["", "## Selection notes", "", "- `core`: use for minimal dependency footprint and explicit deterministic stop conditions.",
              "- `langgraph`: choose when graph retries, SQLite checkpoint recovery, and HITL interrupts are the main requirements.",
              "- `crewai`: choose role/task organization with structured Flow control.",
              "- `autogen`: use the classic runtime for compatibility with existing AutoGen Core applications; see ADR-001.",
              "- `semantic_kernel`: use the classic plugin/kernel model when integrating with existing Semantic Kernel code; see ADR-001.",
              "- `llamaindex`: use Workflows when orchestration centers on retrieval and data components.",
              "", "Fake step counts are observed worker calls from this synthetic run. Accuracy, tokens, cost, and model latency remain `PENDING`; fake mode does not measure model quality.", ""]
    (output_dir / "COMPARISON.md").write_text("\n".join(lines), encoding="utf-8")
    return payload


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
