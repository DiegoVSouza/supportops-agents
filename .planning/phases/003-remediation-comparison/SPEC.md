# Phase 003 — Remediation comparison

## Goal
Make P01 comparison runs isolate each execution from business ticket identity, test repeated runs for stale checkpoint reuse, and compare eligible framework adapters over the versioned P00 60-case golden set with candid descriptions of their execution semantics.

## Acceptance criteria
- Ticket identity remains business data. Every fresh run/checkpoint gets an execution identity; state is reused only with an explicit resume key. Repeating a ticket without that key does not inherit prior state; explicit resume does.
- The same versioned P00 golden cases are run against each adapter whose contract supports them, with per-case result/status and unsupported semantics recorded. No synthetic three-case smoke is described as representative.
- The comparison documents each adapter's native orchestration versus generic wrapper behavior for fan-out, retries, checkpoints, HITL, state, and observability.
- Fake-only accuracy/token/cost/latency claims are not presented as representative model benchmarks; real model metrics remain `PENDING`.
- Consumer paths identify installed local wheels versus local test doubles precisely, including package version/source commit/SHA-256 where wheels are consumed.
- Every executed check records command, exit code, and output under `artifacts/evidence/`.

## Scope and contract
Keep the public `TriageRunner` contract compatible unless a required change is documented in an ADR, receives a package version change, and is reconciled by consumers. Use installed versioned P00 artifacts for package integration; never import a sibling repository by relative path.

## Dependencies
- P00 approved local wheel and its version/source/hash provenance.
- P01 pinned framework environment and existing runner contract tests.
- The complete 60-case P00 golden set is available through the installed P00 package. Framework-specific limitations must be reported rather than silently omitting cases.
- Fake mode only; no live calls or external services are required.
