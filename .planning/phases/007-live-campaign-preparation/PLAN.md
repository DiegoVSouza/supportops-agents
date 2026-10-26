# Plan — Live campaign preparation

## Execution controls

- `llm_mode`: `fake`; preparation and dry-run require no credentials or provider access.
- `allowed_write_paths`:
  - `.planning/phases/007-live-campaign-preparation/**`
  - `evals/datasets/live-v1/**`
  - `evals/rubrics/live-v1/**`
  - `evals/live-campaign.json`
  - `scripts/run_live_campaign.py`
  - `tests/test_live_campaign_preparation.py`
  - `docs/harness/decisions.md`
  - `artifacts/evidence/live-campaign-preparation/**`
- `forbidden_changes`: runner/runtime/prompts, framework adapters, other repositories, harness-kit, root `.env`, secrets, prior live evidence, provider calls, Docker mutation, paid usage, external effects, push, or relaxed quality thresholds.
- Budget source: profile ceiling is USD 2 per task; the existing live exception authorizes a single bounded Core case at USD 0.01 estimated exposure. The expanded campaign, any fresh confirmation set, and any additional live runner have no approved reservation and stay `PENDING`. Four keys are not four quotas.
- Planned load to display, not authorization: pilot is 6 development cases × 1 trial × at most 4 calls = 24 calls; full Core campaign is 60 cases × 3 trials × at most 4 calls = 720 calls before retries/confirmation. Unknown token/spend ceilings block generation.
- Validation: P01 fast/full fake checks; dataset uniqueness/split/family/language tests; deliberately invalid grader outputs; dry-run and blocked-generation safety tests. Store command, exit code, and sanitized output under the evidence path.
- Stop condition: no live run until all finite caps, quota/cost reservation, confirmation capacity, dataset/rubric review, and model preflight are evidenced. Missing prerequisites mean `INCOMPLETE`.

## Tasks

1. **Freeze the Core dataset and rubrics for review** — inspect versioned orchestration contracts and prior failure taxonomy; author 60 unique synthetic cases in 18/42 development/holdout splits with required families and 36/24 language coverage. Keep related scenarios in one split, record public/synthetic hashes, and leave sign-off `PENDING` until an independent reviewer approves expected outcomes and rubric.
2. **Implement a guarded dry-run and reservation config** — expose validated help/stages, summarize case/trial/call limits and unresolved budget fields without constructing the SDK or reading credentials. The generation path must stop before dispatch while any required approval or limit is `PENDING`; other framework runners remain explicitly offline-only in this phase.
3. **Prove preparation and grader behavior** — test duplicate/split isolation, family/language coverage, deliberate bad routing/tool/evidence/termination outputs, dry-run isolation, and fail-closed generation. Run fake-mode project gates, save evidence, and review the staged diff.

## Plan review

Coordinator review completed against the portfolio readiness spec, P01 decisions, and current Core/runner scope. The 18/42 case split, 36/24 language split, and 24-call pilot / 720-call Core ceilings are consistent. The selected paths are local to this preparation phase, expanded spend and quota remain blocked, and framework runners are not implicitly promoted. Accepted for preparation execution on 2026-10-26. A clean-context verifier is still required for the finished phase gates.
