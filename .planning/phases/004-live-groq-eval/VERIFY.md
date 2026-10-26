# P01 verification

## Planning

- Confirm existing fake-only agent contract and that the new phase writes only P01-owned paths.
- Confirm at most four serial agent calls, <=256 output tokens each, <=USD 0.01 estimated exposure, and no provider fallback.

## Offline

- Run live-client mocked tests, existing shared runner contract tests, and full documented P01 gate with live mode unset.
- Save command, exit code, and output under `artifacts/evidence/phase-004-groq-offline.txt`.

## Live

- Query Groq model catalog using root `.env` loaded silently; require `openai/gpt-oss-20b`.
- Execute one Core runner ticket, record each agent step and provider usage without storing prompts/responses, and compare the final `TriageResult` to its domain assertions.
- Save sanitized JSON and `.txt` command/exit evidence under `artifacts/evidence/phase-004-groq-live.*`.

## Review

- Report actual-run metrics only; label one-ticket results as smoke evidence, not broad quality claims.
- Preserve all fake baselines and history. Check staged paths and secret scan, run local commit hook, commit locally, and do not push.

## Recorded result — 2026-10-26

- Offline: final full gate passed with 26 tests, including explicit live-mode, four-key selection, transient-only rotation, budget preflight, secret redaction, and unchanged fake Core behavior. Full comparison gate passed across all six runners.
- Live: `LLM_MODE=live uv run --extra live python scripts/run_live_groq_eval.py`; exit 0. Four numbered keys passed model preflight; Core used 4 serial calls; 1470 input / 655 output tokens; estimated cost USD 0.00030675; approved response, action, category and agent order passed; no retries or rotation.
- Earlier runs were preserved as separate timestamped artifacts. Provider JSON mode caused HTTP 400 `json_validate_failed`; after local JSON parsing, a tracking case escalated; the policy-only case still over-escalated. A general escalation rule fixed the defect. A mocked test then found and fixed secret leakage from client-construction errors before the sanitization boundary.
- Final run passed on the clarified synthetic policy question. One ticket is smoke evidence, not a broad quality claim.
