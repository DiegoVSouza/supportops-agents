# Accounted Core boundary — phase 009

Internal offline control gate: **PASS**. Full campaign execution and live readiness: **INCOMPLETE**. Independent/human/dataset/rubric review: **PENDING**.

## Implemented

- The actual Core loop crosses `AccountedCoreClient` with stable campaign/case/trial/call indexes, strict worker order and at most four calls. Early escalation, responder completion, guard/provider/contract failure, timeout and interruption stop and close the workflow. There is no fallback, key rotation, semantic retry or uncertain replay.
- A project-owned UTF-8 subprocess boundary targets the documented root transport v1, fixed to P01. The parent handles no Groq credentials or SDK. Typed allowlisted diagnostics preserve receipts, known usage/latency and unknown usage without raw errors/replies in public results.
- A pure payload builder reads `agent/prompts/live-core.md`, includes only actual state/global contracts and matches transport normalization plus framing under unchanged 2,048/256 caps. Oversized or invalid-UTF-8 state fails before transport; expected/rubric fields are rejected.
- Before any live process, the owner manifest, fixed allocation, frozen source identity, tracked committed project/root inputs, durable reservation and cumulative primary limits must validate. Tests use real fixture Git repositories and SQLite ledgers to prove staged/unstaged/untracked source rejection, root policy dirty-state rejection, unknown reservations across IDs at the 744-call primary boundary and receipt-based uncertain restart denial.
- Legacy SDK/key/catalog helpers and CLI now deny unallocated access before credentials/SDK operations. ADR-002 documents the safety restriction. Historical acceptance and the old rotation baseline are retained; graders, data, thresholds and framework control flow are unchanged.
- The registry enforces offline-only framework scope and disables telemetry before imports. Installed CoreTelemetry recognizes the three configured flags. The actual six-runner comparison passed a Python socket-denial probe with zero external attempts; no unrecorded historical telemetry activity is inferred.

## Evidence and limits

| Gate | Result | Evidence |
| --- | --- | --- |
| Planning | PASS, implementing-agent review | SPEC/PLAN/VERIFY and `plan-check.md`; planning commits precede code |
| Regression | PASS | Focused 20 tests, `focused.txt`, exit 0; final locked full gate 60 tests, `check-full.txt`, exit 0 |
| Framework contract comparison | PASS, fake only | All six runners executed the versioned 60-case installed-wheel fixture; metrics remain PENDING |
| Network/telemetry control | PASS for tested Python socket boundary | `offline-network.txt`, six actual runners, zero external attempts, exit 0; no OS packet-capture claim |
| CLI/owner denial | PASS | `legacy-help.txt`, help exit 0; `legacy-blocked.json`, expected exit 2; disabled owner and absent allocations reject before child/keys |
| Offline capacity inventory | PASS | `verify_state.py` / `readiness-dry-run.json`, exit 0; P01 registration/ledger absent and zero P01 calls; account guard still records sixteen P00 attempts |
| Docker identity preservation | PASS | Before/after container identity files match; no stack operation occurred |
| Full durable campaign / actual tools | INCOMPLETE | Dispatcher, final candidate freeze and owned allocation not created. Core has no external/financial-effect tool executor; contexts do not establish actual retrieval or financial operation |
| Live quality, reviews, holdout, promotion | INCOMPLETE/PENDING | No provider trial or promotion occurred |

P01 retains 984 calls: 744 primary and protected confirmation 240, with original per-call limits. No correction/judge/canary allocation is created. Later batching must cap **provider attempts**, not just logical trials; this dry-run plans two complete four-call workflows per batch (at most eight provider attempts) while preserving all original cases/trials. Paid allowance is USD 0; actual billing and current provider quota are unknown.

The new Git/SQLite fixtures initially leaked SQLite handles during Windows cleanup; explicit closure fixed the test resource lifecycle. `red-fixture-handles.txt` preserves that failure. `red-legacy-boundary.txt` preserves the red authorization regression before implementation. Fixture commits, receipts and usage are not real campaign results or account calls.

## Safe next step

`uv run --locked python scripts/run_live_campaign.py --stage pilot --dry-run`

No live/resume command is valid from phase 009. Keep `evals/live-execution.json` disabled and its approved campaign/allocation collections empty until an owning dispatch phase is fully specified, implemented, validated and committed. A Docker bridge is neither created nor assumed.
