# Initial locked gate failure after Core cap change

COMMAND: `uv run --locked --group frameworks python scripts/check_fast.py`
EXIT_CODE: 1

The red run showed two existing Core callers still requested `max_steps=12`: `tests/test_comparison.py` through `src/supportops_agents/comparison.py`, and `tests/test_runner_contract.py`. Both raised the new Core four-call ceiling before their assertions. The plan was amended to pass `max_steps=4` only to Core in the fake comparison/shared contract harness. Framework adapters and golden data were left unchanged. The final fast and full locked gates pass; see `fast-gate.txt` and `full-gate.txt`.
