# Verify

Status: fixture integration verified; live framework execution remains INCOMPLETE. No live quality or framework comparison is claimed.

- [x] Red import test and focused output saved. The first isolated fast check failed because the snapshot did not preserve the lab directory layout; the corrected second attempt passed. Evidence: `artifacts/evidence/accounted-framework-adapters-029/`.
- [x] Five framework runners use fixture receipts; focused tests cover four-call limits, early escalation, and no retry after an uncertain call.
- [x] LangGraph parallel calls are serialized at the fixture boundary; a forced reverse arrival and an uncertain second call are covered. Framework retries do not repeat a failed accounted request in the tested cases.
- [x] Corrected isolated snapshot fast and full gates passed before the additional focused parallel-failure test; the latter passed separately. Neither check overwrote existing modified run evidence.
- [x] Live registry access and allocations remain disabled; prior accounting and reserves were not changed. Live campaigns need a separate phase and root authorization.
