# Progress

- Intake and phase 001 artifacts created before product code.
- Core supervisor-worker and local domain contract doubles implemented; fake-mode contract tests cover all six runners for approval, escalation, and step termination.
- Git audit evidence: `artifacts/evidence/git-setup.md`.
- The `frameworks` dependency group is pinned by `uv.lock`; exact versions are recorded in `docs/harness/sources.lock.json`.
- LangGraph implements parallel KB/billing, per-node retries, SQLite checkpoints, and resumable HITL for refunds above the configured threshold.
- CrewAI, AutoGen classic, Semantic Kernel classic, and LlamaIndex adapters are implemented and pass the shared synthetic golden set.
- Full gate at prior state passed: 19 tests, six runners, three local cases, comparison report, and offline demo. That smoke did not establish P00 golden coverage.

## 2026-10-15 — Phase 003 run/checkpoint identity

- LangGraph now assigns a unique checkpoint thread ID to every fresh invocation, even when the business ticket ID repeats.
- A caller-provided `resume_key` maps to a stable ticket-scoped checkpoint identity and enables resume from another runner process. In-process resume without a key targets only that runner's latest execution.
- Regression evidence first reproduced stale interrupt reuse and unsupported cross-process `resume_key`; the fixed focused test run and full fake gate are saved in `artifacts/evidence/check-fast.txt` and `artifacts/evidence/check-full.txt`.
- P00 package 1.0.1 was installed in an isolated consumer environment and exported the versioned 60-case fixture. Source commit and wheel SHA-256 are recorded in `docs/harness/sources.lock.json`.
- The isolated wheel export avoids a dependency conflict in the shared runtime environment: P00 pins Pydantic 2.14.1, while the locked CrewAI 1.15.28 requires Pydantic below 2.13. P01 runtime continues to use its local domain doubles; only the comparison fixture comes from P00's installed package.
- All six adapters executed all 60 cases in fake mode. Unsupported P00 decision fields and answer/request-info distinctions are recorded per case. Full-gate output is in `artifacts/evidence/check-full.txt`.
- Accuracy, tokens, cost, latency, and formal evaluation remain `PENDING`; fake-run step counts are control-flow observations only.

## 2026-10-26 — Phase 004 live Core evaluation

- Added optional Groq 1.7.0 support for the Core runner only. Four numbered credentials are preflighted; the client caps each of four serial calls at 256 tokens and total estimated exposure at USD 0.01. Fake mode remains the default and imports no SDK unless live is used.
- The real model first returned a JSON-mode validation error; local JSON parsing fixed the provider error. Initial real cases over-escalated routine questions; adding a general escalation threshold fixed the issue. Offline tests also found and fixed exception text leaking before the sanitization boundary.
- Final four-key live run passed: 4 steps in order, 1470 input / 655 output tokens, estimated cost USD 0.00030675. Full fake comparison gate passed across six runners.

## 2026-10-26 — Live evaluation readability cleanup

- Use a normal Path import, initialize optional client state explicitly, extract retry and artifact helpers, and replace nested mock factories with ordinary Mock instances.
- Full offline gate: PASS (26 tests and all six fake runner comparisons).
- Offline helper and static checks passed; no live calls were needed. Evidence: artifacts/evidence/code-cleanup/.

## 2026-10-26 — Live Docker acceptance

One real Core workflow passed all domain assertions with four serial calls (1470 input / 588 output tokens). The deterministic full comparison passed for all six installed runners; live acceptance covers Core only. Evidence: artifacts/evidence/live-docker/.

## 2026-10-26 — Phase 007 campaign preparation

