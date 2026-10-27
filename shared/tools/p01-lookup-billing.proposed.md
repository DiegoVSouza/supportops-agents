# Proposed tool: `lookup_billing`

**Status: PROPOSAL ONLY — no executable source, endpoint, tenant/record authorization contract, or approval exists.** This document does not authorize a connection or claim billing behavior.

## Intended behavior

Read one bounded billing summary for the customer already attached to an authenticated P01 ticket. The source must be P01-owned or explicitly authorized for P01, with an identified owner, versioned API/schema, tenant boundary, record ACL, and local/non-production test endpoint specified before implementation.

## Proposed input

```json
{"customer_ref":"<opaque trusted ticket reference>"}
```

The model cannot nominate a tenant or arbitrary customer. The adapter binds the request to the trusted authenticated principal and the customer reference already authorized for the ticket. Do not accept account numbers, payment credentials, arbitrary identifiers, or tool arguments copied from untrusted message text.

## Proposed result

```json
{"status":"found|not_found|denied|unavailable","source_version":"<pinned version or null>","summary":{"charge_state":"current|past_due|duplicate_review|unknown","invoice_amount_minor":null,"currency":null},"evidence_id":"<opaque source receipt or null>"}
```

Return only allowlisted billing fields needed for the triage contract. No payment instrument, full invoice, address, contact detail, account mutation, refund instruction, or arbitrary upstream message is returned. Keep the encoded result within 768 UTF-8 bytes. A missing/denied/unavailable record is not a negative billing fact and must not be paraphrased as one.

## Proposed runtime limits and failure rules

- One read-only lookup per invocation; three-second deadline; no retry after timeout or ambiguous transport failure.
- The source enforces tenant and record authorization using the trusted principal. P01 verifies the source version and a bounded evidence receipt before returning the summary.
- The tool has no write capability and is not an executor for refund, cancellation, credit, account update, or customer communication.
- Missing source, source-version mismatch, stale or missing authorization, invalid response, or timeout fails closed; no fake fixture or sibling-project data may substitute.

Limits above are a proposal and require source-owner/privacy review before implementation. Tool selection and execution must fit the original four-call Core envelope; changing the plan/prompt protocol requires its own frozen candidate and evaluation plan.
