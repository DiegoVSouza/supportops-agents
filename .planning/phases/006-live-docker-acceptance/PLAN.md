# Execution plan

1. Record the Docker baseline, select unused loopback ports and commit this SDD plan. Inspect current project state and validate the plan boundaries.
2. Implement only the provider/service integration missing for this project's acceptance. Test mode selection and failure paths offline before enabling live mode. Supply credentials only through private process/container environment; never echo expanded Compose config or environments.
3. Execute deterministic fast/full gates and one small live evaluation. Preserve prior reports and retain every failed attempt. Confirm actual service state, model identity, token usage, tenant/privacy/idempotency assertions and configured limits.
4. Review staged paths and sanitized evidence, update VERIFY and progress, and commit locally with a component scope. Leave existing stacks untouched and record newly started services.

allowed_write_paths:
- docs/knowledge/live-docker.md
- .planning/phases/006-live-docker-acceptance/**
- scripts/run_live_groq_eval.py
- src/supportops_agents/live_groq.py
- tests/test_live_groq_eval.py
- docs/harness/decisions.md
- docs/harness/progress.md
- docs/harness/failures.md
- artifacts/evidence/live-docker/**
- artifacts/evidence/phase-*-groq-* (new run artifacts only)

forbidden_changes: root .env, harness-kit/**, sibling source imports, production/customer data, prior provider evidence, existing stack volumes, existing commit history.
llm_mode: fake for regressions; live only for the bounded synthetic provider case.
validation: project fast/full checks; focused service-mode tests; authenticated Groq model catalog; real service assertions.
stop_condition: provider quota/budget failure, missing model, unsafe tenant/tool action, or unrecoverable service failure. Never replace a failed live run with fake data.
