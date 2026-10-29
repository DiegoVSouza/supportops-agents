"""Finalize the stopped diagnostic conservatively, retaining its full charge."""
import json
import sqlite3
import sys
from contextlib import closing
from pathlib import Path

project = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project))
from scripts.campaign_ledger import CampaignLedger

path = project / "artifacts/evals/live/ledger.sqlite"
provider = project / "artifacts/evals/live/provider-usage.sqlite"
with closing(sqlite3.connect(provider.resolve().as_uri() + "?mode=ro", uri=True)) as db:
    assert db.execute("SELECT COUNT(*) FROM usage_events").fetchone()[0] == 4
    assert db.execute("SELECT COUNT(*) FROM usage_events WHERE campaign='local-diagnostic-v1'").fetchone()[0] == 0
original = CampaignLedger(path, campaign_id="local-operation-v1", read_only=True).reserved_trials()
with closing(sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)) as db:
    assert db.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 3
ledger = CampaignLedger(path, campaign_id="local-diagnostic-v1")
rows = ledger.reserved_trials()
assert len(rows) == 1 and rows[0]["event"] == "reserved" and rows[0]["case_id"] == "fixture-diagnostic-01"
ledger.complete(case_id="fixture-diagnostic-01", trial=1, input_tokens=None, output_tokens=None,
                actual_cost_usd=None, outcome="incomplete", error_class="unknown")
assert CampaignLedger(path, campaign_id="local-operation-v1", read_only=True).reserved_trials() == original
totals = ledger.totals()
assert totals["requests"] == 8 and totals["input_tokens"] == 16384 and totals["output_tokens"] == 2048
report = {"status": "PASS_CONSERVATIVE_STOP_RECONCILIATION", "diagnostic_result": "INCOMPLETE",
          "diagnostic_provider_calls": 0, "original_provider_calls": 2,
          "original_logical_history_unchanged": True, "reserved_calls_retained": 8,
          "reserved_input_tokens_retained": 16384, "reserved_output_tokens_retained": 2048,
          "provider_accessed": False, "credentials_read": False, "replay_allowed": False,
          "logical_events": ledger.reserved_trials()}
(Path(__file__).resolve().parent / "stop-reconciled.json").write_text(json.dumps(report, indent=2) + "\n", newline="\n")
print(json.dumps({key: value for key, value in report.items() if key != "logical_events"}))
