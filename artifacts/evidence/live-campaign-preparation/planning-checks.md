# Live campaign preparation — planning checks

No provider calls or Docker mutations were made.

| Command | Exit | Observed result |
|---|---:|---|
| `uv run --locked python scripts/check_fast.py` | 0 | Compile and all 26 unittest cases passed. |
| `uv run --locked python scripts/check_full.py` | 0 | Fast check, compile, all 26 tests, six-runner offline comparison, demo, and comparison/source-lock checks passed. |

The first full-check invocation returned a running session without its final output being captured; a rerun completed with exit 0 and the output above. The check scripts rewrote tracked generic evidence and `artifacts/runs/latest/results.json`; those three paths were restored to their clean initial contents. No unrelated changes were present at the start. These are offline framework results, not live model quality evidence.
