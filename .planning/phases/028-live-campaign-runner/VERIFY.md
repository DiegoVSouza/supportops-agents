# Verify

Status: PARTIAL. Executor built and tested; the live pilot stopped on a provider error, so there is no development result and no quality number.

- [x] Tests were written and run red first (`artifacts/evidence/live-campaign-runner/tests-red.txt`: both modules missing), then green: 144 unit tests pass (`python -m unittest discover -s tests`).
- [x] Fake full gate passes (`artifacts/evidence/live-campaign-runner/check-full-fake.txt`, exit 0). Root account tests: 91 OK (`artifacts/evidence/live-campaign-runner/root-tests-after-run.txt`).
- [x] Candidate `996037d` frozen with manifest `ce8e5d7`; the manifest file set equals the set `SubprocessGuard` requires. Catalog preflight PASS (`catalog-preflight.txt`, zero generation calls).
- [x] Live pilot ran through the accounted boundary: 3 trials graded (9 calls ok), the fourth trial's call 1 ok and its call 2 returned `provider_error` (`pilot-run.txt`, `pilot-report.json`, `pilot-trials.jsonl`, `pilot-stop.json`). Usage ledger and logical ledger agree (reserved = completed for every case).
- [ ] Development run (14 remaining cases): NOT RUN. The root account closed the campaign after the non-ok attempt and the stop rule forbids a replay.
- [ ] Quality numbers, latency percentiles over the full split, README wording: NOT PRODUCED. `framework-quality-metrics` stays `PENDING` and its evidence line states the stop.
- Tests for the grader and executor were authored before the code this time and the red run is recorded; the tests were adjusted twice afterwards only to fix two wrong fixtures (the Core trace keeps the escalation reason, not the classifier summary), not to weaken a check.
