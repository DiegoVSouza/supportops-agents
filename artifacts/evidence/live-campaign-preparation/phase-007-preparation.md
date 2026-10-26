# P01 Phase 007 — Campaign preparation evidence

## Offline checks

| Command | Exit | Result |
|---|---:|---|
| `uv run --locked python scripts/run_live_campaign.py --help` | 0 | CLI exposes `pilot`, `development`, `holdout`, config, and dry-run. |
| `uv run --locked python -m unittest discover -s tests -p test_live_campaign_preparation.py -v` | 0 | 7 focused tests passed. |
| `uv run --locked python scripts/check_fast.py` | 0 | Compile and all 33 unittest cases passed. First invocation returned a running session without final output; the successful rerun captured exit 0. |
| `uv run --locked python scripts/check_full.py` | 0 | Fast/compile/unit checks, 33 tests, all six offline comparison runners, demo, comparison JSON, and source-lock checks passed. |

## Dry-run reservation

Dry-run commands for `pilot`, `development`, and `holdout` all exited 0. They reported 6 pilot cases / 24 calls; 18 development cases / 54 trials / 216 calls; 42 holdout cases / 126 trials / 504 calls. The primary campaign maximum is 720 calls, with a 240-call, 20-case fresh confirmation reserve; additive total including the separate pilot is 984 calls.

Per-case ceilings are four provider calls, 8,192 input tokens and 1,024 output tokens across the task (256 output tokens per call). Primary campaign token maxima are 1,474,560 input and 184,320 output. Confirmation maxima are 491,520 input and 61,440 output; all stages additive including pilot are 2,015,232 input and 251,904 output tokens. These are planned maxima, not approved or consumed quota.

Dataset SHA-256: `6884c47eb34ae46b1c1a8aa94735bec871315a1ad60aaffb39dace4cf7b1259f`. All dry-runs reported `generation_authorized=false`, `provider_accessed=false`, `credentials_read=false`, and `docker_mutated=false`. The Core runner is the only live-scoped runner; five framework adapters remain explicitly offline-only.

## Remaining gates

The existing one-ticket USD 0.01 exception does not authorize the broad campaign. Paid ceiling remains USD 0; free-tier quota, cumulative spend/token/request caps, timing/pacing, retry policy, and confirmation funding are `PENDING`. Dataset/rubric review provenance and the durable lease/ledger are also `PENDING`. No provider request was made, and fake comparison metrics are not live model quality evidence.
