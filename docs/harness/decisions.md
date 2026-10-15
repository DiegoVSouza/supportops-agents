# Intake decisions

## 2026-10-15 — Independent orchestration comparison

- The product implements deterministic SupportOps ticket triage and compares the pure Python runner with five executable framework integrations.
- P00's versioned domain package is not available. P01 keeps a local contract double in `src/supportops_agents/contracts.py`; replacing it requires an approved P00 package with version, source commit, and artifact hash.
- `LLM_MODE=fake` is the default. No provider credentials or paid calls are used. Replay/live remain unavailable until implemented and authorized.
- ADR-001 selects classic AutoGen and Semantic Kernel APIs to preserve the historical comparison targets. Microsoft Agent Framework 1.0 is their documented successor and is not silently substituted. Exact versions are pinned in `uv.lock`; adapters have executable contract coverage.
- Multi-agent manager/children, session state, and tool contracts are enabled because they match the product. MCP, production sampling, and live evaluations are disabled because this project has no remote tools or production traces.
- Risk is lite: fixtures contain synthetic ticket data; no outbound communication or irreversible action is performed.
