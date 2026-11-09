# Phase 028: sealed P01 Core development campaign runner

## Goal
Replace the "campaign generation is blocked" stub of `scripts/run_live_campaign.py` with a sealed, resumable executor that runs the real Core supervisor/worker (classifier, kb_researcher, billing_agent, responder) against Groq on the `p01-live-v1` **development split only**, so `framework-quality-metrics` carries a measured Core number instead of a bare `PENDING`.

## Authority
Owner reply of 2026-11-09, verbatim: "pode usar os modelos da groq tem as env ai documentada" and "faz a 1 mesmo". Recorded in `.planning/llm-live-readiness/phases/059-p01-live-campaign/AUTHORIZATION.json` (lab repo, committed `5f8cfa6`). Free Groq keys, `openai/gpt-oss-20b`, paid 0.00, owner total-loss cap USD 5.00, shared window 200,000 tokens/day and 8,000/minute. Independent review is `WAIVED_BY_OWNER`: owner approval, never independent verification.

## Scope
- Campaign `p01-dev-v1`: the 18 development cases (7 families; 3 classification, 3 routing_order, 3 billing_vs_knowledge, 3 incomplete_evidence, 2 escalation, 2 contradictory_requests, 2 loop_termination; 11 en, 7 pt-BR counted from the case file), 1 trial each, up to 4 provider calls per trial (72 at most), through the existing accounted boundary `AccountedCoreClient` + `SubprocessGuard` (root transport v1). Pilot of 4 cases first, then the other 14.
- Out of scope: the 42 holdout cases (never opened), the fresh confirmation reserve, paid spend, semantic retries, any live call of the five framework runners (langgraph, crewai, autogen, semantic_kernel, llamaindex stay fake/replay), other projects.

## What the live number is, and is not
It measures the **Core runner only**. It is not a cross-framework quality comparison: the other five runners were not run live and their quality stays unmeasured. The feature label must say so (`CORE_DEV_SPLIT_MEASURED; RUNNER_COMPARISON_PENDING`).

## Grader (assistant-authored, human review PENDING)
Code-first, following `evals/rubrics/live-v1/rubric.md`. A trial passes only when all hold: the Core run completed (no worker-contract, schema, truncation or input-bound failure), category matches, final action and escalation flag match (for `bounded` loop cases any documented terminal result is accepted, as the rubric says), stop reason matches, agent order is the documented prefix with no duplicate worker and at most 4 steps, the required-fact term groups appear in the final text, and no forbidden outcome fires (claiming a completed refund, cancellation or change; asking for a password or one-time code).

`route` (billing, knowledge, none) is **not graded**: the Core boundary supplies no billing or knowledge tools, so workers can only write "unavailable" and the expected route cannot be observed. The observation keeps `kb_supported` and `billing_supported` booleans only.

## Content-free observations
Per trial: booleans, enums, counts, token totals and per-call latency. Never the ticket text, prompts or model text.

## Measures
Pass rate with Wilson interval (by family and language), failing-check counts, per-trial calls, input/output tokens, estimated cost (policy pricing, free-plan keys), per-call and per-trial latency p50/p95 from the transport receipts.

## Acceptance
1. Fake-mode tests for observation, grader, executor and resume exist and were run red before the code.
2. Root account tests stay green; guards of the other projects unchanged.
3. P01 full fake gate passes.
4. Live pilot (4) and, if clean, the other 14 run through the accounted boundary; the report holds the counts above.
5. `feature_list.json` changes only from the recorded run and keeps human review `PENDING`.
