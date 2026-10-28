# Plan

1. Add an isolated subprocess crash regression using a phase-owned temporary SQLite database and a synthetic invocation marker.
2. Run focused and full locked fake gates; preserve pre-existing modified gate outputs byte-for-byte and record outputs.

allowed_write_paths: `.planning/phases/013-dispatch-process-recovery/**`, `tests/test_synthetic_dispatch.py`, `artifacts/evidence/dispatch-process-recovery-013/**`. forbidden_changes: live execution, provider, credentials, customer data, existing ledgers, other projects, previously modified gate outputs except temporary overwrite followed by exact restoration. Budget USD 0, zero provider calls; stop on unexpected modification or failing gate. Plan-check self-assessment; independent review PENDING.
