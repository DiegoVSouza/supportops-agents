# Plan

Allowed paths: `scripts/framework_smoke.py`, `evals/live-execution.json`, `src/supportops_agents/accounted_live.py`, `tests/test_accounted_frameworks.py`, this phase, and new `artifacts/evals/live/p01-framework-smoke-v2/` output.

1. Use `projects/p01/` manifest keys and bind v2 to the recovery authorization.
2. Preserve the v1 failed-pre-dispatch records and existing project ledger.
3. Run full fake gates, commit, freeze v2, then execute up to five framework trials within the shared 20-call cap.
