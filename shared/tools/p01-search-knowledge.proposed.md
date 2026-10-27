# Proposed tool: `search_knowledge`

**Status: PROPOSAL ONLY — no executable source, endpoint, corpus, tenant contract, or approval exists.** This document does not authorize a connection or claim retrieval behavior.

## Intended behavior

Read a small set of evidence passages from one versioned P01-owned knowledge source. The source must be identified by owner, immutable corpus/version identifier, provenance metadata, and a documented local access boundary before implementation. Never read evaluation labels, grader expectations, rubric notes, or case fixtures as product knowledge.

## Proposed input

```json
{"query":"<untrusted search text, at most 512 UTF-8 bytes>","limit":3}
```

The authenticated runtime derives `tenant_id` and authorization from its trusted caller/ticket context. The model cannot choose a tenant, source, filesystem path, URL, or authorization scope. Reject invalid UTF-8, an empty/oversized query, booleans/floats for `limit`, and values outside 1–3 before source access.

## Proposed result

```json
{"status":"found|not_found|denied|unavailable","source_version":"<pinned version or null>","evidence":[{"evidence_id":"<opaque stable id>","document_id":"<authorized source id>","title":"<bounded title>","snippet":"<at most 400 UTF-8 bytes>","rank":1}]}
```

Return no more than three passages and keep the encoded result within 1,536 UTF-8 bytes. No raw document, credentials, HTML, script, hidden grader data, or unbounded URL is returned. Each snippet must be attributable to a versioned source record and preserve its provenance identifier into the final answer/trace. `not_found`, `denied`, and `unavailable` are distinct; callers cannot turn them into fabricated evidence.

## Proposed runtime limits and failure rules

- One read-only source call per invocation; three-second deadline; no retry after timeout or ambiguous transport failure.
- Source access must enforce the verified principal's tenant and document ACL in the source, not only in the planner.
- The adapter may expose only the declared schema and bounded evidence. It cannot write, send, mutate, or execute returned content.
- If the approved source, version, tenant binding, or ACL check is missing, fail closed with `unavailable`/`denied`; do not fall back to fixtures or another project.

Limits above are a proposal and require source-owner review before implementation. Tool selection and execution must fit the original four-call Core envelope; changing the plan/prompt protocol requires its own frozen candidate and evaluation plan.
