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

## 2026-10-27 — Accounted Core boundary

The user authorizes controlled synthetic free-only evaluation under the root policy; paid allowance remains USD 0 and deferred human review is not approval. Phase 009 implements the Core boundary offline, while the owner manifest remains disabled and campaign allocation/freeze/dispatch are incomplete. P01's unchanged finite envelope is 984 calls: 744 primary and protected confirmation 240; no corrections, judges or canary are funded automatically.

ADR-002 requires the actual Core worker loop to use the accounted adapter and disables legacy direct SDK/key/catalog paths before credential access. Worker input contains only actual state and global contracts; rubric/expected data never enter prompts. Root subprocess protocol v1 owns credentials/receipts; P01 imports no sibling product source. Framework registry access is fake/replay only and disables installed telemetry before imports. Full campaign execution and real external tools remain separate work; no provider or Docker mutation occurred in phase 009.
