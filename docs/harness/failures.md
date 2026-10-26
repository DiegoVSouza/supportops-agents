# Failures

Record recurring builder or product failures here before fixing them.
## 2026-10-26 — Phase 008 campaign ledger

- A completed attempt with missing provider usage initially replaced its reservation with zero token/cost values in cumulative accounting. The completion event now copies the original reservation; a regression confirms the full amount remains reserved.
- The first multiprocessing regression used a nested Windows worker and leaked SQLite connections in test setup. Windows spawn requires top-level targets, and SQLite context managers do not close connections. The tests now use top-level workers/explicit closure; concurrent cap and lease tests pass.
- Unknown and completed trials remain immutable and cannot be rerun. No semantic errors were rerun and no grader was changed.