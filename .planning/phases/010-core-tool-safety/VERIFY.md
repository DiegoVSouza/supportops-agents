# Verify — Core tool safety and execution limits

Status: **OFFLINE CONTROL PASS; REAL RETRIEVAL INCOMPLETE**. This verification was performed by the implementing agent; independent review remains PENDING.

- [x] Core rejects `max_steps > 4` before invoking its client; defaults to four.
- [x] Non-approved responders and Core fake comparison stop under the four-call product ceiling. Framework adapters retain their existing behavior.
- [x] Model-supplied effectful `tool_calls` are terminally rejected after one accounted provider result; no local/external tool executor runs and repeated calls fail as stopped.
- [x] Locked fast and full gates pass: 62 tests; all six fake comparison runners pass all 60 P00 golden cases, with evaluation metrics still PENDING.
- [x] Commands, exits and output are saved under `artifacts/evidence/core-tool-safety/`.
- [x] Pre-existing user-modified `artifacts/evidence/check-fast.txt`, `check-full.txt`, and `artifacts/runs/latest/results.json` were restored byte-for-byte after gate runs; before/after hashes match in `preservation.json`. The initially clean `artifacts/runs/latest/COMPARISON.md` was restored after saving generated comparison evidence.
- [x] No provider, credential, network, Docker or external-effect use occurred; campaign config/ledgers/registry and all evaluation files remain unchanged.
- [ ] Real KB/billing sources and retrieval are unavailable. The concrete read-only tool/source proposal is in `docs/knowledge/core-tool-safety.md`; external effects remain disabled.
- [x] Human, independent, dataset/rubric, billing-tier and promotion reviews remain PENDING.

Supplemental formatter note: Ruff 0.15.21 from the global Python passes lint but `format --check` requests whole-file formatting of the Core/test files; the committed Core baseline also failed this formatter check. Ruff is not installed in the project's locked environment. No broad formatting rewrite was applied. The locked project gates do not include Ruff formatting.
