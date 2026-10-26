# Plan — Bounded campaign ledger for P01

## Execution controls

- `llm_mode`: `fake`; this phase has no provider calls.
- `allowed_write_paths`:
  - `.planning/phases/008-bounded-campaign-ledger/**`
  - `scripts/campaign_ledger.py`
  - `scripts/run_live_campaign.py`
  - `tests/test_campaign_ledger.py`
  - `tests/test_live_campaign_preparation.py`
  - `docs/harness/decisions.md`
  - `docs/harness/failures.md`
  - `docs/harness/progress.md`
  - `docs/knowledge/live-campaign-ledger.md`
  - `artifacts/evidence/live-campaign-ledger/**`
- `forbidden_changes`: root `.env`, campaign datasets/rubrics/config approvals, existing product prompts/adapters, other repositories, harness-kit, paid or free provider calls, Docker mutation, quota/budget increases, external effects, push, and weakened graders.
- Budget: paid USD 0; campaign free quota and all cumulative campaign limits remain `PENDING`. Do not use the earlier single-ticket USD 0.01 exception.
- Validation: focused ledger/preparation tests, P01 fast/full gates, `--help`, offline dry-run, and blocked execution. Save exact command, exit code, and sanitized output.
- Stop condition: no dispatch implementation or provider call in this phase. Any unresolved prerequisite leaves campaign status `INCOMPLETE`.

## Tasks

1. **Specify ledger and lease behavior in tests first** — cover immutable reservation/outcome transitions, unknown-usage retention, duplicate refusal, cumulative cap races, and cross-process lease exclusion/release.
2. **Implement durable P01 campaign state** — add a SQLite append-only journal and OS lease; wire read-only resume inspection into the campaign CLI. Keep results sanitized and preserve uncertain reservations without automatic retries.
3. **Verify fail-closed operation and record evidence** — prove dry-run and pending execution avoid SDK, credentials, provider, and Docker; run focused and full fake checks, update decisions/failures/progress/knowledge, and inspect the staged diff.

## Plan review

Reviewed against root AGENTS.md, the P01 Phase 007 contracts, current CLI/config, and the broad readiness SPEC. Paths stay within P01 and do not overlap dataset/config ownership. The prior single-call exception is explicitly excluded; no finite campaign caps or approvals are inferred. P00 implementation is design reference only; no sibling imports or shared-ledger claim. Accepted for offline execution on 2026-10-26. Clean-context phase review remains required before phase completion.
