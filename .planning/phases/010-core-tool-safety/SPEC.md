# Phase 010 — Core tool safety and execution limits

Status: PLANNED. No provider, credential, network, Docker, or external-effect use is in scope.

## Problem

Phase 009 connected P01's actual Core worker loop to a single-attempt accounted client, but the general Core runner accepts `max_steps` values above the live contract's four provider-call limit. The accounted adapter blocks a fifth call, while fake/local execution can continue invoking the responder. The product has no concrete KB or billing connector/spec: `agent/tools/README.md` requires a matching spec, and the current agent card/security policy expose no external tools. The live adapter rejects provider `tool_calls` and must continue to do so until a separately reviewed read-only tool contract and source exist.

## Outcomes

1. Make the actual Core runner enforce the declared maximum of four worker/model calls per workflow, regardless of injected client. Requests above the product maximum fail before the first call.
2. Keep tool execution closed in the live accounted path. A tool call, including a repeated or effectful call, becomes a sanitized terminal failure; it is never dispatched, retried, or converted to a second worker call.
3. Preserve all datasets, expected labels, splits, rubric, graders, thresholds, framework implementations and campaign allocations. Fake tests are control evidence only. Campaign execution remains disabled.
4. Record an owning proposal for future real retrieval: `search_knowledge` and `lookup_billing` must be read-only, versioned tools backed by named P01-owned sources, with tenant/record authorization, evidence provenance, input/output bounds, timeout and failure contracts. No source is currently configured. Refund, account mutation, ticket update and outbound-message tools require a separate authorization/allocation phase and durable idempotency key/outbox contract; phase 010 does not implement them.

## Acceptance

- `CoreTriageRunner` rejects `max_steps > 4` before client invocation and terminates non-approved responder output by four calls maximum.
- Actual Core plus `AccountedCoreClient` rejects provider tool calls before local execution; only one provider attempt is recorded and the workflow cannot continue.
- Existing early escalation, worker order, output contract, guard, timeout, unknown reservation, UTF-8, payload-bound, fake/framework comparison and locked-gate tests remain intact.
- No actual KB/billing source, customer record, financial action or outbound path is invented. Their integration remains INCOMPLETE until a concrete P01-owned source and contract are available.

Human, independent, dataset/rubric review, provider billing tier and campaign allocation remain PENDING. Paid authorization remains USD 0.
