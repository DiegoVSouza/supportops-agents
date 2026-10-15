# Phase 001 — Core orchestration

## Goal
Implement a reproducible SupportOps triage example and a common `TriageRunner` contract. The project remains independent; its local `Ticket`, `TriageDecision`, and `LLMClient` doubles are temporary compatibility contracts pending an approved, versioned P00 package.

## Acceptance criteria
- Pure Python supervisor-worker runner invokes classifier, KB researcher, billing agent, and responder through a shared typed state.
- Runner stops deterministically at the configured step limit, on an approved response, or on escalation, including a fake that continually requests another step.
- Public runner lookup has stable names for core and five framework adapters; unavailable dependencies fail with an explicit actionable error rather than silently impersonating a framework.
- Golden synthetic cases exercise normal response, escalation, and step-boundary behavior in fake mode.
- Comparison output distinguishes measured values from `PENDING`; no fake numbers are presented as model quality, latency, tokens, or cost.
- README in English and Brazilian Portuguese documents architectures, execution, comparison limitations; knowledge doc explains orchestration patterns and failure modes.
- Every check stores command, exit code, and output under `artifacts/evidence/`; full check performs real contract and test checks.

## Out of scope
HTTP/auth, production observability, queueing, paid LLM calls, publishing packages, and claims of real framework performance. Framework-specific integrations are implemented only where installed dependencies and current official APIs can be verified.
