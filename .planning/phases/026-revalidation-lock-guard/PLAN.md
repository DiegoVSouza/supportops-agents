# Plan

1. Add a lock-aware validation path: perform the root migration dry-run before acquiring the shared campaign lease; while holding the lease, recheck the frozen source/policy/owner/manifest and exact append-only root history directly without recursively invoking the migration subprocess. Add deterministic tests for the nested-lock failure and the corrected locked validation path.
2. Run focused tests and the complete locked fake gate in an isolated committed-source snapshot. Preserve the pre-existing modified `artifacts/evidence/check-fast.txt`, `check-full.txt` and `artifacts/runs/latest/results.json` byte-for-byte. No Docker/provider use.
3. Record the repaired source fingerprint, the consumed live attempt's exact no-marker/no-reserve/no-provider result, and the continuation condition. No live invocation is in scope; any new workflow requires a separately authorized scope and new stable ID.

allowed_write_paths: `.planning/phases/026-revalidation-lock-guard/**`; `scripts/revalidation_operation.py`; `tests/test_revalidation_operation.py`; `artifacts/evidence/revalidation-operation-026/**`; `docs/harness/progress.md`; `docs/harness/failures.md`.

forbidden_changes: root policy/auth/migration, P01 original/diagnostic/revalidation IDs/results/manifests/provider receipts/logical rows/reservations, evaluation data/rubrics/expectations, user-modified standard gate outputs, sibling projects, credentials, any provider/model call, network access, Docker lifecycle, customer data/effects, fallback, paid use, human annotations, deployment/push/PR/merge. `LLM_MODE=fake` only. Provider call budget 0; new logical/provider reserve 0; paid USD 0. `max_tries:3` for local validation failures; no live retry/replay. Plan-check is implementer self-assessment.
