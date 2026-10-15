# P01 phase state

- Phase 001 — core orchestration: complete.
- Phase 002 — local package: complete.
- Phase 003 — remediation comparison: complete for local acceptance; SDD artifacts are committed.
- Run/checkpoint identity: implemented and verified for repeated same-ticket execution and explicit-key cross-process resume.
- Local checks: fake-mode full gate passed with 20 tests, six adapter identities, all 60 P00 golden cases, and offline demo; evidence is in `artifacts/evidence/check-full.txt`.
- Required P00 golden comparison: PASS for the eligible P01 action/category contract; each case labels unsupported P00 fields/actions.
- LLM mode: fake. Model quality, tokens, cost, latency, and formal evaluation remain `PENDING`.
- P00 golden fixture consumer: installed P00 1.0.1 wheel in an isolated environment; source commit and SHA-256 are in `docs/harness/sources.lock.json`. P01 runtime contracts remain local doubles because P00 and CrewAI Pydantic constraints conflict in one environment.
- P01 package API extension: ADR-003 documents the LangGraph-specific `resume_key`; package version is 0.1.1. Local wheel build/consumer smoke is a separate pending artifact task.
