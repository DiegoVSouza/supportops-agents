# Plan

1. Add deterministic tests for bounded plans, trusted context, duplicate and concurrent claims, completed receipts, and interrupted dispatch.
2. Implement a local SQLite-backed read-only dispatcher with injected synthetic adapters; use FULL synchronous transactions and reject unknown outcomes on restart.
3. Run focused and locked full fake checks, preserving pre-existing modified gate artifacts, and record evidence and limitations.

allowed_write_paths: `.planning/phases/012-synthetic-dispatch/**`, `src/supportops_agents/synthetic_dispatch.py`, `tests/test_synthetic_dispatch.py`, `artifacts/evidence/synthetic-dispatch-012/**`, `docs/harness/progress.md`. The existing three modified standard output files may be temporarily overwritten by the required gate only if their exact bytes are restored afterwards.

forbidden_changes: external source integrations, live dispatch, model prompts, real customer data, provider credentials, campaign policy/ledgers, effectful operations, sibling sources, promotion and human approvals.

llm_mode: fake; budget: zero provider calls and USD 0. Validation: locked focused tests and `uv run --locked python scripts/check_full.py`, with output and exit recorded; hash the three pre-existing modified output files before and after. Stop on altered user artifacts, actual external calls, unexpected effects, or failing checks.

Plan-check: self-assessment; independent review PENDING. Fixtures do not demonstrate real integration, external authorization or exactly-once effects.
