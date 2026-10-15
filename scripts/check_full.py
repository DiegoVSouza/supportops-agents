#!/usr/bin/env python3
"""Run unit, synthetic integration, and demo checks; preserve evidence."""
import json
import importlib.metadata
import os
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "artifacts" / "evidence" / "check-full.txt"


def main() -> int:
    os.environ.setdefault("LLM_MODE", "fake")
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    os.environ["PYTHONPATH"] = str(ROOT / "src") + os.pathsep + os.environ.get("PYTHONPATH", "")
    commands = [
        [sys.executable, "scripts/check_fast.py"],
        [sys.executable, "-m", "supportops_agents.comparison", "--output", "artifacts/runs/latest"],
        [sys.executable, "-m", "supportops_agents.demo"],
    ]
    sections = []
    exit_code = 0
    for command in commands:
        result = subprocess.run(command, cwd=ROOT, text=True, encoding="utf-8", errors="replace",
                                capture_output=True, env=os.environ.copy())
        sections.append(f"command={' '.join(command)}\nexit_code={result.returncode}\n{result.stdout}{result.stderr}")
        exit_code = result.returncode
        if exit_code:
            break

    if exit_code == 0:
        try:
            source_lock = json.loads((ROOT / "docs/harness/sources.lock.json").read_text(encoding="utf-8"))
            results = json.loads((ROOT / "artifacts/runs/latest/results.json").read_text(encoding="utf-8"))
            required_docs = ["README.md", "README.pt-BR.md", "docs/knowledge/P01-multi-agent.md"]
            missing = [path for path in required_docs if not (ROOT / path).is_file()]
            if source_lock.get("runtime", {}).get("third_party_dependencies") != []:
                raise ValueError("stdlib core should have no undeclared third-party dependencies")
            if not (ROOT / "uv.lock").is_file():
                raise ValueError("uv.lock is required for framework version reproducibility")
            locked_records = {record["name"]: record for record in source_lock["framework_research"]}
            expected_versions = {
                "langgraph": locked_records["LangGraph Python"]["version"],
                "langgraph-checkpoint-sqlite": locked_records["LangGraph Python"]["sqlite_checkpoint_extra"].split("==", 1)[1],
                "crewai": locked_records["CrewAI"]["version"],
                "autogen-agentchat": locked_records["AutoGen classic"]["version"],
                "semantic-kernel": locked_records["Semantic Kernel classic"]["version"],
                "llama-index-core": locked_records["LlamaIndex Workflows"]["version"],
            }
            for package, expected in expected_versions.items():
                actual = importlib.metadata.version(package)
                if actual != expected:
                    raise ValueError(f"{package} version {actual} does not match sources lock {expected}")
            if len(results.get("runners", [])) != 6 or missing:
                raise ValueError(f"runner or documentation contract failed; missing={missing}")
            if results.get("evaluation_metrics") != "PENDING":
                raise ValueError("synthetic run must not claim model-quality metrics")
            mismatches = [f"{runner['runner']}:{case['case_id']}" for runner in results["runners"]
                          for case in runner.get("cases", []) if case.get("contract_match") is False]
            if mismatches:
                raise ValueError("shared golden contract mismatch: " + ", ".join(mismatches))
            sections.append("command=check comparison JSON, sources lock, and required documentation\nexit_code=0\n6 runner identities found; metrics remain PENDING")
            consumer = next((entry for entry in source_lock.get("package_consumers", [])
                             if entry.get("package") == "supportops-foundation"), None)
            recorded = results.get("p00_package_consumer")
            if (consumer is None or not isinstance(recorded, dict)
                    or recorded.get("version") != consumer.get("version")
                    or recorded.get("source_commit") != consumer.get("source_commit")
                    or recorded.get("wheel_sha256") != consumer.get("wheel_sha256")):
                raise ValueError("P00 installed-wheel provenance is missing or mismatched")
            bad_coverage = [runner["runner"] for runner in results["runners"]
                            if runner["status"] != "EXECUTED" or len(runner.get("cases", [])) != 60
                            or any(case.get("contract_match") is None and not case.get("unsupported_semantics")
                                   for case in runner.get("cases", []))]
            if results.get("golden_case_coverage") != "COMPLETE" or bad_coverage:
                exit_code = 2
                sections.append("product_gate=INCOMPLETE\nrequired=60 P00 golden cases per eligible runner "
                                "with unsupported semantics labeled\nmissing=" + ", ".join(bad_coverage))
            incomplete = [runner["runner"] for runner in results["runners"] if runner["status"] != "EXECUTED"]
            if incomplete:
                exit_code = 2
                sections.append("product_gate=INCOMPLETE\nmissing=" + ", ".join(incomplete) +
                                "\nFramework adapters and their contract validations are required for approval.")
        except Exception as error:
            exit_code = 1
            sections.append(f"command=check comparison JSON, sources lock, and required documentation\nexit_code=1\n{error}")

    report = "\n\n".join(sections)
    EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE.write_text(report, encoding="utf-8")
    print(report)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
