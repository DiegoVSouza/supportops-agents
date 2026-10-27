# Phase 010 command record

All product checks used fake/offline mode. No credentials, provider, network, Docker, or external-effect path was used.

| Command | Exit | Result |
| --- | ---: | --- |
| `uv run --locked --group frameworks python -m unittest discover -s tests -p test_core.py -v` (before implementation) | 1 expected | `red-limit.txt`: budgets 5/6/12/100 reached the client before the four-call cap existed. |
| Same focused Core command (after implementation) | 0 | 9 passed; `core-tests.txt`. |
| `uv run --locked --group frameworks python -m unittest discover -s tests -p test_accounted_core.py -v` | 0 | 21 passed; `accounted-core-tests.txt`. |
| `uv run --locked --group frameworks python scripts/check_fast.py` (initial red gate) | 1 expected | `initial-gate-failure.md`: two comparison callers passed 12 to the Core-specific limit. |
| `uv run --locked --group frameworks python scripts/check_fast.py` (final) | 0 | 62 tests; `fast-gate.txt`. |
| `uv run --locked --group frameworks python scripts/check_full.py` (final) | 0 | 62 tests, six runners × 60 golden cases, comparison and demo; metrics PENDING; `full-gate.txt`. |
| `uv run --locked --group frameworks python scripts/run_live_campaign.py --help` | 0 | CLI contract inspected; `cli-help.txt`. No dispatch occurred. |
| `uv run --locked --group frameworks python -m ruff check src/supportops_agents/core.py` | 1 | Ruff is not present in the locked frameworks group; no dependency was added. See `ruff-locked-unavailable.txt`. |
| Global `python -m ruff check src/supportops_agents/core.py src/supportops_agents/comparison.py tests/test_core.py tests/test_accounted_core.py tests/test_comparison.py tests/test_runner_contract.py` (Ruff 0.15.21) | 0 | `ruff-check.txt`; supplemental only, not a locked-project gate. |
| Global `python -m ruff format --check src/supportops_agents/core.py src/supportops_agents/comparison.py tests/test_core.py tests/test_accounted_core.py tests/test_comparison.py tests/test_runner_contract.py` (Ruff 0.15.21) | 1 | Requests whole-file formatting. The committed Core baseline also fails Ruff format check; no broad rewrite was applied. See `ruff-format.txt`. |

The full-gate runner overwrites three standard project artifacts. Their exact pre-run bytes were restored; before/after SHA-256 values match in `preservation.json`. `artifacts/runs/latest/COMPARISON.md` was clean before the run and was restored after copying the generated comparison into this phase evidence. Fake-run timing/control results are not live quality evidence.
