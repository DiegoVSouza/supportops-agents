# Phase 001 verification

## Unit
- `python -m unittest discover -s tests -v` — core decisions, stop conditions, malformed inputs, fake continuation limit.

## Integration
- `python -m supportops_agents.comparison --output artifacts/runs/latest` — all installed runners on identical synthetic golden cases; optional unavailable frameworks marked `INCOMPLETE`.

## E2E
- `python -m supportops_agents.demo` — user-visible synthetic ticket triage, fake mode only.

## Product evaluation
- `python -m supportops_agents.comparison` output reports framework/model metrics as `PENDING` until collected from genuine, traceable runs. Unit tests do not count as agent-quality evaluation.

## Gate
- `python scripts/check_fast.py` and `python scripts/check_full.py`; save exact command, exit status, and combined output in `artifacts/evidence/` before each commit.
