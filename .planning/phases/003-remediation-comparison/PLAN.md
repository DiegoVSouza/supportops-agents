# Plan — Remediation comparison

## Execution controls
- `llm_mode`: `fake`; replay only if a sanitized, traceable cassette is already available.
- `allowed_write_paths`: `.planning/phases/003-remediation-comparison/**`, `src/supportops_agents/**`, `tests/**`, `comparison/**`, `artifacts/runs/**`, `artifacts/evidence/**`, `docs/**`, `README.md`, `README.pt-BR.md`, `pyproject.toml`, `uv.lock`.
- `forbidden_changes`: lab root including `roadmap-ai-engineer.md`, harness kit, sibling projects, unversioned contract changes, weakening/deleting tests, source imports from sibling repositories, paid/live model calls, package publication, push, deploy, or secrets.
- Dependencies: approved local P00 wheel with recorded version, source commit, and SHA-256; pinned P01 framework dependencies; Python and uv from P01 lock/docs.

## Tasks
1. **Execution identity and regression tests** — add tests first for repeated ticket execution with distinct fresh checkpoints, explicit resume-key reuse, and ticket ID remaining business metadata; implement identity separation only as needed to satisfy these tests.
2. **Golden-set adapter comparison** — run all 60 eligible P00 golden cases through each contract-compatible adapter using the installed P00 wheel; record per-case outcomes and explicit unsupported semantics. Distinguish framework-native orchestration from generic worker wrappers in the report.
3. **Reconcile provenance and gate evidence** — identify installed-wheel and local-double paths, verify P00 version/source/hash provenance, run the fake-mode checks, and update comparison/feature/state docs to reflect observed results. Keep real model metrics `PENDING`.

## Checks
- `uv run --locked python scripts/check_fast.py`
- `uv run --locked python scripts/check_full.py` with `LLM_MODE=fake`
- Focused run identity/checkpoint regression tests and shared runner contract tests.
- Comparison command implemented by the project, with its exact invocation and output saved to `artifacts/evidence/` and versioned per-case results under `artifacts/runs/`.
- Verify P00 wheel version/source commit/SHA-256 against the installed consumer artifact; do not rely on sibling source paths.

## Stop condition
Stop a wheel-backed comparison if the approved package artifact or provenance is missing/mismatched; record the gate `INCOMPLETE` and continue only adapter-independent work. If an adapter cannot support a golden-case semantic, report it per case. Stop before any public contract change lacking ADR, version change, and consumer update.

## Plan review
Coordinator review against GSD-LITE-PLUS and P01 remediation criteria: three observable tasks, tests precede identity changes, allowed paths and forbidden actions are explicit, wheel provenance gates integration, and unsupported semantics remain visible. Approved for execution.
