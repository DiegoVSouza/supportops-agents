# Verification

PASS: red-first test exposed the one-call-only ledger; correction passed eight focused tests and 77 locked fake unit tests. The default remains one call, explicit counts must be integers in 1–4, and persisted requests count against cumulative caps. The locked full six-runner gate passed on an isolated snapshot of source commit `403d153`, preserving preexisting modified outputs. Evidence: `artifacts/evidence/workflow-reservation-017/`. Accounted live workflow remains INCOMPLETE until its owning allocation and controller are implemented.

Additional compatibility verification: the actual ledger's four-call record is accepted by the frozen-source guard; all 22 accounted Core tests passed. The first compatibility attempt failed because the older test fixture created a simplified schema; attempt 2 replaces that disposable fixture schema with the actual ledger schema and passes. No real ledger was modified.
