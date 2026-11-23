# Phase 029: accounted framework adapters

## Goal
Make the five existing framework runners testable through a bounded, receipt-accounted client without opening a live campaign. The owner selected all five adapters on 2026-11-23. The existing Core development campaign is closed and must not be replayed.

## Safety and scope
Use fixture transports only. Do not contact a model, change the root guard or campaign allocations, consume holdout or confirmation cases, or enable live registry access in this phase. Preserve all existing reservations and dirty artifacts. Framework execution must not retry a dispatched or uncertain request; enforce a maximum of four calls and deterministic indices. LangGraph's concurrent workers and retry policy must be explicitly accommodated or refused before dispatch; a lock alone cannot establish the required worker order. Each runner must preserve its actual framework orchestration and have content-free receipts. Do not report fixture outcomes as live quality.

## Acceptance
Exercise each framework with synthetic inputs and an accounted fixture transport. Test ordered calls, early termination, call limits, failure/unknown-work stop and absence of replay, including LangGraph concurrency and timeout behavior. Existing fake-mode contracts must pass. Live campaigns, dataset selection, root authorization and production promotion are separate work and remain pending.
