# Core tool safety and execution limits

P01's actual Core path has four serial worker calls: classifier, knowledge, billing and responder. The Core runner now defaults to four calls and rejects a larger step budget before calling its LLM client. The accounted live client uses stable campaign/case/trial/call indexes, rejects out-of-order or fifth calls, and permanently stops after guard, provider, timeout, interruption, schema or tool-selection failure.

There is no KB or billing data source/connector in the repository, and `agent/tools/README.md` requires a matching tool spec. Do not treat fake contexts or evaluation expected facts as retrieval. The current model boundary rejects all provider tool calls before an executor exists. This means duplicate external effects are impossible on this path today; it is not evidence that a future effectful tool is idempotent.

## Concrete next-tool proposal

If P01 later receives an approved local knowledge corpus and billing-record service, add only two read-only tools first: `search_knowledge` and `lookup_billing`. Each must have a versioned spec, source identity, tenant/record authorization, strict input/output schema and byte/token limits, bounded timeout, typed unavailable/error results, and evidence IDs that flow into the final answer and trace. Tool execution must be deterministic and must not mutate source records. Refund, ticket update, outbound message, or other effects stay disabled; enabling any of them needs a separate SDD, approval, funded allocation, durable idempotency key and append-only effect receipt/outbox with replay recovery. No service, source, tenant contract, or external-effect authorization currently exists, so that integration remains INCOMPLETE.

Phase 011 records this as a source-gated proposal, not an implementation. Proposed contracts are in `shared/tools/p01-search-knowledge.proposed.md`, `shared/tools/p01-lookup-billing.proposed.md`, and `shared/tools/p01-plan-dispatch.proposed.md`. The current fixed four-call plan and prompt contract cannot be silently changed: a new planner/tool schema requires a frozen candidate and its original live evaluation protocol. The offline development dry-run remains non-authorizing (54 logical trials, up to 216 calls; generation disabled; review, quota, campaign, reserve, and cumulative execution settings still block it). No source data or credentials were read.

Phase 010 is fake/offline only. Its tests are control evidence, not tool quality or live evaluation. The campaign manifest, allocation and all review states remain unchanged/PENDING.
