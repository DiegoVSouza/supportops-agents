# Plan

1. Implement a local controller with injected fixture clients and lease, durable reservation before dispatch, no retry, conservative unknown usage, stable identity and bounded synthetic input.
2. Test success, no replay, failed/uncertain work, lease contention and accounting failures; run locked fake checks and isolated full gate without touching preexisting outputs.

allowed_write_paths: `.planning/phases/018-synthetic-operation-controller/**`, `scripts/local_operation.py`, `tests/test_local_operation.py`, `artifacts/evidence/synthetic-operation-controller-018/**`, `artifacts/evidence/synthetic-operation-controller-018-tmp/**`.

forbidden_changes: real ledger or policies, evaluation allocations, live opt-in, credentials, provider calls, historical artifacts, unrelated files, sibling projects, customer data, paid use, external effects or weaker tests. Fake mode and zero calls / USD 0. max_tries: 3 per local failure. Live execution requires separately validated ownership and funding; user evaluation remains pending. Plan-check is implementer self-assessment.
