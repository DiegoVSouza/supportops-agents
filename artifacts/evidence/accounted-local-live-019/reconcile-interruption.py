import hashlib
import json
import subprocess
import sys
from pathlib import Path

project = Path(__file__).resolve().parents[3]
lab = project.parents[1]
sys.path.insert(0, str(project))
sys.path.insert(0, str(lab / "scripts/harness"))
from live_free_account import SharedAccount, machine_lease
from scripts.local_operation import reconcile_interrupted_fixture

manifest = project / "artifacts/evals/live/local-operation-v1/manifest.json"
if hashlib.sha256(manifest.read_bytes()).hexdigest() != "306635c6669bb0806cbfaa4ba6e1e809b7ac30ef54ff70da55ba0faf594ccef1":
    raise SystemExit("manifest_changed")
smoke = json.loads((Path(__file__).resolve().parent / "live-smoke-attempt1.json").read_text())
if smoke.get("exit_code") != 2 or smoke.get("result", {}).get("status") != "INCOMPLETE":
    raise SystemExit("smoke_evidence_changed")
for command in (["git", "ls-files", "--error-unmatch", "--", "scripts/local_operation.py", "artifacts/evals/live/local-operation-v1/manifest.json", "artifacts/evidence/accounted-local-live-019/live-smoke-attempt1.json"], ["git", "diff", "--quiet", "HEAD", "--", "scripts/local_operation.py", "artifacts/evals/live/local-operation-v1/manifest.json", "artifacts/evidence/accounted-local-live-019/live-smoke-attempt1.json"]):
    subprocess.run(command, cwd=project, capture_output=True, check=True, timeout=15)
policy = json.loads((lab / "shared/policies/groq-free-campaign.json").read_text())
SharedAccount(lab, policy).snapshot()
report = reconcile_interrupted_fixture(ledger_path=project / "artifacts/evals/live/ledger.sqlite", provider_path=project / "artifacts/evals/live/provider-usage.sqlite", lease=machine_lease(lab / ".runtime/llm-live-readiness/campaign.lock"))
report.update(command="uv run --locked python artifacts/evidence/accounted-local-live-019/reconcile-interruption.py", cwd=str(project), exit_code=0, provider_accessed=False, credentials_read=False)
(Path(__file__).resolve().parent / "reconciled-interruption.json").write_text(json.dumps(report, indent=2) + "\n", newline="\n")
print(json.dumps(report, indent=2))
