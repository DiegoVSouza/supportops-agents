# ADR-002: package the dependency-free triage core as a local wheel

- Status: accepted
- Date: 2026-10-15

## Context
P05 needs a separately installable orchestration component. P01 previously had `tool.uv.package = false`, although its `src/supportops_agents` core already exposes a stable `TriageRunner` protocol, SupportOps value types, fake client, and pure Python supervisor implementation. The framework comparison adapters are optional and loaded only when requested. P00's domain package remains a separate dependency and is not available yet.

## Decision
Build `supportops-agents==0.1.0` as a local wheel using the uv build backend. Keep runtime dependencies empty. The wheel exposes P01's existing API without changing public contracts; it is not a substitute for P00. Retain the wheel and provenance locally for P05 installation. Do not publish it.

## Consequences
P05 can install the same immutable wheel in an isolated environment and record its version, source commit, and SHA-256. Framework adapters requiring optional dependencies are not part of the P05 dependency contract. A future public API change requires a versioned release and consumer update.

## Sources
- uv build backend: https://docs.astral.sh/uv/configuration/build-backend/
- uv package configuration: https://docs.astral.sh/uv/concepts/projects/config/
