# Plan

1. Audit current original provider/logical rows and source/manifest identity without credentials/network or ledger writes; compute finite recovery arithmetic and preserve user-modified outputs by hash.
2. Write the disabled decision proposal and read-only evidence; run fast/full checks only in a fresh committed snapshot so existing outputs remain unchanged, then review explicit staged paths and commit.

allowed_write_paths: .planning/phases/020-reviewed-recovery-proposal/**; artifacts/evidence/recovery-proposal-020/**.
forbidden_changes: original manifest/IDs/results, runtime code, historical ledgers/reservations, provider calls, credentials, other budgets, holdout/confirmation, Docker, existing modified gate outputs and weakened tests. Budget zero calls/USD 0 paid. max_tries: 3 per failure, preserve existing phase-019 failure. Stop on unexpected rows, missing metadata or changed protected hashes. Plan-check: implementer self-assessment. This proposal cannot authorize execution.
