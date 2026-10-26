# Verify — Bounded campaign ledger for P01

Save commands, exit codes and sanitized output in `artifacts/evidence/live-campaign-ledger/`.

- [x] Ledger persists reservations before results, records known usage, retains unknown usage, and forbids mutation/deletion of journal history.
- [x] Duplicate and uncertain trials cannot be rerun; cap checks are cumulative and safe under concurrent reservations.
- [x] A second process cannot acquire the active lease; lease releases on normal exit and metadata is secret/content free.
- [x] Resume inspection is read-only, rejects unknown/empty campaign IDs with exit 2, and does not dispatch uncertain attempts.
- [x] Generation remains blocked while any quota, cumulative cap, reviewer approval, or model preflight prerequisite is pending.
- [x] Focused tests (6), fast checks, and full fake-mode project gate (40 tests) pass; no provider or Docker access occurs.
- [x] Evidence/report, decisions, failures, progress and Portuguese/bilingual knowledge are updated; staged diff is reviewed and atomically committed.
- [ ] Independent clean-context review performed; unresolved items remain explicitly `INCOMPLETE`.

Campaign dispatch, integration of the lease into an approved live execution path, cross-project accounting, human dataset/rubric sign-off, finite quota/cost limits and model preflight are not implemented or approved in this phase. Promotion remains `INCOMPLETE`.
