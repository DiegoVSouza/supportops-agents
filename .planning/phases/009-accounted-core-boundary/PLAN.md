# Plan — accounted Core boundary

## Tasks

1. Specify the guarded Core adapter and transport/payload contracts in offline tests. Freeze source inventory, public protocol v1, finite call/input/output limits, historical reports and the explicit absence of financial/external-effect handlers; record the legacy SDK bypass in failures/ADR.
2. Implement the project-owned subprocess boundary, pure versioned worker prompt/payload, guarded Core client and typed diagnostics. Require an execution manifest before subprocess construction, leave execution disabled, and fail the legacy direct-key/preflight/CLI path before credentials or SDK access.
3. Execute actual Core-loop fixtures and root-encoder parity probes, then locked fast/full checks and six offline framework comparisons. Save sanitized command/exits/output, review staged diff/secrets, update project state/knowledge and commit the implementation separately from planning.

allowed_write_paths:
- `.planning/phases/009-accounted-core-boundary/**`
- `src/supportops_agents/accounted_live.py`
- `src/supportops_agents/live_groq.py`
- `agent/prompts/live-core.md`
- `evals/live-execution.json`
- `scripts/run_live_groq_eval.py`
- `tests/test_accounted_core.py`
- `tests/test_live_groq_eval.py`
- `docs/harness/decisions.md`
- `docs/harness/failures.md`
- `docs/harness/progress.md`
- `docs/adr/ADR-002-accounted-live-boundary.md`
- `docs/knowledge/accounted-core-boundary.md`
- `README.md`
- `README.pt-BR.md`
- `artifacts/evidence/accounted-core-boundary/**`
- `artifacts/evidence/check-fast.txt` and `artifacts/evidence/check-full.txt` (standard gate outputs)
- `artifacts/runs/latest/**` (standard fake comparison outputs)

forbidden_changes: Core control-flow semantics, framework implementations, dataset/splits/rubric/graders/thresholds, existing historical live acceptance/campaign records, logical/provider ledgers or registry, root policy/runtime/kit, credentials, dependencies or package versions, Docker/services, sibling repositories, provider calls, paid use and external effects.

llm_mode: fake/offline only. Provider/credential access: zero. Budget: zero provider calls; USD 0 paid; existing root/project envelopes are read-only. Execution manifest remains disabled. Human and independent review remain PENDING.

Validation commands:
- `uv run --locked --group frameworks python scripts/check_fast.py`
- `uv run --locked --group frameworks python -m unittest discover -s tests -p test_accounted_core.py -v`
- `uv run --locked --group frameworks python scripts/check_full.py`
- Offline root transport encoder parity probe via its documented protocol/source contract; do not instantiate ProviderSession, SharedAccount or any SDK.
- Inspect real CLI `--help` and execute its default fail-closed path with credentials/network denied; save sanitized output and expected nonzero exit.

Stop conditions: no provider process or `.env` read in this phase; any unknown work or missing binding fails closed. Missing framework/service checks remain INCOMPLETE, never hidden by skips. Do not weaken evaluation expectations or transfer historical quality evidence.

Plan-check: implementing-agent review only; independent verification PENDING. Three ordered tasks, concrete paths, immutable evaluation controls, zero-call budget and stop conditions are explicit. Planning is committed before implementation.
