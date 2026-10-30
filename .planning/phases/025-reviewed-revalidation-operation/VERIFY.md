# Verification

Plan self-check PASS on attempt 2: SPEC/PLAN/VERIFY present, exactly three tasks, concrete paths, exact finite call/token/cost caps, fake default, retained historical reserves and one live invocation. Attempt 1's phrase check was case-sensitive; the documented sentence began with a capital letter. Both results remain in `artifacts/evidence/revalidation-operation-025/plan-validation-attempt{1,2}.json`. Command `python -` (validation source piped on stdin), cwd `C:\estudo\Golpe\lab\projects\p01`, exit 0. No provider or credentials accessed.

## Offline implementation and validation

- Root finite migration `p01-p04-reviewed-revalidation-v1` is applied exactly once. Applied policy SHA-256: `f8428a8da06fd551e6a41d3d009db69d1d31c620eda68ef21a02ff1dbcc32cdf`. Root migration retained all six original UUIDs and every provider/logical history prefix; it added only four P01 calls to the bounded envelope. Evidence: root `artifacts/evidence/llm-live-readiness/p01-p04-revalidation/`.
- Official Groq model and Structured Outputs documentation was checked on 2026-10-30 and recorded in `artifacts/evidence/revalidation-operation-025/official-source.json`. The configured model supports strict JSON schema; exact account quota remains an account-level preflight, not inferred from public Free-tier limits. Price estimate is within USD 0 paid authorization.
- Focused controller fake tests: attempt 1 exposed a test assumption that reservation totals include a `reserved_calls` field; no product defect or provider access. Corrected the assertion to use the durable request total. Attempt 2: 7 tests PASS. Evidence: `operation-focused-attempt{1,2}.json` and `.txt`.
- Dispatch binding test: attempt 1 fixture hit the append-only SQLite trigger while trying to mutate an established history row; corrected the fixture to construct isolated state. Attempt 2: 23 tests PASS, including the exact new controller binding. Evidence: `binding-focused-attempt{1,2}.json` and `.txt`.
- Python compilation passed for the controller, accounted-live implementation and both test files.
- Full fake gate ran in a Git-archive snapshot: `scripts/check_full.py`, exit 0, **108 tests PASS**. `snapshot-result.json` records no provider access. All three protected, pre-existing user outputs remained byte-identical (`snapshot-preservation.json`). Command and output are in `snapshot-commands.json`.
- Root migration dry-run reports `ALREADY_APPLIED`; the scoped P01 controller validation verifies the exact applied migration, authorization, source binding and retained histories before permitting an invocation.

## Remaining gated work

The source candidate and operation manifest still need separate commits and a final offline `--validate`. Then the one user-authorized, single-use live invocation may proceed only if current credentials, exact model access, quota headers, clean source fingerprint, root bindings and both durable ledgers pass preflight. No live call has been made by this phase. The original P01 attempt remains INCOMPLETE with its four-call reservation retained. This new diagnostic is capped at four calls / 8,192 input / 1,024 output tokens (estimated USD 0.0009216, paid USD 0). If invocation starts, it will not be repeated. Human review, quality, holdout and promotion remain pending.

Source context: phase 024 strict worker-schema candidate `f1b3742` passed four focused tests and 100 full fake tests/six runners in an isolated snapshot. The root guard commit is `f211d88`; the finite migration was subsequently applied under the exact SHA above. Historical P01 calls/results and the original 12-call logical reservation remain intact.
