# Verification

Status: INCOMPLETE pending the v2 freeze and live results.

| Check | Result | Evidence |
|---|---|---|
| Campaign v1 provider calls | 0, root provider ledger | `artifacts/evals/live/p01-framework-smoke-v1/live-run-r2.txt` |
| Campaign v2 LangGraph calls | 4 root attempts, all `ok`; workflow returned, executor receipt check failed | `artifacts/evals/live/p01-framework-smoke-v2/reconciliation.json` |
| Project test suite (152 passed, 65 subtests) | PASS, exit 0 | `artifacts/evidence/framework-smoke-recovery-tests-r2.txt` |
| Campaign v2 live smoke | PENDING | v2 campaign artifacts |
