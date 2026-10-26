# Phase 008 — P01 bounded campaign ledger

Status: `INCOMPLETE` for live adoption. Offline ledger and resume primitives passed; provider dispatch and promotion gates remain pending.

## Evidence

| Command | Exit | Result |
|---|---:|---|
| `uv run --locked python -m unittest discover -s tests -p test_campaign_ledger.py -v` | 0 | 6 ledger tests passed, including process lease and concurrent cumulative cap enforcement. |
| `uv run --locked python scripts/check_fast.py` | 0 | Compile and all 40 unittest checks passed. |
| `uv run --locked python scripts/check_full.py` | 0 | Full fake comparison and demo gate passed; all six runner identities are present, with live metrics remaining PENDING. |
| `uv run --locked python -S scripts/run_live_campaign.py --help` | 0 | Help exposes stage and read-only resume commands. |
| `uv run --locked python -S scripts/run_live_campaign.py --stage pilot --dry-run` | 0 | Offline reservation summary; provider, credentials, and Docker untouched. |
| `uv run --locked python -S scripts/run_live_campaign.py --stage pilot` | 2 | Generation blocked because approval, quota, and cumulative limits remain pending. |

Detailed command output is stored beside this report. The temporary outputs written by the repository's existing check scripts to `artifacts/evidence/check-fast.txt`, `artifacts/evidence/check-full.txt`, and `artifacts/runs/latest/results.json` were restored after capture so historical evidence stayed unchanged.

## Remaining gates

- Groq preflight and dispatch, crash-after-dispatch recovery, and lease integration into an authorized execution path.
- Independent dataset/rubric review, finite approved free quota and cumulative request/token/cost/time ceilings, and confirmation reserve.
- Cross-project ledger/lease and quota accounting, which this project-local phase does not claim.
- Independent clean-context review. No provider call was made in this phase.
