# Live Groq and Docker acceptance

Status: verified for the bounded acceptance case.

Run one Core workflow with the real Groq client and rerun the complete deterministic framework comparison.

The user authorized starting local Docker services and using Groq. Preserve existing Compose projects, data and ports; use an empty dedicated project for destructive acceptance scenarios. Use only GROQ_API_KEY_1..4 loaded silently from the root .env and openai/gpt-oss-20b after authenticated model preflight. Never write credentials, headers, raw prompts or model responses to evidence. Keep fake/replay deterministic and use no silent fallback.

Limits: USD 0.01 estimated; four serial 256-token completions; maximum one key pass, transient-only retry, bounded backoff/Retry-After. Only the designated free allowance is authorized; billed cost is PENDING absent billing evidence. Pause generation on quota/budget failures. A failed completed semantic evaluation is retained; do not repeat it merely for a passing sample.

Acceptance: offline checks pass, configured local service checks execute, the project-relevant live case records real model/usage/assertions, and artifacts include commands, exit codes and sanitized results. Missing prerequisites remain INCOMPLETE. Do not change the kit, publish, push, or perform real refunds/outbound messages.
