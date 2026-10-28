# Verification

PASS for fixture process-death recovery: a child exits immediately inside the adapter after durable reservation; restart rejects that run without invoking the adapter again. Five focused tests and the locked fake full gate (67 tests and six runner comparisons) passed. Four pre-existing output hashes match before and after. Evidence is under `artifacts/evidence/dispatch-process-recovery-013/`. This does not establish real effect idempotency, authenticated identity or live dispatch. Independent and human review remain PENDING; no provider calls were made.
