# Progress

- Intake and phase 001 artifacts created before product code.
- Core supervisor-worker and local domain contract doubles implemented; fake-mode contract tests cover all six runners for approval, escalation, and step termination.
- Git audit evidence: `artifacts/evidence/git-setup.md`.
- The `frameworks` dependency group is pinned by `uv.lock`; exact versions are recorded in `docs/harness/sources.lock.json`.
- LangGraph implements parallel KB/billing, per-node retries, SQLite checkpoints, and resumable HITL for refunds above the configured threshold.
- CrewAI, AutoGen classic, Semantic Kernel classic, and LlamaIndex adapters are implemented and pass the shared synthetic golden set.
- Full gate at prior state passed: 19 tests, six runners, three local cases, comparison report, and offline demo. That smoke did not establish P00 golden coverage.

## 2026-10-15 — Phase 003 run/checkpoint identity

- LangGraph now assigns a unique checkpoint thread ID to every fresh invocation, even when the business ticket ID repeats.
- A caller-provided `resume_key` maps to a stable ticket-scoped checkpoint identity and enables resume from another runner process. In-process resume without a key targets only that runner's latest execution.
- Regression evidence first reproduced stale interrupt reuse and unsupported cross-process `resume_key`; the fixed focused test run and full fake gate are saved in `artifacts/evidence/check-fast.txt` and `artifacts/evidence/check-full.txt`.
- P00 package 1.0.1 was installed in an isolated consumer environment and exported the versioned 60-case fixture. Source commit and wheel SHA-256 are recorded in `docs/harness/sources.lock.json`.
- The isolated wheel export avoids a dependency conflict in the shared runtime environment: P00 pins Pydantic 2.14.1, while the locked CrewAI 1.15.28 requires Pydantic below 2.13. P01 runtime continues to use its local domain doubles; only the comparison fixture comes from P00's installed package.
- All six adapters executed all 60 cases in fake mode. Unsupported P00 decision fields and answer/request-info distinctions are recorded per case. Full-gate output is in `artifacts/evidence/check-full.txt`.
- Accuracy, tokens, cost, latency, and formal evaluation remain `PENDING`; fake-run step counts are control-flow observations only.
