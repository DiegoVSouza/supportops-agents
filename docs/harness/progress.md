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

## 2026-10-26 — Phase 004 live Core evaluation

- Added optional Groq 1.7.0 support for the Core runner only. Four numbered credentials are preflighted; the client caps each of four serial calls at 256 tokens and total estimated exposure at USD 0.01. Fake mode remains the default and imports no SDK unless live is used.
- The real model first returned a JSON-mode validation error; local JSON parsing fixed the provider error. Initial real cases over-escalated routine questions; adding a general escalation threshold fixed the issue. Offline tests also found and fixed exception text leaking before the sanitization boundary.
- Final four-key live run passed: 4 steps in order, 1470 input / 655 output tokens, estimated cost USD 0.00030675. Full fake comparison gate passed across six runners.

## 2026-10-26 — Live evaluation readability cleanup

- Use a normal Path import, initialize optional client state explicitly, extract retry and artifact helpers, and replace nested mock factories with ordinary Mock instances.
- Full offline gate: PASS (26 tests and all six fake runner comparisons).
- Offline helper and static checks passed; no live calls were needed. Evidence: artifacts/evidence/code-cleanup/.

## 2026-10-26 — Live Docker acceptance

One real Core workflow passed all domain assertions with four serial calls (1470 input / 588 output tokens). The deterministic full comparison passed for all six installed runners; live acceptance covers Core only. Evidence: artifacts/evidence/live-docker/.

## 2026-10-26 — Phase 007 campaign preparation

- Added 60 synthetic Core orchestration cases with a fixed 18/42 development/holdout split, 36/24 English/Portuguese coverage, and seven required families. Dataset SHA-256: `6884c47eb34ae46b1c1a8aa94735bec871315a1ad60aaffb39dace4cf7b1259f`.
- Added code-first decision/route/order/termination grader tests and an offline dry-run. It reports pilot 24 calls, primary campaign 720, confirmation reserve 240, and 984 calls if all stages are additive; no provider, credential, or Docker access occurs.
- Campaign preparation tests: 7 passed. Fast/full gates passed with 33 tests; six framework comparisons and demo remain fake/offline. Evidence: `artifacts/evidence/live-campaign-preparation/phase-007-preparation.md`.
- Dataset/rubric review, expanded quota/spend/token/timing caps, durable lease/ledger and live runtime acceptance remain `PENDING`/`INCOMPLETE`. No Groq calls were made.
