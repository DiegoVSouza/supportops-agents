"""Validate planning in a fresh P01 snapshot and preserve user outputs."""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

OUT = Path(__file__).resolve().parent
PROJECT = OUT.parents[2]
SNAPSHOT = OUT / "planning-snapshot-2" / "lab" / "projects" / "p01"
ARCHIVE = OUT / "planning-source-2.tar"
PROTECTED = ("artifacts/evidence/check-fast.txt", "artifacts/evidence/check-full.txt",
             "artifacts/runs/latest/results.json")
if SNAPSHOT.exists() or ARCHIVE.exists():
    raise SystemExit("planning snapshot already exists")
before = {p: hashlib.sha256((PROJECT / p).read_bytes()).hexdigest() for p in PROTECTED}
archive = subprocess.run(["git", "archive", "HEAD", "-o", str(ARCHIVE)], cwd=PROJECT,
                         capture_output=True, text=True)
if archive.returncode:
    raise SystemExit("git archive failed")
SNAPSHOT.mkdir(parents=True)
with tarfile.open(ARCHIVE) as source:
    source.extractall(SNAPSHOT, filter="data")
lab = PROJECT.parents[1]
snapshot_lab = SNAPSHOT.parents[1]
for name in ("live_provider_transport.py", "live_free_account.py"):
    target = snapshot_lab / "scripts/harness" / name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(lab / "scripts/harness" / name, target)
env = dict(os.environ, LLM_MODE="fake", PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
command = [sys.executable, "scripts/check_fast.py"]
result = subprocess.run(command, cwd=SNAPSHOT, env=env, capture_output=True,
                        encoding="utf-8", errors="replace", timeout=300)
after = {p: hashlib.sha256((PROJECT / p).read_bytes()).hexdigest() for p in PROTECTED}
record = {"command": command, "cwd": str(SNAPSHOT), "exit_code": result.returncode,
          "output": result.stdout + result.stderr, "protected_before": before,
          "protected_after": after, "provider_accessed": False}
(OUT / "planning-check-attempt2.json").write_text(json.dumps(record, indent=2) + "\n",
                                          encoding="utf-8", newline="\n")
print(json.dumps({"exit_code": result.returncode, "protected_unchanged": before == after}))
raise SystemExit(result.returncode if before == after else 2)
