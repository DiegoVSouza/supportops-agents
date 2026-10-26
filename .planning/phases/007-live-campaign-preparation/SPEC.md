# Phase 007 — Live campaign preparation

## Goal

Prepare a reviewed, project-owned evaluation set and guarded reservation dry-run for P01's Core supervisor-worker live runner. Framework adapters remain offline-only unless a later reviewed phase proves a supported live path and separately reconciles its budget.

## Current evidence and constraints

- Revalidated repository HEAD: `d3d4f9da6c0d1d24c1ce5b7d1b9b9cd2d7bcf20b` (`test(orchestration): verify a real Groq workflow`).
- The prior live decision bounded one Core ticket to USD 0.01 under the USD 2 task profile. It does not reserve the expanded campaign, confirmation set, or additional runners.
- Six runners have deterministic offline comparisons. Existing live quality evidence covers Core only and is not representative of the 60-case campaign.
- No credential inspection, provider call, Docker mutation, cross-framework quality comparison, or budget increase is in scope.

## Acceptance criteria

1. A versioned P01 dataset contains 60 distinct semantic orchestration cases: 18 development and 42 sealed holdout, covering classification, routing/order, billing vs knowledge, incomplete evidence, escalation, contradiction, and loop/turn termination.
2. Every applicable family has at least three distinct cases; quality cases use 36 English and 24 Portuguese scenarios, including ambiguous and informal requests. Each case has expected decision/allowed tools, forbidden behavior, rubric, criticality, and finite task/call/token caps.
3. Configuration includes three trials, the four-call-per-trial maximum for Core, all cumulative ceilings, confirmation reserve, timeout/retry/pacing/chunk fields, and budget approval source. Expanded limits remain `PENDING`; the prior USD 0.01 scope is not silently reused.
4. Dry-run shows counts and unresolved reservations without SDK construction, credential reads, network access, or Docker mutation. Generation fails closed unless every required cap, quota, approval, and authenticated model preflight is satisfied.
5. Deterministic grader and preparation checks prove wrong routing, unsupported evidence, invalid tool selection, and termination failures are rejected. Artifacts contain only sanitized results and real command/exit/output evidence.

## Out of scope

Provider execution, runtime changes, framework live promotion, public API changes, cross-project imports, paid usage, public deployment, customer data, external communications, and real refunds.
