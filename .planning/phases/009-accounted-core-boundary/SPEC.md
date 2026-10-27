# Phase 009 — Accounted Core provider boundary

Status: PLANNED. Provider generation and promotion remain INCOMPLETE.

## Outcome

Connect the actual Core supervisor's classifier, knowledge worker, billing worker and responder to the documented lab account/transport protocol. Remove the production bypass through the legacy direct SDK client and its implicit key rotation. Keep fake/offline framework comparisons unchanged and preserve every dataset, rubric, split, grader and threshold.

Baseline inspected: clean P01 HEAD `60be3e028cd39eb4314e4dcc4e46be018ec57a35`. Phase 008 supplies a local durable trial ledger; the live adapter still constructs Groq SDK clients directly and retries transient errors. This violates the current single-attempt/account-wide authorization. Legacy smoke acceptance remains historical and cannot authorize new calls or establish broad quality.

## Required behavior

1. A project-owned guarded adapter implements the existing `LLMClient.complete(agent,payload)` boundary used by the real Core runner. It binds project/campaign/case/trial, enforces the four-worker order and at most four single provider attempts, assigns stable call indexes and stops permanently for that workflow on guard denial, provider/JSON/contract failure, interruption or unknown work. It never falls back, rotates keys, retries a semantic failure or replays an uncertain call.
2. All normal production Groq completion paths use a root subprocess transport protocol v1 with explicit UTF-8 and bounded timeout. No sibling project source is imported. The parent does not read credentials or import the Groq SDK; the root transport alone owns the numbered credentials and account registry/receipts. Construction requires a valid owning-project execution manifest; this phase leaves execution disabled and creates no account registration or provider session.
3. A pure payload builder uses a versioned generic worker prompt under `agent/prompts/`, includes only actual Core shared state and global worker contracts, and includes no expected labels, grading facts or rubric. Match full canonical transport normalization and framing; enforce the existing 2,048-input/256-output per-call caps before transport initialization or dispatch. Reject oversized evolving workflow state rather than truncating it silently.
4. Disable legacy direct-key completion and model preflight before key reads or SDK initialization. Preserve the importable public names with an explicit sanitized guard-required failure and document the safety restriction in an ADR. Replace the old retry expectation with stronger no-provider/no-retry coverage under the current authorization; preserve historical reports.
5. The Core's actual worker loop remains the orchestration path. It has no financial-effect or external-tool executor; document that boundary and do not create a detached classifier or claim external-effect behavior. Duplicate provider effects are prevented by stable trial/call identity and permanent workflow stop; full durable campaign dispatch/allocation/resume remains for the next owning phase.
6. Project/root committed-source binding, primary-versus-confirmation allocation and immutable campaign/provenance enforcement must be specified before later generation. P01's unchanged root envelope is 984 calls (744 pilot/main plus protected confirmation 240), 2,015,232 input / 251,904 output, USD 0.2267136 economic estimate; paid allowance remains USD 0. No corrections, judges or canary are funded implicitly. Phase 009 consumes zero calls and does not enable `--execute`.

## Acceptance

Offline tests execute the actual Core loop through a fixture implementation of the guard contract, proving four serial indexed calls, early escalation, no fifth/duplicate worker, full payload bounds, no expected-field leakage, typed allowlisted diagnostics and stop on timeout/quota/guard/invalid output. The real root encoder is checked through an offline subprocess contract probe, without constructing ProviderSession or loading keys. Legacy CLI denies unallocated calls before `.env`/SDK access. Fake/framework and existing ledger regressions remain passing in locked environments. No fixture is counted as live quality evidence.

Dataset/rubric/human/independent review, actual account preflight, broad campaign execution, full durable campaign integration, real external tools/effects, heldout/generalization and promotion remain PENDING/INCOMPLETE.
