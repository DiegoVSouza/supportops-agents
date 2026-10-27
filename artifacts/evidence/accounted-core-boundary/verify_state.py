"""Offline inventory and finite-envelope dry-run; no provider or credential imports."""

import json
import sqlite3
from contextlib import closing
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[3]
LAB = PROJECT.parents[1]
policy = json.loads((LAB / "shared/policies/groq-free-campaign.json").read_text())
registry = json.loads((LAB / ".runtime/llm-live-readiness/ledger-references.json").read_text())
owner = json.loads((PROJECT / "evals/live-execution.json").read_text())
dataset = json.loads((PROJECT / "evals/datasets/live-v1/manifest.json").read_text())
assert owner["execution_enabled"] is False and owner["approved_campaigns"] == []
assert owner["allocations"] == {}
assert "p01" not in registry["projects"]
assert not (PROJECT / "artifacts/evals/live/provider-usage.sqlite").exists()
totals = []
for project in registry["projects"]:
    path = LAB / "projects" / project / "artifacts/evals/live/provider-usage.sqlite"
    with closing(sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)) as db:
        totals.append(db.execute("SELECT COUNT(DISTINCT attempt_id) FROM usage_events").fetchone()[0])
before = set((PROJECT / "artifacts/evidence/accounted-core-boundary/docker-before.txt").read_text().splitlines())
after = set((PROJECT / "artifacts/evidence/accounted-core-boundary/docker-after.txt").read_text().splitlines())
assert before == after
caps = policy["projects"]["p01"]
assert caps["requests"] == 984
assert caps["input_tokens"] == 2015232 and caps["output_tokens"] == 251904
stages = {}
for stage, cases, trials in (("pilot",6,1),("development",18,3),("holdout",42,3),("protected_confirmation",20,3)):
    workflows = cases * trials
    calls = workflows * 4
    stages[stage] = {"unique_cases":cases,"trials_per_case":trials,"workflow_trials":workflows,"maximum_provider_calls":calls,"planned_batches":(workflows+1)//2,"workflow_trials_per_batch":2,"maximum_provider_calls_per_batch":8}
assert sum(stage["maximum_provider_calls"] for stage in stages.values()) == 984
assert dataset["split_counts"] == {"development":18,"holdout":42}
report = {
    "mode":"offline_dry_run", "provider_accessed":False,"credentials_read":False,
    "candidate":"PENDING_FINAL_COMMIT_FREEZE_AND_DISPATCH_PHASE",
    "campaign":"NONE_ALLOCATED", "runner":"actual Core supervisor loop",
    "stages":stages,
    "primary_capacity":{"calls":744,"input_tokens":1523712,"output_tokens":190464,"economic_estimate_usd":"0.1714176"},
    "protected_confirmation":{"calls":240,"input_tokens":491520,"output_tokens":61440,"economic_estimate_usd":"0.055296"},
    "p01_provider_calls":0,"account_guard_recorded_attempts":sum(totals),
    "p01_provider_ledger_exists":False,"p01_registered":False,
    "unknown_prior_account_usage":"P00 unknown reservation remains intact; see owning P00 accounting.json; do not add logical/provider ledgers",
    "extra_corrections_judges_canary":"NOT_ALLOCATED",
    "paid_authorization_usd":"0.00","actual_billed_usd":None,"current_daily_provider_quota":"UNKNOWN",
    "dataset_rubric_human_independent_review":"PENDING",
    "external_tools_and_effect_executor":"NOT_IMPLEMENTED; do not infer retrieval or financial effects from worker contexts",
    "docker_identities_unchanged":True,
    "stop_conditions":["execution disabled","no frozen candidate/campaign allocation","missing durable full campaign dispatcher","provider/resource/provenance error or uncertain work"],
    "safe_next_command":"uv run --locked python scripts/run_live_campaign.py --stage pilot --dry-run",
    "live_resume_command":None,"status":"INCOMPLETE",
}
print(json.dumps(report,indent=2))
