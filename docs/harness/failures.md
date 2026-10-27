# Failures

Record recurring builder or product failures here before fixing them.
## 2026-10-26 — Phase 008 campaign ledger

- A completed attempt with missing provider usage initially replaced its reservation with zero token/cost values in cumulative accounting. The completion event now copies the original reservation; a regression confirms the full amount remains reserved.
- The first multiprocessing regression used a nested Windows worker and leaked SQLite connections in test setup. Windows spawn requires top-level targets, and SQLite context managers do not close connections. The tests now use top-level workers/explicit closure; concurrent cap and lease tests pass.
- Unknown and completed trials remain immutable and cannot be rerun. No semantic errors were rerun and no grader was changed.
## 2026-10-27 — Legacy provider bypass and uncertain rotation

The old Core adapter loaded root credentials and constructed SDK clients without the shared account/receipt boundary, rotating to another key after a transient failure. Red regressions with credential/SDK operations mocked as forbidden reproduced that bypass without a provider call. Phase 009 replaces the unauthorized path with an explicit guard-required failure and exercises the real Core loop through the accounted adapter. Historical smoke reports and the old retry baseline remain preserved; no evaluation expectation, grader or threshold was weakened.

## 2026-10-27 — Offline framework telemetry

Installed CrewAI/CoreTelemetry code enables telemetry unless its disable flags are set. Registry entrypoints now enforce offline-only framework scope and set OTEL_SDK_DISABLED, CREWAI_DISABLE_TELEMETRY and CREWAI_DISABLE_TRACKING before imports. The actual six-runner comparison passed a Python socket-denial probe with zero external attempts. Historical telemetry activity was not recorded and is not reconstructed as fact.

## 2026-10-27 — Fixture SQLite handles

New committed-source/ledger fixture tests initially used SQLite context managers without closing connections, preventing Windows temporary-directory cleanup. Explicit closing and commits correct the fixture resource lifecycle; the failed run remains in `red-fixture-handles.txt`. Production guard reads already used read-only connections with explicit closure. Final full checks passed 60 tests.
