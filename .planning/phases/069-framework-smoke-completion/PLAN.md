# Plan

Allowed paths: `scripts/framework_smoke.py`, `src/supportops_agents/accounted_frameworks.py`, `src/supportops_agents/accounted_live.py`, `evals/live-execution.json`, `tests/test_accounted_frameworks.py`, this phase, and new `artifacts/evals/live/p01-framework-smoke-v3/` output.

1. Validate live receipts using the safe diagnostic fields.
2. Limit v3 to CrewAI, AutoGen, Semantic Kernel, and LlamaIndex (16 calls maximum).
3. Run full fake tests, commit, freeze, execute through the root transport, and reconcile all v1–v3 attempts without replay.
