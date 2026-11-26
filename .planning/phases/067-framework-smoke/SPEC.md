# Framework Live Smoke

Exercise the five non-Core runners against synthetic development prompts through `SubprocessGuard` and `AccountedCoreClient` only. Each workflow has one trial and reserves four provider calls; the new campaign is capped at five workflows and 20 calls total.

Acceptance requires fake contract coverage for each runner, committed source and root authorization hashes, reconciled project/root ledgers, zero paid spend, and a stop on any uncertain result. The closed Core campaign is not resumed.
