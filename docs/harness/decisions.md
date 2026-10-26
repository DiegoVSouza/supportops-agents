# Intake decisions

## 2026-10-15 — Independent orchestration comparison

- The product implements deterministic SupportOps ticket triage and compares the pure Python runner with five executable framework integrations.
- P00's versioned domain package is not available. P01 keeps a local contract double in `src/supportops_agents/contracts.py`; replacing it requires an approved P00 package with version, source commit, and artifact hash.
- `LLM_MODE=fake` remains the default. Phase 004 adds an opt-in Groq live path; framework comparisons and tests stay fake/replay offline.
- ADR-001 selects classic AutoGen and Semantic Kernel APIs to preserve the historical comparison targets. Microsoft Agent Framework 1.0 is their documented successor and is not silently substituted. Exact versions are pinned in `uv.lock`; adapters have executable contract coverage.
- Multi-agent manager/children, session state, and tool contracts are enabled because they match the product. MCP, production sampling, and live evaluations are disabled because this project has no remote tools or production traces.
- Risk is lite: fixtures contain synthetic ticket data; no outbound communication or irreversible action is performed.
- Phase 004 decision (2026-10-26): enable an opt-in live evaluation of one synthetic ticket through the Core supervisor/worker only. Bound provider-estimated exposure to USD 0.01 within the existing USD 2 task ceiling; keep all framework comparisons in fake mode.

## 2026-10-26 — Live Docker acceptance

Use opt-in Groq live mode with numbered credentials and authenticated model preflight. Preserve deterministic fake defaults and fail closed on provider/contract failures. Only local synthetic acceptance and the designated free allowance are authorized; billed cost remains PENDING. Evidence: artifacts/evidence/live-docker/.

## 2026-10-26 — Broad live campaign preparation

Phase 007 prepares a 60-case Core-only dataset (18 development / 42 holdout; 36 English / 24 Portuguese) and offline dry-run. The prior USD 0.01 single-ticket exception does not authorize 720 primary calls, a 240-call fresh confirmation reserve, or framework runner campaigns. Paid spend remains USD 0; quota and cumulative token/request/spend/timing limits remain `PENDING`. Dataset/rubric sign-off remains `PENDING`; generation is disabled. No provider request was made.

## 2026-10-26 — Bounded campaign ledger

Phase 008 adds local SQLite reservations, a process lease, and read-only resume inspection for future P01 campaign execution. This infrastructure does not authorize or enable generation. Paid spend remains USD 0; free-tier quota, cumulative request/token/spend/timing limits, dataset/rubric approval, and campaign approval remain `PENDING`. No provider request was made.
