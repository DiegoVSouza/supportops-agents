import json
import sqlite3
from contextlib import closing
from pathlib import Path

project = Path(__file__).resolve().parents[3]
path = project / "artifacts/evals/live/provider-usage.sqlite"
with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)) as db:
    rows = db.execute("SELECT campaign,case_id,trial,call_index,event,status,actual_input,actual_output,typeof(call_index),typeof(actual_input),typeof(actual_output) FROM usage_events ORDER BY ordinal").fetchall()
    filtered = db.execute("SELECT call_index,event,status,actual_input,actual_output FROM usage_events WHERE campaign=? AND case_id=? AND trial=1 ORDER BY ordinal", ("local-operation-v1", "fixture-local-01")).fetchall()
report = {"cwd": str(project), "command": "python inspect-provider-shape.py", "exit_code": 0, "rows": rows, "filtered": filtered, "provider_accessed": False}
(Path(__file__).resolve().parent / "provider-shape-filtered.json").write_text(json.dumps(report, indent=2) + "\n", newline="\n")
print(json.dumps(report, indent=2))