- Added 60 synthetic Core orchestration cases with a fixed 18/42 development/holdout split, 36/24 English/Portuguese coverage, and seven required families. Dataset SHA-256: `6884c47eb34ae46b1c1a8aa94735bec871315a1ad60aaffb39dace4cf7b1259f`.
- Added code-first decision/route/order/termination grader tests and an offline dry-run. It reports pilot 24 calls, primary campaign 720, confirmation reserve 240, and 984 calls if all stages are additive; no provider, credential, or Docker access occurs.
- Campaign preparation tests: 7 passed. Fast/full gates passed with 33 tests; six framework comparisons and demo remain fake/offline. Evidence: `artifacts/evidence/live-campaign-preparation/phase-007-preparation.md`.
- Dataset/rubric review, expanded quota/spend/token/timing caps, durable lease/ledger and live runtime acceptance remain `PENDING`/`INCOMPLETE`. No Groq calls were made.
## 2026-10-26 — Phase 008 bounded campaign ledger

- Added an append-only SQLite reservation ledger, cumulative cap enforcement, cross-process OS lease, and read-only resume inspection for P01. Unknown usage retains the full original reservation; uncertain/completed trials cannot be rerun.
- Focused ledger tests: 6 passed. Fast/full fake gates passed with 40 tests and all six offline runner identities. `-S` dry-run exited 0; generation exited 2 while prerequisites remain pending. No Groq request or Docker mutation occurred.
- Groq dispatch, approved campaign limits/reviews, crash-after-dispatch recovery, lease integration, and cross-project accounting remain incomplete. Phase status: `INCOMPLETE`; evidence: `artifacts/evidence/live-campaign-ledger/`.
## 2026-10-27 — Phase 009 accounted Core boundary

- Added a project-owned single-attempt adapter at the actual Core worker loop, a pure versioned prompt/payload builder and root transport v1 framing/UTF-8 boundary. Four indexed calls, early escalation, worker order, typed diagnostics, complete 2,048/256 bounds, shutdown and no uncertain/semantic replay have deterministic coverage. The direct SDK/key/preflight path and legacy smoke CLI now deny before credentials or SDK access.
- Frozen-source binding validates project/root tracked committed inputs, exact candidate hashes, durable trial reservation, cumulative 744-call primary ceilings and prior provider receipts before any transport process. Real Git/SQLite fixtures reject staged/unstaged/untracked sources, dirty root policy, cross-ID unknown reservations beyond primary and uncertain restart. These are fixture/control results, not model calls.
- Framework registry now denies live use and disables telemetry before imports, using flags confirmed in installed CrewAI/CoreTelemetry source. The real six-runner fake comparison passed with external sockets denied and zero external attempts observed. No framework control-flow implementation changed.
- Focused checks passed 20 tests; the final locked full gate passed 60 tests and all six runner comparisons over the versioned 60-case installed-wheel fixture. Live quality metrics remain PENDING. Docker identity observations were unchanged and the root account still records the original sixteen P00 attempts, with no P01 registration or provider ledger.
- Owner execution remains disabled, approved campaigns/allocations empty and paid authorization zero. Complete durable campaign dispatch, candidate freeze, actual evidence/tool integration, preflight, reviews, holdout/generalization and promotion remain INCOMPLETE/PENDING. Batches for later dispatch must contain at most ten provider attempts; the dry-run plans two full four-call workflows per batch (maximum eight calls), without reducing total coverage.
- Evidence and commands: `artifacts/evidence/accounted-core-boundary/`. Safe next CLI is offline: `uv run --locked python scripts/run_live_campaign.py --stage pilot --dry-run`.


## 2026-10-27 — Phase 010 Core step/tool safety

- Phase 010 raised a regression showing `CoreTriageRunner` would honor a caller's six-step budget and repeatedly invoke the responder, even though the live accounted contract allows only four model calls. The Core runner now defaults to four and rejects any larger request before invoking a client.
- The actual accounted Core path now has a specific regression for a model-requested effectful tool call: the response is recorded as one terminal attempted call, no local tool is executed, the workflow closes, and a repeated worker invocation is rejected.
- Focused Core tests pass (9) and accounted Core tests pass (21). Full fast/full gates are recorded under `artifacts/evidence/core-tool-safety/`; live generation remains disabled. Existing user-modified standard gate outputs were preserved byte-for-byte.
- No KB/billing source or connector exists. A read-only tool contract proposal is documented; no evaluation facts or fixture contexts were promoted as retrieval. No external/effectful tool or campaign allocation was created. Provider billing tier and campaign/review approvals remain PENDING.

