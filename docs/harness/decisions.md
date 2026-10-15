# Intake decisions

- Task and measurable success criterion: PENDING
- Pattern (single-call, workflow, or agent): PENDING
- Runtime rationale: PENDING
- Risk and budget rationale: PENDING
# Intake decisions

## 2026-10-15 — Independent orchestration comparison

- The product implements a deterministic SupportOps ticket triage contract and compares a pure Python runner with optional framework integrations.
- P00's versioned domain package is not yet available. P01 will keep a local contract double under `src/supportops_agents/contracts.py`; package integration is a follow-up gated on an approved P00 artifact and must record its version, source commit, and artifact hash.
- `LLM_MODE=fake` is the default. No provider credentials or paid calls are used. Replay/live remain unavailable until explicitly implemented and authorized.
- AutoGen and Semantic Kernel implementation choice is unresolved pending official documentation and current framework status. No claim of maturity or measured comparison will be made before verification; unavailable framework runners report explicit `INCOMPLETE`.
- Multi-agent manager/children, session state, and tool contracts are enabled because they match the product. MCP, production sampling, and live evaluations are disabled because this project has no remote tools or production traces.
- Risk is lite: fixtures contain synthetic ticket data; no outbound communication or irreversible action is performed.
