import hashlib
import json
import sqlite3
import sys
from contextlib import closing
from pathlib import Path

project = Path(__file__).resolve().parents[3]
lab = project.parents[1]
sys.path.insert(0, str(lab / "scripts/harness"))
from live_free_account import machine_lease

with machine_lease(lab / ".runtime/llm-live-readiness/campaign.lock"):
    events = []
    for name, query in (
        ("logical", "SELECT campaign_id,case_id,trial,event,reserved_calls,reserved_input_tokens,reserved_output_tokens,outcome,error_class FROM events ORDER BY sequence"),
        ("provider", "SELECT campaign,case_id,trial,call_index,event,status,actual_input,actual_output FROM usage_events ORDER BY ordinal"),
    ):
        path = project / ("artifacts/evals/live/ledger.sqlite" if name == "logical" else "artifacts/evals/live/provider-usage.sqlite")
        with closing(sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)) as db:
            db.row_factory = sqlite3.Row
            events.append((name, [dict(row) for row in db.execute(query)]))
    manifest = project / "artifacts/evals/live/local-operation-v1/manifest.json"
    report = {"status": "INCOMPLETE", "campaign_lease": "acquired_no_live_holder", "manifest_sha256": hashlib.sha256(manifest.read_bytes()).hexdigest(), "logical": dict(events)["logical"], "provider": dict(events)["provider"], "failure_reason": "NOT_PRESERVED", "provider_accessed": False, "credentials_read": False}
(Path(__file__).resolve().parent / "interruption-inspection.json").write_text(json.dumps(report, indent=2) + "\n", newline="\n")
print(json.dumps(report, indent=2))
