import json
import sys
from pathlib import Path

project = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project))
from scripts.campaign_ledger import CampaignLedger

ledger = CampaignLedger(project / "artifacts/evals/live/ledger.sqlite", campaign_id="local-operation-v1", read_only=True)
events = ledger.reserved_trials()
totals = ledger.totals()
assert len(events) == 2 and events[-1]["event"] == "completed" and events[-1]["outcome"] == "incomplete"
assert events[-1]["error_class"] == "unknown" and events[-1]["actual_input_tokens"] is None and events[-1]["actual_output_tokens"] is None
assert totals["requests"] == 4 and totals["input_tokens"] == 8192 and totals["output_tokens"] == 1024
report = {"status": "PASS_CONSERVATIVE_RECONCILIATION", "cwd": str(project), "command": "uv run --locked python artifacts/evidence/accounted-local-live-019/verify-reconciliation.py", "exit_code": 0, "events": events, "totals": {name: str(value) for name, value in totals.items()}, "provider_accessed": False, "credentials_read": False}
(Path(__file__).resolve().parent / "reconciliation-verified.json").write_text(json.dumps(report, indent=2) + "\n", newline="\n")
print(json.dumps(report, indent=2))
