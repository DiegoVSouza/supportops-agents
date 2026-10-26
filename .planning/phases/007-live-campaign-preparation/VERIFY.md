# Verify — Live campaign preparation

Use repository artifacts and commands, not chat claims. Save each command, exit code, and sanitized output to `artifacts/evidence/live-campaign-preparation/`.

- [x] Dataset has 60 unique cases, 18 development / 42 holdout, 36 English / 24 Portuguese, and at least three cases per family. Dataset SHA-256 is recorded.
- [x] Source groups are distinct and validation rejects cross-split leakage. Independent review provenance remains `PENDING`.
- [x] Code-first tests reject wrong decision, route, agent order, over-limit traces and unsupported-claim/safety flags. Human grounding/rubric review remains `PENDING`.
- [x] Core is the only claimed live runner; all five framework runners have explicit offline-only reasons.
- [x] Config has finite per-case caps and explicitly labels unresolved cumulative spend/request/token, retry/pacing/time, confirmation funding and approval as `PENDING`; paid spend stays USD 0.
- [x] Python `-S` dry-run reports 24 pilot / 720 primary / 240 confirmation / 984 additive calls and token maxima, with all blockers. No provider, credential, or Docker access occurs.
- [x] Generation exits incomplete during preparation and cannot construct a provider client or silently fall back.
- [x] Fake fast/full checks pass: 33 tests, six-runner offline comparison and demo; command and exit evidence are saved.
- [x] No provider calls or live quality metrics are claimed. Existing golden comparisons remain fixture-only.
- [ ] Durable cumulative ledger/resume and serialized campaign lease remain gates for the bounded-runner phase.
- [ ] Independent dataset/rubric review and clean-context phase verification remain outstanding.
- [ ] Final staged-path/secrets review is pending commit preparation.
