# Phase 008 — Bounded campaign ledger for P01

## Goal

Add durable, project-local reservation and resume inspection to P01's Core campaign foundation while keeping provider generation disabled until its unresolved policy gates are approved. This phase is offline only; it does not execute Groq calls or change framework runners.

## Starting evidence

- Phase 007 froze a 60-case Core dataset and a dry-run that reports a maximum 24-call pilot, 720-call primary campaign, and 240-call fresh confirmation reserve.
- Cumulative free quota, tokens, estimated spend, wall-clock/pacing limits, dataset/rubric review, confirmation funding and campaign approval are `PENDING`; paid spend remains USD 0.
- P01 has an existing opt-in single-ticket Groq path with a USD 0.01 estimated cap. That exception does not authorize campaign traffic.
- P00's Phase 012 introduced a project-local SQLite ledger and OS lease primitive. P01 must implement and test its own campaign contract without importing from a sibling repository or claiming cross-project accounting.

## Acceptance criteria

1. A project-local append-only ledger persists pre-dispatch reservations and outcomes, retains the reservation when usage is unknown, prevents duplicate reruns of an uncertain/completed trial, and enforces cumulative request/token/estimated-cost caps under concurrent reservations.
2. Campaign lease excludes concurrent P01 campaign processes and releases on normal exit; metadata contains no credentials or case content.
3. `--resume CAMPAIGN_ID --dry-run` inspects only recorded P01 state without provider access; unknown or empty campaigns fail with exit 2. Resume never retries an uncertain dispatch.
4. The execution path remains fail-closed while approvals and finite campaign limits are pending. Dry-run and tests must not construct the SDK, read `.env`, contact Groq, or mutate Docker.
5. Deterministic tests exercise ledger immutability, usage reconciliation, concurrency, lease contention, resume inspection, sanitized output, and pending-gate blocking. Fast/full fake gates pass and evidence is saved.

## Out of scope

Groq dispatch, approval/quota acquisition, dataset or rubric edits, threshold changes, cross-project ledger/lease integration, framework live runners, Docker changes, paid calls, public deployment, external effects, or modifying historical campaign evidence.

## Status

`PLANNED`; promotion remains `INCOMPLETE` until all applicable campaign and runtime gates pass.
