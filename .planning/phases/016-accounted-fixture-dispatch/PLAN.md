# Plan

1. Add failing tests for accounted fixture-client dispatch, refusal for live or unknown transport, durable duplicate and failure handling.
2. Implement the narrow Core guard and run the owning locked fake checks without overwriting preexisting artifacts; save sanitized commands and exits.

allowed_write_paths: `.planning/phases/016-accounted-fixture-dispatch/**`, `src/supportops_agents/core.py`, `tests/test_core_fixture_dispatch.py`, `artifacts/evidence/accounted-fixture-dispatch-016/**`, `artifacts/evidence/accounted-fixture-dispatch-016-tmp/**`.

forbidden_changes: previous evidence and user changes, sibling projects, dataset and evaluation gates, runtime live opt-in, budgets, provider calls, credentials, Docker lifecycle, real data, external effects, test weakening. LLM_MODE=fake; budget zero calls / USD 0. max_tries: 3 per failure. Stop on uncertain external work or scope mismatch. Plan-check is implementer self-assessment.
