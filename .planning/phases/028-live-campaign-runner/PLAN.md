# Plan

1. Write `tests/test_campaign_observe.py` and `tests/test_campaign_execution.py` first; run them red and save the output.
2. `scripts/campaign_observe.py`: term groups, forbidden patterns, content-free observation, grader.
3. `scripts/campaign_execution.py`: ordered cases and pilot, manifest in the `SubprocessGuard` format plus a source fingerprint, trial runner (live `SubprocessGuard`, fixture oracle transport), resumable executor with logical ledger and root usage proof, report.
4. `scripts/run_live_campaign.py`: `--freeze`, `--execute-free`, `--execute-fixture`, `--max-trials`, `--output-dir`; `evals/live-execution.json`: approve `p01-dev-v1` with one development allocation of the 18 ordered case ids.
5. Full fake gate, commit the candidate, freeze the manifest, catalog preflight, pilot, review, development run, report, labels, catalog.

allowed_write_paths: `scripts/campaign_observe.py`, `scripts/campaign_execution.py`, `scripts/run_live_campaign.py`, `tests/test_campaign_*.py`, `evals/live-execution.json`, `artifacts/evals/live/p01-dev-v1/**`, `artifacts/evidence/live-campaign-runner/**`, `.planning/phases/028-live-campaign-runner/**`, `docs/harness/**`, `README.md`, `README.pt-BR.md`.
forbidden_changes: `src/supportops_agents/**` (the accounted boundary is the frozen candidate), the dataset, rubric and prompt, other projects, credentials, holdout and confirmation reserves, the existing operation allocations.
Budget: at most 72 provider calls (18 trials x 4). max_tries: 3 per component; no tuning after the pilot.
