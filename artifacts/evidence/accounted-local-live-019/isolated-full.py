import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

project = Path(__file__).resolve().parents[3]
lab = project.parents[1]
isolated = project / "artifacts/evidence/accounted-local-live-019-tmp/lab/projects/p01"
isolated.mkdir(parents=True, exist_ok=False)
archive = subprocess.run(["git", "archive", "HEAD"], cwd=project, capture_output=True, check=True)
with tarfile.open(fileobj=io.BytesIO(archive.stdout)) as payload:
    payload.extractall(isolated, filter="data")
shutil.copytree(lab / "scripts/harness", isolated.parents[1] / "scripts/harness", ignore=shutil.ignore_patterns("__pycache__"))
command = [sys.executable, "scripts/check_full.py"]
result = subprocess.run(command, cwd=isolated, env=dict(os.environ, LLM_MODE="fake", PYTHONIOENCODING="utf-8"), capture_output=True, text=True, timeout=240)
report = {"command": "uv run --locked python scripts/check_full.py (isolated committed snapshot)", "cwd": str(isolated), "source_git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=project, text=True).strip(), "exit_code": result.returncode, "output": result.stdout + result.stderr}
(Path(__file__).resolve().parent / "isolated-full-attempt1.json").write_text(json.dumps(report, indent=2) + "\n", newline="\n")
print("isolated full exit", result.returncode)
sys.exit(result.returncode)
