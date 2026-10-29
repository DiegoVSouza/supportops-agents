import json
import os
import subprocess
import sys
from pathlib import Path

project = Path(__file__).resolve().parents[3]
command = [sys.executable, "-m", "scripts.local_operation", "--request-id", "fixture-local-01"]
result = subprocess.run(command, cwd=project, env=dict(os.environ, LLM_MODE="live"), capture_output=True, text=True, timeout=140)
try:
    payload = json.loads(result.stdout)
    safe = {name: payload[name] for name in ("status", "reason", "stop_reason", "calls") if name in payload}
except (TypeError, ValueError):
    safe = {"status": "INCOMPLETE", "reason": "unparseable_output"}
report = {"command": "LLM_MODE=live python -m scripts.local_operation --request-id fixture-local-01", "cwd": str(project), "exit_code": result.returncode, "result": safe, "stdout_redacted": True, "stderr_redacted": True}
(Path(__file__).resolve().parent / "live-smoke-attempt1.json").write_text(json.dumps(report, indent=2) + "\n", newline="\n")
print(json.dumps(report, indent=2))
sys.exit(result.returncode)
