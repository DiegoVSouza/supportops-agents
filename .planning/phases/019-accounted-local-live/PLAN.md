# Plan

1. Adapt the local controller and guard to a committed operation-specific manifest, fixed synthetic cases, shared campaign lease and durable four-call reservations; retain fixture mode.
2. Test fake transport, provenance, accounting, no replay and crash/uncertainty; run locked fake unit and isolated full gates without overwriting user changes.
3. Freeze candidate and manifest, verify the applied shared allocation and run at most one synthetic workflow; stop on first provider, quota, semantic or uncertain failure and save only sanitized evidence.

allowed_write_paths: `.planning/phases/019-accounted-local-live/**`, `scripts/local_operation.py`, `src/supportops_agents/accounted_live.py`, `evals/live-execution.json`, `tests/test_local_operation.py`, `tests/test_accounted_core.py`, `artifacts/evals/live/local-operation-v1/manifest.json`, `artifacts/evals/live/ledger.sqlite*` (normal append-only reservation/outcome only), `artifacts/evals/live/provider-usage.sqlite*` (normal shared guard only), `artifacts/evidence/accounted-local-live-019/**`, `artifacts/evidence/accounted-local-live-019-tmp/**`.

forbidden_changes: prior ledgers/results, other allocations, holdout/confirmation, model/provider fallback, paid use, customer data, real effects, public deployment, Docker lifecycle, review fabrication and weakened tests. Eight free calls maximum, USD 0 paid; one workflow smoke up to four calls. max_tries: 3 local corrections; no live completion replay. Stop on unknown work, quota, provider or semantic failure, missing provenance or exhausted allowance. Plan-check is implementer self-assessment; evaluation remains PENDING.
