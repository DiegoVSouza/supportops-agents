# ADR-003: Separate ticket identity from LangGraph execution identity

- Status: accepted
- Date: 2026-10-15

## Context

The LangGraph adapter used `Ticket.id` as the SQLite checkpoint `thread_id`. Repeating a completed or interrupted ticket could therefore reopen stale run state. A business ticket identifies the support request, while a checkpoint identifies one execution.

## Decision

- Every `run()` without a `resume_key` receives a fresh random checkpoint identity, regardless of the ticket ID.
- A caller may provide a non-empty `resume_key` to `run()` and `resume()`. P01 hashes the ticket ID and key into a deterministic checkpoint identity, allowing a pending run to resume from another runner process.
- `resume()` without a key remains a convenience for the most recent execution in the same runner object. It does not guess a checkpoint from the business ticket ID.
- The shared `TriageRunner` protocol is unchanged; the optional key is a LangGraph-specific extension. Package version advances from 0.1.0 to 0.1.1 to publish the adapter behavior.

## Consequences

Callers that need cross-process recovery must persist and provide the resume key. Ticket IDs remain in the graph state as business data. Fresh-run isolation is deterministic under fake mode and does not claim durable service recovery beyond the existing SQLite checkpoint implementation.
