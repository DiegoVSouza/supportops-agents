# Plan

1. Reconcile the phase025 consumed invocation, exact historical ledgers, applied migration, capacity and shared guard. Record the stable operation identity and dependency on a separately planned root guard change.
2. Implement the new single-use controller and owner scope with tests for old identity denial, duplication, retained historical reservations, crash and unknown-result no-replay. Protect standard user outputs using isolated snapshots.
3. Run fake locked gates and preserve commands, exit codes and outputs; freeze a committed-source manifest only after PASS. Dispatch once only if root guard, authenticated limits, exact reservations and all bindings PASS; retain uncertainty without replay.

allowed_write_paths: `.planning/phases/027-distinct-operation/**`, `scripts/reviewed_operation_027.py`, `tests/test_reviewed_operation_027.py`, `src/supportops_agents/accounted_live.py`, `evals/live-execution.json`, `artifacts/evidence/reviewed-operation-027/**`, `artifacts/evals/live/local-reviewed-operation-027-v1/**`, `docs/harness/progress.md`.

forbidden_changes: historical operations, manifests, receipts, reservations and ledgers except the one explicitly authorized new reservation after all gates; user-modified check-fast.txt, check-full.txt and results.json; sibling projects; root guard without a separate root phase; paid spend, fallback, customer data, external effects, holdout, promotion or invented review.

Fake mode by default; provider calls zero during validation, live maximum four calls, 8192 input/1024 output, bounded timeout, USD 0 paid, one workflow and no replay. Stop on unknown existing work, missing capacity, stale manifest, gate failure or uncertain invocation. Plan-check is implementer self-assessment.
