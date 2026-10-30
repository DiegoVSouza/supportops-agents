# Verification plan

Root phase042 guard commit `80d332a` accepts the new P01 identity, refuses the consumed P01 identity and preserves P04's scope; seven guard tests and account/transport regressions passed. The migration dry-run returned `ALREADY_APPLIED`, exit0, with the canonical policy SHA and 86 historical provider attempts; no credential or provider access. Evidence: `artifacts/evidence/reviewed-operation-027/migration-recheck.json`.

Controller focused attempt3 PASS: ten tests including prior workflows/reservations, duplicate marker, crash after reservation, failure/unknown no-replay and finite bounds. Gate attempt1 and attempt2 passed on earlier source snapshots; final full gate attempt3 PASS: 119 tests and six runners, exit0, saved as `artifacts/evidence/reviewed-operation-027/full-attempt3.json`. All snapshots retain hashes of the three pre-existing modified outputs. Provider calls0 during validation; human review PENDING.

PENDING: review staged source, commit and freeze binding, then check credential/model/usage and reserve before the one authorized invocation. Treat a started or uncertain attempt as consumed.
