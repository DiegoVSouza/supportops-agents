# Verify — Live campaign preparation

Use repository artifacts and commands, not chat claims. Save each command, exit code, and sanitized output to `artifacts/evidence/live-campaign-preparation/`.

- [ ] Dataset has exactly 60 unique semantic cases, 18 development and 42 sealed holdout; family coverage and English/Portuguese denominators are correct.
- [ ] Related source/scenario groups do not cross splits; cases include expected decisions/tools, forbidden behavior, rubric, criticality and finite caps.
- [ ] Graders reject deliberate wrong routing, tool use, unsupported facts/evidence, contradictions and invalid termination outcomes.
- [ ] Core is the only claimed live runner; each other advertised framework runner is listed with an explicit offline-only rationale unless separately budgeted and verified.
- [ ] Config includes three trials, per-task/per-call limits, cumulative request/input/output/spend caps, confirmation reserve, timeouts, retry policy, chunk/pacing/wall-clock ceilings, and budget source.
- [ ] Dry-run does not construct the SDK, read credentials, access network, or mutate Docker, and clearly reports the 24-call pilot / 720-call full Core ceilings and all PENDING fields.
- [ ] Generation fails before dispatch when expanded approval/quota/caps or authenticated model preflight are missing; no fallback or semantic retry occurs.
- [ ] Fake-mode fast/full checks pass without unexpected skips and outputs are saved.
- [ ] No provider calls or quality metrics are claimed by this preparation phase; fixture scores are not represented as live results.
- [ ] Staged changes are within allowed paths and contain no secrets or unrelated user data.
