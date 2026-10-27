# Proposed Core plan/tool dispatch boundary

**Status: PROPOSAL ONLY.** Current P01 does not implement this plan schema or execute model-selected tools. The live accounted client rejects provider `tool_calls` terminally.

## Proposed planning result

Extend the existing classifier result only in a separately planned candidate:

```json
{"category":"billing|account_access|technical|shipping|other","summary":"<bounded text>","escalate":null,"read_plan":{"tools":["search_knowledge|lookup_billing"]}}
```

The server, not the model, maps allowed tool names to fixed P01 adapters and builds all trusted tenant/customer arguments from authenticated ticket context. No tool arguments can request a write, network destination, filesystem access, arbitrary method, or retry. Unknown/duplicate tools and malformed output end the workflow with a fixed terminal diagnostic.

## Call and effect limits

- The plan is produced inside the existing classifier call; no fifth provider call is added. Each existing provider attempt retains its stable campaign/case/trial/call index and 2,048/256 token limits.
- A subsequent candidate must explicitly preserve the original evaluation cases, split, rubric, graders, thresholds and required live campaign coverage. Any changed prompt/payload/source fingerprint is a new candidate; historical results cannot be transferred.
- The only proposed initial tools are the two read-only contracts in this directory. There is no tool for refund, customer messaging, account/ticket mutation, external HTTP selection, or arbitrary code.
- A read-only duplicate call can be tolerated only if source ownership confirms no external effect; unknown timeout remains unavailable and is not retried.

## Preconditions before executable work

1. P01 source owner supplies the corpus and billing-record source identity/version, local/test access contract, and accountable owner.
2. The source owner approves tenant and record authorization claims, data fields and retention, and names a non-customer test fixture or disposable local service.
3. P01 creates a new SDD phase for the source adapters, planner schema, prompt/candidate provenance, deterministic control tests, and real service-path gate. No connector may be tested against production or real customer records.
4. P01 verifies Free billing tier and usable shared account quota, and follows its existing funded campaign protocol. Current free-tier billing/quota is UNKNOWN; paid authorization is USD 0.
5. For any future effectful action, create a different phase with explicit authorization and funded allocation; require an authenticated actor, approval where applicable, a tenant-scoped idempotency key, durable intent/outbox before dispatch, append-only external receipt, reconciliation of unknown outcomes, and no replay until authoritative outcome is known.

Until these preconditions are met, real planning/tool integration and duplicate-effect guarantees remain INCOMPLETE. The current fail-closed rejection of provider tool calls remains the correct runtime behavior.
