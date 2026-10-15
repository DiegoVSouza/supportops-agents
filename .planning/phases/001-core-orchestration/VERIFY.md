# Phase 001 verification

## Unit
- `uv run --group frameworks python scripts/check_fast.py` — compilation and unit/shared-contract tests for core and all five framework adapters.

## Integration
- `uv run --group frameworks python -m supportops_agents.comparison --output artifacts/runs/latest` — execute all six runners against the same synthetic golden cases; the gate fails if any required adapter is unavailable or mismatches expected outcomes.

## E2E
- `uv run --group frameworks python -m supportops_agents.demo` — user-visible synthetic ticket triage, fake mode only.

## Product evaluation
- Comparison output reports model-quality metrics as `PENDING` until collected from genuine, traceable runs. Unit tests and fake-mode runs do not count as agent-quality evaluation.

## Gate
- `uv run --group frameworks python scripts/check_fast.py` and `uv run --group frameworks python scripts/check_full.py`; save exact command, exit status, and combined output in `artifacts/evidence/` before each commit.
- `check_full.py` exits `2` and reports `INCOMPLETE` if any required framework adapter is absent; a green core smoke does not approve the six-runner product.
