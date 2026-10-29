# Plan

1. Add red-first tests for four-call reservations, cumulative limits, persistence and invalid counts.
2. Correct the ledger and run focused and full locked fake regressions in an isolated committed snapshot; preserve existing modified outputs.

allowed_write_paths: `.planning/phases/017-workflow-reservation/**`, `scripts/campaign_ledger.py`, `tests/test_campaign_ledger.py`, `tests/test_accounted_core.py` (ledger/guard compatibility), `artifacts/evidence/workflow-reservation-017/**`, `artifacts/evidence/workflow-reservation-017-tmp/**`.

forbidden_changes: existing ledger files, historical evidence, unrelated user files, sibling projects, provider calls, credentials, budgets, live opt-in, customer data, external effects and weakened tests. Fake mode; budget zero calls / USD 0. max_tries: 3 per failure. Plan-check is implementer self-assessment. Stop on uncertain external work.
