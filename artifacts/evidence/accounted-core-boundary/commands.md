# Executed commands

Working directory: `C:\estudo\Golpe\lab\projects\p01`. Python code checks use the project lock and framework group.

| Command | Exit | Saved output |
| --- | ---: | --- |
| `uv run --locked --group frameworks python scripts/check_fast.py` (baseline) | 0 | `baseline-fast.txt`: 40 tests |
| `uv run --locked --group frameworks python -m unittest discover -s tests -p test_live_groq_eval.py -v` (new contract, old code) | 1 expected | `red-legacy-boundary.txt` |
| `uv run --locked --group frameworks python -m unittest discover -s tests -p test_accounted_core.py -v` (fixture leak) | 1 | `red-fixture-handles.txt`; corrected with explicit closure |
| Same focused command after correction | 0 | `focused.txt`: 20 tests |
| `uv run --locked --group frameworks python scripts/check_full.py` (final) | 0 | `check-full.txt`: 60 tests, six framework comparisons, demo and package provenance |
| `uv run --locked --group frameworks python artifacts/evidence/accounted-core-boundary/verify_offline.py` | 0 | `offline-network.txt`: six actual frameworks, zero external socket attempts |
| `uv run --locked --group frameworks python artifacts/evidence/accounted-core-boundary/verify_state.py` | 0 | `readiness-dry-run.json` |
| `uv run --locked --group frameworks python scripts/run_live_groq_eval.py --help` | 0 | `legacy-help.txt` |
| Same legacy CLI without flags | 2 expected | `legacy-blocked.json`; no credentials/provider |
| `uv run --locked --group frameworks python scripts/run_live_campaign.py --stage pilot --dry-run` | 0 | `preparation-dry-run.json`; collection disabled |

The existing locked Ruff 0.17.0 executable was used only as a formatting/static-analysis tool, with exit 0; no P00 product source was imported into P01 and no dependency was added. Runtime/framework exact versions are validated against the existing P01 sources lock by the full gate. Root shared encoder inspection runs only in a separate offline contract subprocess and never instantiates a provider session.

Docker `ps` observations are read-only; identity lists match. Phase-owned large fake comparison output is temporary; the saved sanitized probe and standard fake comparison outputs retain its result. Line endings of newly saved command output are normalized to LF before staging. Independent verification and all human/quality approvals remain PENDING.
