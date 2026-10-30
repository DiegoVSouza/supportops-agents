"""Check current finite P01 authorization without dispatch or secret output."""
import json
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parent
PROJECT = OUT.parents[2]
LAB = PROJECT.parents[1]
sys.path.insert(0, str(LAB / "scripts/harness"))
from live_free_account import SharedAccount, numbered_key_slots

policy = json.loads((LAB / "shared/policies/groq-free-campaign.json").read_text(encoding="utf-8"))
account = SharedAccount(LAB, policy)
rows = account._history()
account._reviewed_revalidation(rows, "p01", "local-reviewed-operation-027-v1",
                               "fixture-reviewed-operation-027", 1, 1, False)
slots = [slot for slot, _ in numbered_key_slots(LAB)]
paths = [PROJECT / "artifacts/evidence/reviewed-operation-027" / name
         for name in ("attempt.json", "invocation.json", "live-result.json")]
if any(path.exists() or path.is_symlink() for path in paths):
    raise SystemExit("operation identity already used or uncertain")
report = {"status": "PASS", "provider_accessed": False, "credential_slots_present": slots,
          "provider_attempts_before": len(rows), "new_reservation_created": False,
          "paid_authorized_usd": "0.00", "marker_paths_absent": True}
print(json.dumps(report, sort_keys=True))
