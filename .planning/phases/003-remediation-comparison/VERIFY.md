# Verify — Remediation comparison

For every executed check, save the exact command, exit code, and output in `artifacts/evidence/`.

- [ ] Repeated ticket with no resume key starts an isolated execution and does not reuse an old checkpoint.
- [ ] Explicit resume key resumes the intended execution; ticket identity is preserved as business data.
- [ ] Shared fake-mode runner contract tests pass for supported adapters.
- [ ] Versioned P00 golden set is exercised across all eligible adapters; results include per-case outcomes and unsupported semantics.
- [ ] Report distinguishes framework-native orchestration from generic wrappers across fan-out, retries, checkpoints, HITL, state, and observability.
- [ ] Installed P00 wheel version, source commit, and SHA-256 are recorded; local doubles are labeled and their consumer paths are explicit.
- [ ] Full fake-mode gate result is recorded with actual exit code; any missing required gate is `INCOMPLETE`.
- [ ] Accuracy, tokens, cost, latency, and model evaluation remain `PENDING` absent comparable authorized real-model runs.
- [ ] Any public contract change has an ADR, package version change, and consumer update.
