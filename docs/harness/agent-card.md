# Agent card — SupportOps triage

- Purpose: classify a synthetic support ticket, gather KB and billing context, and produce an approved response or escalation.
- Unit of work: one `Ticket` instance handled by one `TriageRunner` invocation.
- Verifiable success criterion: return the common `TriageResult` with a matching golden action and stop at approval, escalation, or `max_steps`.
- Pattern: agent, implemented as a supervisor-worker workflow.
- Runtime: custom Python core plus optional pinned framework adapters; `LLM_MODE=fake` is the default. No model is configured for live calls.
- Allowed tools: injected `LLMClient.complete` only. No network, filesystem, MCP, or external communication tools are exposed to workers.
- Human approval points: LangGraph pauses before a refund above USD 100; `resume()` continues from its SQLite checkpoint after explicit approval/denial. Other runners escalate without executing a refund.
- Limits: default `max_steps=12`; LangGraph node retries are limited to transient timeout/connection errors; usage and model cost are unknown in fake mode.
- P00 domain package: pending approval/versioned artifact; this project currently uses local compatibility contracts.
