# Phase 001 plan

## Ownership
- `allowed_write_paths`: `projects/p01/**` (in this independent repository, all paths are relative to its root).
- `forbidden_changes`: lab root, `harness-kit/**`, and all sibling projects.
- `llm_mode`: fake.
- Contract: local doubles match the archived P01 Ticket/TriageDecision and `TriageRunner` result shape; do not silently change public fields. Any incompatibility requires ADR, version bump, and consumer update.
- Dependency policy: prefer stdlib for core. Pin any framework/test dependency in a lockfile only after checking current official docs; record source and version in `docs/harness/sources.lock.json`.
- Stop condition: stop framework-specific work if official API/version or contract cannot be verified; record `INCOMPLETE` and continue independent core work.

## Tasks
1. **Core contract and test-first behavior** — add local domain/LLM doubles, runner protocol/results, deterministic agents, and behavior tests for approval, escalation, errors, and limit boundaries.
2. **Framework boundary and genuine check** — implement `get_runner`, explicit optional dependency adapters, and a full check that executes real tests/contract checks; record unavailable adapters without pretending they ran.
3. **Comparison and project docs** — provide golden set and honest pending comparison report, English/Portuguese READMEs, architecture diagrams, and Portuguese knowledge guide with EN/PT interview answers.

## Plan review
Reviewed before product code: tasks are observable, cover core acceptance criteria, and remain within this project's exclusive write ownership. Framework API research is a gate for framework integration, not an excuse to report simulated results as real.
