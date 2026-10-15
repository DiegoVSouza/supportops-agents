# Progress

- Intake and phase 001 artifacts created before product code.
- Core supervisor-worker and local domain contract doubles implemented; fake-mode contract tests cover all six runners for approval, escalation, and step termination.
- Git audit evidence: `artifacts/evidence/git-setup.md`.
- The `frameworks` dependency group is pinned by `uv.lock`; exact versions are recorded in `docs/harness/sources.lock.json`.
- LangGraph implements parallel KB/billing, per-node retries, SQLite checkpoints, and resumable HITL for refunds above the configured threshold.
- CrewAI, AutoGen classic, Semantic Kernel classic, and LlamaIndex adapters are implemented and pass the shared synthetic golden set.
- Full gate passed: 19 tests, six runners, comparison report, and offline demo. Real-model accuracy, tokens, cost, latency, and formal capability evaluations remain `PENDING` / out of scope.
