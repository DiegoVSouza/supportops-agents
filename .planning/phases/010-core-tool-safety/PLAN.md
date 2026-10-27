# Plan — Core tool safety and execution limits

## Tasks

1. Add regressions for the four-call ceiling in the actual Core loop and terminal rejection of model tool calls through the accounted client; preserve current evaluator contracts and historical artifacts.
2. Enforce `max_steps <= 4` before any client call and ensure no tool call or duplicate is executable in the live boundary. Keep all frameworks/fake behavior otherwise unchanged.
3. Run locked focused/fast/full checks, save command/exit/output, record the real-tool source limitation and concrete proposal, inspect/stage only owned paths, update status/knowledge, and commit atomically.

allowed_write_paths:
- `.planning/phases/010-core-tool-safety/**`
- `src/supportops_agents/core.py`
- `tests/test_core.py`
- `tests/test_accounted_core.py`
- `docs/harness/progress.md`
- `docs/harness/failures.md`
- `docs/harness/security.md`
- `docs/harness/agent-card.md`
- `docs/knowledge/core-tool-safety.md`
- `artifacts/evidence/core-tool-safety/**`

forbidden_changes: dataset/cases/splits, expected labels, required facts, rubric, graders, thresholds, framework adapters, prompts, campaign configs/allocations, ledgers/registry, credentials, provider calls, Docker/services, customer data, external or financial effects, sibling projects, shared kit/policies, dependency locks and pre-existing working-tree changes.

llm_mode: fake/offline only. Provider calls: zero. Paid authorization: USD 0. Campaign manifest stays disabled. Do not run or modify live campaign ledgers.

Validation commands:
- `uv run --locked --group frameworks python -m unittest discover -s tests -p test_core.py -v`
- `uv run --locked --group frameworks python -m unittest discover -s tests -p test_accounted_core.py -v`
- `uv run --locked --group frameworks python scripts/check_fast.py`
- `uv run --locked --group frameworks python scripts/check_full.py`
- inspect CLI help only; do not invoke live preflight or dispatch.

Stop conditions: unexpected provider/credential/network access; any edit to pre-existing artifact outputs; any change to frozen evaluation files; a tool path that can write, contact users, or perform billing; or a failing regression without a root-cause fix. Real knowledge/billing integration stays INCOMPLETE because no approved source or service contract exists. Do not fill this gap with dataset labels or fixtures presented as live retrieval.
