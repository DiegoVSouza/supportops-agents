# Verify — Bounded campaign ledger for P01

Save commands, exit codes and sanitized output in `artifacts/evidence/live-campaign-ledger/`.

- [ ] Ledger persists reservations before results, records known usage, retains unknown usage, and forbids mutation/deletion of journal history.
- [ ] Duplicate and uncertain trials cannot be rerun; cap checks are cumulative and safe under concurrent reservations.
- [ ] A second process cannot acquire the active lease; lease releases on normal exit and metadata is secret/content free.
- [ ] Resume inspection is read-only, rejects unknown/empty campaign IDs with exit 2, and does not dispatch uncertain attempts.
- [ ] Generation remains blocked while any quota, cumulative cap, reviewer approval, or model preflight prerequisite is pending.
- [ ] Focused tests, fast checks, and full fake-mode project gate pass; no provider or Docker access occurs.
- [ ] Evidence/report, decisions, failures, progress and Portuguese/bilingual knowledge are updated; staged diff is reviewed and atomically committed.
- [ ] Independent clean-context review performed; unresolved items remain explicitly `INCOMPLETE`.