## 2026-10-27 — Phase 011 real tool source contract: proposal PASS; integration INCOMPLETE

- Source inspection reconfirmed that P01's actual Core path is fixed to four provider calls and the accounted boundary terminally rejects model-supplied `tool_calls`. No P01 KB corpus, billing connector, source identity, tenant authorization contract, or effectful executor exists. Synthetic worker contexts and golden facts remain excluded from retrieval.
- Added non-executable proposals for `search_knowledge`, `lookup_billing`, bounded Core plan dispatch, and the separate idempotency/outbox/receipt requirements for any future write tool. The proposed schemas specify trusted tenant/customer provenance, source version, ACL enforcement, typed unavailable/denied states, output bounds, timeouts and evidence IDs. They are not approved contracts or connected service paths.
- Locked offline development dry-run passed with 54 logical trials and maximum 216 provider calls; it reports `generation_authorized=false`, `provider_accessed=false`, `credentials_read=false`, paid authorization USD 0, and review status PENDING. Billing/quota evidence, dataset/rubric review, expanded campaign approval, primary/confirmation reservation and execution limits remain blockers. No request or credential was used.
- The three pre-existing modified gate outputs (`artifacts/evidence/check-fast.txt`, `artifacts/evidence/check-full.txt`, `artifacts/runs/latest/results.json`) were not run through standard scripts or staged; SHA-256 before/after values match in `artifacts/evidence/real-tool-source-contract-011/preservation.json`.
- Real retrieval, planner/tool execution and effect idempotency remain INCOMPLETE until the source owner supplies an eligible local source/version, tenant/record ACL contract, and non-customer verification environment. Live dispatch, model quality, human/independent review and promotion remain PENDING/INCOMPLETE.

## 2026-10-28 - Phase 012 synthetic dispatch

- Fixture-only bounded reads use durable reservations and receipts; unknown work is not replayed. Focused tests and the locked fake full gate passed. Real integrations and independent review remain pending. Evidence: artifacts/evidence/synthetic-dispatch-012/.

## 2026-10-28 - Phase 014 Core fixture dispatch

- The Core runner can explicitly dispatch bounded synthetic reads with a fake client and caller-provided fixture context. Four focused tests and the full fake gate (71 tests) passed; real sources, identity and live evaluation remain pending. Evidence: artifacts/evidence/core-fixture-dispatch-014/.

2026-10-29 phases023/024: second explicitly reviewed diagnostic INCOMPLETE after two calls509/134, worker_contract at kb_researcher; original and both diagnostic outcomes/reserves retained12calls. Native strict worker schemas and content-free structural diagnostics now pass full100 tests/six runners in isolated fake snapshot, preserving user output hashes. No additional live dispatch or release. Further live operation requires new explicit finite scope, preserving12 calls, validated migration and fresh candidate; quality/human/holdout/promotion pending.
2026-10-30 phase026: fixed P01 revalidation's recursive campaign-lock deadlock. Focused unittest passed 8 tests; isolated committed-source fake full gate passed 109 tests, six runner comparisons and source/docs checks, with protected standard outputs byte-identical and zero provider/generation calls. Commit `7dc0390`. The separately authorized phase025 invocation remains consumed and INCOMPLETE: no invocation marker, logical/provider reservation, or provider access. No live retry was performed; quality, human review, holdout and promotion remain pending.

2026-10-30 phase027: prepared distinct operation `local-reviewed-operation-027-v1`, with a durable entry marker, one workflow, four calls maximum and retained historical logical reservations. Focused ten tests and final isolated fake gate119 tests/six runners PASS; protected pre-existing outputs unchanged. Root guard committed separately as `80d332a`; migration remains APPLIED. No live operation dispatched yet. Candidate commit, frozen manifest and live preflight remain pending; no quality or human approval is claimed.
