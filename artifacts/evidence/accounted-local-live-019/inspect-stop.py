import json
import sqlite3
from contextlib import closing
from pathlib import Path

project = Path(__file__).resolve().parents[3]
report = {"logical_events": [], "provider_events": [], "provider_accessed": "UNKNOWN"}
for key, relative, query in (
    ("logical_events", "artifacts/evals/live/ledger.sqlite", "SELECT campaign_id,case_id,trial,event,reserved_calls,reserved_input_tokens,reserved_output_tokens,outcome,error_class FROM events ORDER BY sequence"),
    ("provider_events", "artifacts/evals/live/provider-usage.sqlite", "SELECT campaign,case_id,trial,call_index,event,status,reserved_input,reserved_output,actual_input,actual_output FROM usage_events ORDER BY ordinal"),
):
    path = project / relative
    if path.exists():
        with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)) as db:
            db.row_factory = sqlite3.Row
            report[key] = [dict(row) for row in db.execute(query)]
report["provider_accessed"] = bool(report["provider_events"])
(Path(__file__).resolve().parent / "stop-ledger.json").write_text(json.dumps(report, indent=2) + "\n", newline="\n")
print(json.dumps(report, indent=2))
