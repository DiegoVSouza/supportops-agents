# P01 execution plan

## Task 1 — Specify and test the live client boundary

Add offline mocked tests for agent-specific JSON parsing, configured mode, provider catalog check, bounded retry/key rotation, and budget enforcement. Preserve the existing `LLMClient` contract and test every required agent response field.

## Task 2 — Implement one Groq-backed Core run

Add an optional pinned Groq SDK extra and a P01-local client/evaluation script. Run only one synthetic ticket via `CoreTriageRunner`, serialize the four worker calls, apply per-call token limits and a USD 0.01 run budget, and write sanitized metrics to phase-004 artifacts.

## Task 3 — Validate and evaluate

Run focused tests and full offline gate; then query model availability and execute one bounded live Core run. Analyze decision, action, escalation, step order, usage, cost, and failure classifications. Adjust only a proven orchestration/prompt defect; preserve a failed real result and do not tune repeatedly to a single sample.

## Ownership

`allowed_write_paths`: `.planning/phases/004-live-groq-eval/**`, `scripts/run_live_groq_eval.py`, `src/supportops_agents/live_groq.py`, `tests/test_live_groq_eval.py`, `pyproject.toml`, `uv.lock`, `README.md`, `docs/harness/decisions.md`, `docs/harness/progress.md`, `artifacts/runs/phase-004/**`, `artifacts/evidence/phase-004-groq-*`.

`forbidden_changes`: `harness-kit/**`, `.env`, other projects, golden fixture, prior reports, and unrelated framework adapter behavior.

## Runtime and limits

- Explicit live mode only; Groq `openai/gpt-oss-20b`; one model-list preflight and one sequential Core ticket.
- Four agent steps at most; 256 completion tokens each; 20s timeout; USD 0.01 estimated exposure, lower than configured USD 2/task.
- Bounded key pass for retryable throttling/transient failures; no retry on auth, invalid model, validation, or agent contract failure. No paid-provider fallback.

## Validation

Use P01's documented `check_full.py` and focused live client tests. Save commands, exit codes, and sanitized outputs to `artifacts/evidence/phase-004-groq-*`.
