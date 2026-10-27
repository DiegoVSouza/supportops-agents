# Phase 011 plan

## Ownership

`allowed_write_paths`:

- `.planning/phases/011-real-tool-source-contract/**`
- `shared/tools/p01-search-knowledge.proposed.md`
- `shared/tools/p01-lookup-billing.proposed.md`
- `docs/knowledge/core-tool-safety.md`
- `docs/harness/progress.md`
- `docs/harness/failures.md`
- `artifacts/evidence/real-tool-source-contract-011/**`

`forbidden_changes`: `artifacts/evidence/check-fast.txt`, `artifacts/evidence/check-full.txt`, `artifacts/runs/latest/results.json` (pre-existing user modifications), all datasets/fixtures/expected facts/splits/rubrics/graders/thresholds, `src/**`, prompt files, campaign config/manifest/ledger/registry, root account policy/ledger, secrets, sibling projects, framework adapters, external sources/network, Docker, customer data, effectful tools, paid use, or approvals.

## Tasks

1. Inspect P01-owned source, ADR-002, phase 009/010, tool policy and campaign preconditions. Record file-level evidence for the live boundary and the missing real source; do not read credentials or user-modified gate outputs beyond their already observed Git status/hashes.
2. Write proposed read-only `search_knowledge` and `lookup_billing` contracts and an effectful-tool prerequisite checklist. Run only the content-free offline development dry-run, store command/exit/output in the phase evidence directory, and mark implementation INCOMPLETE because no eligible source or tenant authorization contract exists.

## Validation

- `uv run --locked --offline python scripts/run_live_campaign.py --stage development --dry-run`
- Confirm dry-run reports `generation_authorized=false`, `provider_accessed=false`, and `credentials_read=false`.
- `git -c core.whitespace=cr-at-eol diff --check`; compare SHA-256 of the three forbidden pre-existing outputs before and after. This project worktree has CRLF files while the index has LF, so the check explicitly treats only CR at line end as a line-ending marker.
- Do not run `check_fast.py` or `check_full.py` in this documentation-only phase because they overwrite those tracked, user-modified outputs. No product code changes, so no product test claim is made.

## Budget and stop conditions

- USD 0; zero provider requests, credential reads, network calls, Docker operations, and data-source access.
- Stop if a real P01-owned source or authorization contract is unexpectedly found; create a new SDD implementation phase for it rather than substituting a fixture. Stop if dry-run attempts external access or changes a ledger/output, or if any forbidden path changes.
- Live campaign dispatch remains blocked until account billing/quota and all existing review/allocation gates are resolved. Effects remain disabled until separately approved and funded.
