# Plan

1. Add separate controller and owner manifest scope with exact root authority/history checks, source binding, reserve-before-startup and sanitized diagnostics/receipts; tests keep both prior histories and full12 ceiling.
2. Run locked focused and isolated full fake gates, preserving modified user outputs; freeze committed corrected candidate and distinct manifest.
3. Invoke once with explicit live under shared lease, reconcile receipts/logical outcome, preserve all old records and stop on any error with no replay.

allowed_write_paths: .planning/phases/023-second-reviewed-diagnostic/**; scripts/second_diagnostic_operation.py; tests/test_second_diagnostic_operation.py; evals/live-execution.json; artifacts/evals/live/local-diagnostic-2-v1/manifest.json; artifacts/evals/live/ledger.sqlite* (new scope append only); artifacts/evals/live/provider-usage.sqlite* (shared guard only); artifacts/evidence/second-reviewed-diagnostic-023/**; docs/harness/progress.md.
forbidden_changes: original/first diagnostic code, histories/IDs/manifests/reservations, other caps/holdout/confirmation, sibling imports, credentials disclosure, paid use/fallback, external effects and human annotations. Fake default; exactly one approved invocation/max4calls2048/256/20s each, USD0. max_tries3 local failures; no live replay. Stop on missing authority/source/history/schema/provider/receipt failure. Plan-check implementer self-assessment.
