# P01 real-model orchestration evaluation

## Status

Implemented and verified. Real runs exposed Groq JSON validation failures and over-escalation of routine questions. JSON is now validated locally and the escalation policy is explicit; the final four-key Core run passed.

## Goal and selection

Run one synthetic SupportOps ticket through P01's dependency-injected Core supervisor/worker flow using Groq for each agent step. P01 is selected because its purpose is comparing multi-agent orchestration, yet the current runtime uses only `FakeLLMClient`; no model quality evidence exists.

## Requirements

- Use the optional official Groq SDK and `openai/gpt-oss-20b`, authenticated model preflight before completions.
- Implement a P01-local `LLMClient` that returns the exact agent-specific JSON contracts; one ticket and the Core runner only. Do not fan out to all six frameworks in the live run.
- Keep `LLM_MODE=fake` default and all framework comparisons offline/deterministic. Require explicit live opt-in.
- Load root `.env` silently, use only `GROQ_API_KEY_1..4`, retry/rotate only bounded transient failures, and sanitize output.
- Cap each completion at 256 tokens, use a 20-second timeout, limit to one key pass per logical request, and reserve at most USD 0.01 estimated exposure for this run under the existing USD 2 task budget.
- Evaluate stop reason, step order, category, safe response, and escalation behavior against a small synthetic case. Record actual provider model, reported usage, estimated cost, attempts, and each assertion.

## Acceptance

1. Mock tests cover parsing/contracts, mode gating, rotation/retry, cost cap, and redaction.
2. Offline suite remains deterministic without network.
3. One real Core workflow run completes or records a sanitized provider/runtime failure; a successful HTTP response alone is insufficient.
4. Run artifacts contain command/exit code/usage and no prompts, headers, or credentials.

## Scope

P01 only; one Core runner, one synthetic ticket. No kit or sibling-project edits, framework package upgrades, production data, or external actions.

## Verified references

- Model and tool-use support: [Groq GPT-OSS 20B](https://console.groq.com/docs/model/openai/gpt-oss-20b).
- Free-plan limits and `Retry-After`: [Groq rate limits](https://console.groq.com/docs/rate-limits).
- Official Python SDK release: [groq-python 1.7.0](https://github.com/groq/groq-python/releases/tag/v1.7.0).
