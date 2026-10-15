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
- ADR-001 selects the classic AutoGen and Semantic Kernel APIs for the named historical-framework comparison. Microsoft documents Microsoft Agent Framework 1.0 as their successor; it is not silently substituted into these comparison slots. The current package versions and executable adapters remain `PENDING` until dependency resolution and contract validation.
- Multi-agent manager/children, session state, and tool contracts are enabled because they match the product. MCP, production sampling, and live evaluations are disabled because this project has no remote tools or production traces.
- Risk is lite: fixtures contain synthetic ticket data; no outbound communication or irreversible action is performed.
