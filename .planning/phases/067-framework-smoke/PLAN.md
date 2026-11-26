# Plan

Allowed paths: `src/supportops_agents/registry.py`, `src/supportops_agents/accounted_frameworks.py`, `src/supportops_agents/accounted_live.py`, `scripts/framework_smoke.py`, `evals/live-execution.json`, `tests/test_accounted_frameworks.py`, this phase, and new campaign artifacts.

1. Expose live framework construction only via an explicit adapter argument; preserve telemetry disabling and deterministic worker serialization.
2. Add an isolated one-trial-per-runner campaign, exact manifest, 20-call ledger cap, and root usage preflight.
3. Run fake contracts and fast gate, commit, freeze, and execute only through the root transport.

No holdout, tool side effects, retries, direct provider access, or old-campaign replay.
