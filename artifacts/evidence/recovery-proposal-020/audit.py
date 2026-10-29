"""Read-only audit and disabled diagnostic recovery proposal; no provider imports."""
import hashlib
import json
import sqlite3
import subprocess
from contextlib import closing
from pathlib import Path

project = Path(__file__).resolve().parents[3]
out = Path(__file__).resolve().parent
protected = ["artifacts/evidence/check-fast.txt", "artifacts/evidence/check-full.txt", "artifacts/runs/latest/results.json"]
before = {p: hashlib.sha256((project / p).read_bytes()).hexdigest() for p in protected}


def rows(name, table):
    path = (project / "artifacts/evals/live" / name).resolve()
    with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)) as db:
        db.row_factory = sqlite3.Row
        return [dict(row) for row in db.execute("SELECT * FROM " + table + " ORDER BY sequence")]


logical = rows("ledger.sqlite", "events")
provider = rows("provider-usage.sqlite", "usage_events")
assert len(logical) == 2
assert [row["event"] for row in logical] == ["reserved", "completed"]
assert all(row["campaign_id"] == "local-operation-v1" and row["case_id"] == "fixture-local-01" and row["trial"] == 1 for row in logical)
assert all((row["reserved_calls"], row["reserved_input_tokens"], row["reserved_output_tokens"], row["reserved_cost_usd"]) == (4, 8192, 1024, "0.0009216") for row in logical)
assert logical[-1]["outcome"] == "incomplete" and logical[-1]["error_class"] == "unknown"
assert all(logical[-1][key] is None for key in ("actual_input_tokens", "actual_output_tokens", "actual_cost_usd"))
assert len(provider) == 4 and all(row["campaign"] == "local-operation-v1" and row["case_id"] == "fixture-local-01" and row["trial"] == 1 for row in provider)
completed = [row for row in provider if row["event"] == "completed"]
assert [(row["call_index"], row["status"], row["actual_input"], row["actual_output"]) for row in completed] == [(1, "ok", 235, 46), (2, "ok", 228, 183)]
manifest_path = project / "artifacts/evals/live/local-operation-v1/manifest.json"
manifest = json.loads(manifest_path.read_text())
assert manifest["candidate_commit"] == "d17923e0c8fe5992ebac8e25b994e746e9f25ba2"
proposal = {
    "status": "REVIEW_REQUIRED", "execution_enabled": False,
    "original_workflow": "local-operation-v1/fixture-local-01/1",
    "original_candidate": manifest["candidate_commit"],
    "original_manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
    "original_result": "INCOMPLETE", "original_failure_category": "unknown_unrecoverable",
    "original_reserved_calls_retained": 4, "original_reserved_input_tokens_retained": 8192,
    "original_reserved_output_tokens_retained": 1024,
    "observed_provider_calls": 2, "observed_provider_input": 463, "observed_provider_output": 229,
    "observed_receipts": [row["attempt_id"] for row in completed],
    "proposed_scope": "one separately reviewed diagnostic workflow, never replacement of original result",
    "proposed_max_calls": 4, "proposed_max_input_tokens": 8192, "proposed_max_output_tokens": 1024,
    "conservative_total_logical_calls": 8, "maximum_total_observed_provider_calls": 6,
    "existing_operating_call_ceiling": 8, "additional_funding_required": False,
    "authorized_paid_usd": 0, "actual_billed_usd": None,
    "prerequisites": ["explicit user acceptance of unrecoverable original diagnostic and separate diagnostic scope",
                      "disabled-by-default reviewed exception bound to original receipts and retained reservation",
                      "offline regression and isolated full gate of exception controls",
                      "new immutable corrected source/manifest binding; original manifest unchanged",
                      "single invocation; preserve all outcomes and stop after success or any error; no automatic replay"],
    "quality_human_holdout_promotion": "PENDING", "provider_accessed": False, "credentials_read": False,
}
assert proposal["conservative_total_logical_calls"] <= proposal["existing_operating_call_ceiling"]
assert proposal["maximum_total_observed_provider_calls"] <= proposal["existing_operating_call_ceiling"]
(out / "proposal.json").write_text(json.dumps(proposal, indent=2) + "\n", newline="\n")
after = {p: hashlib.sha256((project / p).read_bytes()).hexdigest() for p in protected}
assert before == after
(out / "preservation.json").write_text(json.dumps({"before": before, "after": after, "unchanged": True}, indent=2) + "\n", newline="\n")
print(json.dumps({"status": "PASS_READ_ONLY_AUDIT", "proposal_status": proposal["status"], "original_reservation_retained": True,
                  "provider_calls": 2, "recovery_dispatched": False, "protected_outputs_unchanged": True}))
