"""Run the P01 fake gate on an isolated snapshot with the phase027 overlay."""
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
LAB = PROJECT.parents[1]
WORK = OUT / "full-snapshot-attempt3/lab/projects/p01"
ARCHIVE = OUT / "full-source-attempt3.tar"
OVERLAY = ("scripts/reviewed_operation_027.py", "tests/test_reviewed_operation_027.py",
           "src/supportops_agents/accounted_live.py", "evals/live-execution.json")
ROOT_OVERLAY = ("scripts/harness/live_free_account.py", "scripts/harness/live_provider_transport.py",
                "scripts/harness/migrate_p01_p04_revalidation.py",
                "shared/policies/groq-free-campaign.json",
                ".planning/llm-live-readiness/phases/039-p01-p04-reviewed-revalidation/AUTHORIZATION.json")
PROTECTED = ("artifacts/evidence/check-fast.txt", "artifacts/evidence/check-full.txt",
             "artifacts/runs/latest/results.json")
if WORK.exists() or ARCHIVE.exists():
    raise SystemExit("fresh full snapshot required")
before = {p: hashlib.sha256((PROJECT / p).read_bytes()).hexdigest() for p in PROTECTED}
WORK.mkdir(parents=True)
archive = subprocess.run(["git", "archive", "HEAD", "-o", str(ARCHIVE)], cwd=PROJECT,
                         capture_output=True, text=True)
if archive.returncode:
    raise SystemExit("snapshot archive failed")
with tarfile.open(ARCHIVE) as source:
    source.extractall(WORK, filter="data")
for base, dest, paths in ((PROJECT, WORK, OVERLAY), (LAB, WORK.parents[1], ROOT_OVERLAY)):
    for name in paths:
        target = dest / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(base / name, target)
env = dict(os.environ, LLM_MODE="fake", PYTHONPATH=str(WORK / "src"),
           PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
command = [sys.executable, "scripts/check_full.py"]
try:
    result = subprocess.run(command, cwd=WORK, env=env, capture_output=True,
                            encoding="utf-8", errors="replace", timeout=300)
    record = {"exit_code": result.returncode, "output": result.stdout + result.stderr}
except Exception as exc:
    record = {"exit_code": None, "error_type": type(exc).__name__}
after = {p: hashlib.sha256((PROJECT / p).read_bytes()).hexdigest() for p in PROTECTED}
record.update(command=command, cwd=str(WORK), protected_before=before,
              protected_after=after, provider_accessed=False)
(OUT / "full-attempt3.json").write_text(json.dumps(record, indent=2) + "\n",
                                         encoding="utf-8", newline="\n")
print(json.dumps({"exit_code": record["exit_code"], "protected_unchanged": before == after}))
raise SystemExit(record["exit_code"] if record["exit_code"] is not None and before == after else 2)
