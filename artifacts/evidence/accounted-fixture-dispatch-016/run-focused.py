import json
import os
import subprocess
import sys
from pathlib import Path

project = Path(__file__).resolve().parents[3]
env = dict(os.environ, LLM_MODE="fake")
command = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_core_fixture_dispatch.py"]
result = subprocess.run(command, cwd=project, env=env, capture_output=True, text=True, timeout=90)
report = {"command": " ".join(command), "cwd": str(project), "exit_code": result.returncode, "output": result.stdout + result.stderr}
(Path(__file__).resolve().parent / "focused-attempt2.json").write_text(json.dumps(report, indent=2) + "\n", newline="\n")
print(report["output"])
sys.exit(result.returncode)
