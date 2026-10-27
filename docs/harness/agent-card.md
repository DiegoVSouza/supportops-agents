# Agent card — SupportOps triage

- Purpose: classify a synthetic support ticket, gather KB and billing context, and produce an approved response or escalation.
- Unit of work: one `Ticket` instance handled by one `TriageRunner` invocation.
- Verifiable success criterion: return the common `TriageResult` with a matching golden action and stop at approval, escalation, or `max_steps`.
- Pattern: agent, implemented as a supervisor-worker workflow.
- Runtime: custom Python core plus optional pinned framework adapters; `LLM_MODE=fake` is the default. No model is configured for live calls.
- Allowed tools: no model-executable tools. Core workers receive the injected `LLMClient.complete` boundary only; the accounted live client rejects provider tool calls as a terminal failure. No network, filesystem, MCP, or external communication tool is exposed.
- Human approval points: LangGraph pauses before a refund above USD 100; `resume()` continues from its SQLite checkpoint after explicit approval/denial. Each fresh invocation has a unique checkpoint identity; pass a stable `resume_key` to resume across processes. Other runners escalate without executing a refund.
- Limits: Core defaults to four total worker/model calls per workflow and rejects larger step budgets before client invocation. Framework comparison limits remain runner-specific and offline-only; usage and model cost are unknown in fake mode.
- P00 domain package: P00 1.0.1 is installed in an isolated consumer environment to export the 60-case golden fixture. P01 runtime `Ticket` and `TriageDecision` remain local doubles; wheel provenance and the Pydantic/CrewAI environment constraint are recorded in `sources.lock.json`.
