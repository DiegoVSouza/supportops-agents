# Plan

1. Test the five existing runners through the accounted fixture boundary and record red output; identify deviations in state, ordering, concurrency, retries and termination without changing existing campaign state.
2. Implement the smallest fixture-safe accounted runner integration and any necessary framework-specific controls; preserve runner semantics and stop before unaccounted, duplicate or uncertain calls. Never enable network access here.
3. Run focused and full fake checks, record commands, exit codes and output in phase evidence; document any runner that cannot satisfy the contract instead of claiming completion. Plan the separately owned root-guard and live allocation only after the fixture boundary is verified.

allowed_write_paths: `.planning/phases/029-accounted-framework-adapters/**`, `src/supportops_agents/**`, `tests/**`, `artifacts/evidence/accounted-framework-adapters-029/**`, `docs/harness/decisions.md`, `docs/harness/progress.md`, `docs/harness/failures.md`, `docs/harness/feature_list.json`.

forbidden_changes: root guard and policy, prior campaign evidence or ledgers, holdout and confirmation reserves, credentials, other projects, and live registry access. `LLM_MODE=fake`; no provider calls. Stop on uncertain dispatch, exhausted repair attempts, or an unmet external prerequisite. Three total attempts per reproducible repair; record them.
