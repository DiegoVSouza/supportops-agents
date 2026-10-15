# ADR-001: Preserve named framework identities in the comparison

- Status: accepted for this comparison; implementation pending dependency verification.
- Date: 2026-10-15

## Context

The archived P01 brief names AutoGen and Semantic Kernel as separate comparison targets. Current Microsoft documentation identifies Microsoft Agent Framework as their successor and provides migration guides. Replacing either runner with the successor without changing the comparison name would make the results misleading.

## Decision

Keep `autogen` and `semantic_kernel` as distinct adapter identities and target their classic public APIs for this archived comparison. Record the exact package versions and commits when resolved. Do not claim the classic projects are the current investment focus. Microsoft Agent Framework may be added only as a separately named runner in a separately versioned scope change.

## Consequences

- Current public API and package versions must be resolved from official docs/package metadata before adapters are implemented.
- No local simulation may stand in for a framework adapter. An unavailable adapter is reported `INCOMPLETE`.
- Consumers keep the stable runner names; this ADR does not change the public contract.

## Sources checked 2026-10-15

- [Microsoft Agent Framework 1.0 announcement](https://devblogs.microsoft.com/agent-framework/microsoft-agent-framework-version-1-0/)
- [AutoGen migration guide](https://learn.microsoft.com/agent-framework/migration-guide/from-autogen)
- [Semantic Kernel migration guide](https://learn.microsoft.com/agent-framework/migration-guide/from-semantic-kernel)
