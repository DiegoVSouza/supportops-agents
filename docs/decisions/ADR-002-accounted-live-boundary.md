# ADR-002 — Require accounted single-attempt Core calls

Status: accepted for offline implementation under the user's existing authorization, 2026-10-27. Human quality/promotion approval remains PENDING.

## Context

The historical Groq adapter directly loaded credentials, constructed SDK clients and rotated keys after transient errors. Those behaviors bypass the shared account ledger and can replay an uncertain operation under the current free-only protocol. The old one-ticket smoke does not allocate new traffic. Baseline evidence and its old retry expectation are retained in phase 009 evidence.

## Decision

Use a project-owned `AccountedCoreClient` at the actual Core `LLMClient` boundary. Bind every worker to one campaign/case/trial and a stable call index, enforce four serial workers and original 2,048/256 per-call caps, and stop the workflow after any denial, failure, invalid result or interruption. The pure payload builder reads a versioned generic prompt and accepts only actual Core shared-state fields. It never reads expected outcomes or rubric metadata.

The only production transport is the lab's documented UTF-8 subprocess protocol v1, fixed to P01. The parent passes no provider keys and imports no Groq SDK. Before a process can start, the owner manifest, declared allocation, frozen committed source identities, new durable four-call reservation, primary cumulative limits and absence of prior receipt for the trial must validate. Unknown usage stays reserved. Phase 009 leaves the owner manifest disabled and allocation list empty; full campaign controller/freeze work is still required.

Retain the legacy import names and argument signatures, but reject their unaccounted completion/key/catalog path before `.env` or SDK access. The old CLI reports `legacy_smoke_not_allocated` and provides an offline next step. This enforces the current authorization rather than expanding the public runtime contract; no package signature, dependency or version changes are introduced. A future published guarded runtime contract must be versioned separately if it changes public data/API shapes.

## Consequences

- No automatic key rotation, semantic retry, fallback, fifth worker or uncertain replay exists in the guarded Core client.
- Framework adapters remain fake/offline; this phase does not grant them live allocations.
- Installed CoreTelemetry disable flags are set before offline framework imports, and the registry rejects their live mode. A Python socket-denial comparison observed zero external attempts; no claim is made about unrecorded historical telemetry.
- Core workers currently have no external read/write tool executor. Knowledge/billing fields are worker contexts; no real refund, account mutation or outbound action is performed. Actual evidence/tool integration and durable campaign execution need their own phases before product-quality claims.
- The old retry test is replaced with stronger tests proving zero SDK/credential access and no rotation. Historical reports are immutable; no dataset, rubric, grader or threshold is changed to pass.
- No provider call, registry entry, ledger migration, Docker change or paid use occurs in this phase. Dataset/rubric/human/independent review and promotion remain pending.
