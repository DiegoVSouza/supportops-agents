"""Run owning fast/full gates in a fresh committed snapshot, preserving user output."""
import hashlib
import json
import os
import subprocess
import sys
import tarfile
from pathlib import Path

project = Path(__file__).resolve().parents[3]
out = Path(__file__).resolve().parent
work = out / "snapshot-protocol" / "lab" / "projects" / "p01"
assert not work.exists(), "fresh snapshot required"
work.mkdir(parents=True)
archive = out / "source-protocol.tar"
protected = ["artifacts/evidence/check-fast.txt", "artifacts/evidence/check-full.txt", "artifacts/runs/latest/results.json"]
before = {p: hashlib.sha256((project / p).read_bytes()).hexdigest() for p in protected}
env = dict(os.environ, LLM_MODE="fake", PYTHONPATH=str(work / "src"))
records = []


def run(command, cwd):
    result = subprocess.run(command, cwd=cwd, env=env, text=True, capture_output=True, timeout=240)
    records.append({"command": command, "cwd": str(cwd), "exit_code": result.returncode,
                    "output": result.stdout + result.stderr})
    (out / "snapshot-commands-protocol.json").write_text(json.dumps(records, indent=2) + "\n", newline="\n")
    return result.returncode


code = run(["git", "archive", "HEAD", "--format=tar", "--output", str(archive)], project)
assert code == 0
with tarfile.open(archive) as source:
    source.extractall(work, filter="data")
shared = work.parents[1] / "scripts/harness"
shared.mkdir(parents=True)
for name in ("live_provider_transport.py", "live_free_account.py"):
    (shared / name).write_bytes((project.parents[1] / "scripts/harness" / name).read_bytes())
try:
    code = run([sys.executable, "scripts/check_full.py"], work)
finally:
    after = {p: hashlib.sha256((project / p).read_bytes()).hexdigest() for p in protected}
    (out / "snapshot-preservation-protocol.json").write_text(json.dumps({"before": before, "after": after, "unchanged": before == after}, indent=2) + "\n", newline="\n")
    assert before == after
print(json.dumps({"exit_code": code, "protected_outputs_unchanged": True, "snapshot_only": True}))
sys.exit(code)
