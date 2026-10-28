# Plan

1. Add regressions for allowed plans, malformed and effectful plans, caller-supplied fixture identity, duplicate run reuse, uncertain dispatch and the four-call ceiling.
2. Implement optional fake-only Core binding to the existing dispatcher; preserve existing no-plan behavior and live tool rejection.
3. Run locked focused and full fake gates, preserve the four pre-existing output files byte-for-byte and record evidence.

allowed_write_paths: `.planning/phases/014-core-fixture-dispatch/**`, `src/supportops_agents/core.py`, `tests/test_core_fixture_dispatch.py`, `artifacts/evidence/core-fixture-dispatch-014/**`, `docs/harness/progress.md`. forbidden_changes: live client/transport, prompt, dataset, rubric, ledger, source integrations, effectful actions, customer data, siblings, provider calls and reviews. Existing modified gate outputs may be temporarily overwritten only if restored exactly. Fake mode, USD 0, zero provider calls. Stop on untrusted identity, provider access, uncertain effects or test failure. Plan-check self-assessment; independent review PENDING.
