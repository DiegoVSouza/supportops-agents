# Plan

1. Inspect current source/contract and missing-source evidence; verify parent transport deadlines and disabled execution manifest.
2. Run locked fake fast/full gates with exact restoration of pre-existing standard outputs; record hashes and exit codes.

allowed_write_paths: `.planning/phases/015-transport-regression/**`, `artifacts/evidence/transport-regression-015/**`. Standard outputs `artifacts/evidence/check-fast.txt`, `artifacts/evidence/check-full.txt`, `artifacts/runs/latest/results.json`, `artifacts/runs/latest/COMPARISON.md` may be overwritten only temporarily and restored byte-for-byte. Initial inspection showed COMPARISON.md clean; restore its generated one-line LOC change from the tracked initial version. Preserve the three initially modified files exactly.
forbidden_changes: product source, source integrations, ledgers, providers, credentials, budgets, historical evidence, external services, Docker, sibling sources and human approvals.

LLM_MODE=fake; USD 0; zero provider calls. max_tries: 3 per failure persisted in evidence. Plan-check is implementer self-assessment. Stop affected work on external prerequisite or exhausted corrections and continue independent work.
