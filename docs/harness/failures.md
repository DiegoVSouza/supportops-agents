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


## 2026-10-27 — Core step budget exceeded live call contract

The P01 `CoreTriageRunner` defaulted to twelve steps and accepted caller budgets above four. If the responder never approved, fake/local execution could call it repeatedly; live mode eventually stopped at the accounted client's fourth-call boundary, so the product API and live guard disagreed. A red regression proved `max_steps=5,6,12,100` invoked the client before returning. The Core runner now defaults to four and rejects values over four before the first call. The separate model tool-call regression confirms effectful tool requests stop after one accounted call and cannot be replayed. No tool executor or external effect exists on this path.

The first fast-gate run then exposed two fake comparison/contract callers still requesting twelve steps from Core. The owning comparison now uses Core's four-step contract while each framework adapter keeps its prior limit. This correction leaves the golden dataset and graders unchanged; the final locked gate passes all six runner slots and keeps quality metrics PENDING.
## 2026-10-30 — Phase 026 revalidation lock reentrancy

The already-authorized P01 revalidation returned `INCOMPLETE` before writing its invocation marker or creating a reservation. Read-only reproduction found that the controller acquired the shared campaign lease and then ran root migration validation, whose dry-run tried to acquire the same lease. The offline fix keeps the migration dry-run before lease acquisition and skips only that lock-taking subprocess in the locked validation; frozen-source, owner, manifest and reviewed-history checks still run under the lease. The regression confirms there is no nested lock and stops before marker/preflight. Focused 8-test unittest and isolated fake full gate (109 tests, six runners) pass. The consumed live operation was not retried and remains INCOMPLETE.

## 2026-11-09 — p01-dev-v1 pilot stopped by a provider error on the fourth trial; no quality number

- Sealed run of the frozen candidate (`996037d`, manifest `artifacts/evals/live/p01-dev-v1/manifest.json`, commit `ce8e5d7`): Core supervisor/worker only, Groq `openai/gpt-oss-20b`, free-plan keys, pilot of 4 development cases x 1 trial. Catalog preflight PASS. Three trials were graded; trial 4 (`p01-live-045`) completed call 1 and then call 2 returned `provider_error` in the root usage ledger. The executor stopped with `uncertain_or_failed_provider_attempt`, wrote `stop.json` (`replay_allowed` false) and the root account now treats the campaign as closed (`prior_operational_failure_requires_review`). No replay, no new campaign ID, no development run.
- The provider error carries no error code in the ledger (the root ledger keeps `status` and rate-limit feedback only), so its cause is UNKNOWN. A strict-schema rejection on the second worker is plausible, because the same kind of stop was seen in P05, but nothing recorded proves it.
- What the three graded trials show, with no generalisation: `p01-live-001` and `p01-live-011` ran all four workers and ended at `max_steps` because the responder returned `approved: false`, so the expected `approved` stop reason failed (and `facts_missing` for 001); `p01-live-037` escalated at the classifier (1 call) with the right category but its escalation reason did not contain the required fact terms. Passed 0 of 3. Tokens: the three graded trials used 9 accounted calls, 2,725 input and 693 output tokens; trial 4 added one ok call (326 input, 114 output) and the failed call. Estimated cost is about USD 0.0004 at policy pricing; the provider-billed amount is UNKNOWN.
- Reading: the grader asks for an approved stop within four steps and the prompt never says when to approve, so part of the 0 of 3 is a prompt and grader gap, not only model weakness. The prompt, grader and dataset were not changed after the pilot. A changed candidate needs its own campaign and authorization.
- Limits: 3 trials, one per case; assistant-authored expectations, term groups and grader; human review PENDING; independent review WAIVED_BY_OWNER (owner approval, not independent verification); holdout not opened; the other five runners were not run live.
