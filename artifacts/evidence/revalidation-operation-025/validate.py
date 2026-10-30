"""Run P01's locked full fake gate in an isolated committed-source snapshot."""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[3]
LAB = PROJECT.parents[1]
OUT = Path(__file__).resolve().parent
WORK = OUT / "snapshot-current" / "lab" / "projects" / "p01"
ARCHIVE = OUT / "source-current.tar"
PROTECTED = (
    "artifacts/evidence/check-fast.txt",
    "artifacts/evidence/check-full.txt",
    "artifacts/runs/latest/results.json",
)
OVERLAY = (
    "evals/live-execution.json",
    "scripts/revalidation_operation.py",
    "src/supportops_agents/accounted_live.py",
    "tests/test_accounted_core.py",
    "tests/test_revalidation_operation.py",
)
ROOT_OVERLAY = (
    "scripts/harness/live_free_account.py",
    "scripts/harness/live_provider_transport.py",
    "scripts/harness/migrate_p01_p04_revalidation.py",
    "shared/policies/groq-free-campaign.json",
    ".planning/llm-live-readiness/phases/039-p01-p04-reviewed-revalidation/AUTHORIZATION.json",
)

if WORK.exists():
    raise SystemExit("fresh isolated snapshot required")
WORK.mkdir(parents=True)
before = {
    name: hashlib.sha256((PROJECT / name).read_bytes()).hexdigest()
    for name in PROTECTED
}
records = []


def run(command, cwd, env):
    result = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        timeout=300,
    )
    records.append(
        {
            "command": command,
            "cwd": str(cwd),
            "exit_code": result.returncode,
            "output": result.stdout + result.stderr,
        }
    )
    return result.returncode


archive_result = run(
    ["git", "archive", "HEAD", "--format=tar", "--output", str(ARCHIVE)],
    PROJECT,
    dict(os.environ),
)
if archive_result:
    raise SystemExit(archive_result)
with tarfile.open(ARCHIVE) as source:
    source.extractall(WORK, filter="data")

root = WORK.parents[1]
for name in OVERLAY:
    target = WORK / name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(PROJECT / name, target)
for name in ROOT_OVERLAY:
    target = root / name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(LAB / name, target)

env = dict(
    os.environ,
    LLM_MODE="fake",
    PYTHONPATH=str(WORK / "src"),
    PYTHONIOENCODING="utf-8",
)
try:
    code = run([sys.executable, "scripts/check_full.py"], WORK, env)
finally:
    after = {
        name: hashlib.sha256((PROJECT / name).read_bytes()).hexdigest()
        for name in PROTECTED
    }
    preserved = before == after
    (OUT / "snapshot-preservation.json").write_text(
        json.dumps({"before": before, "after": after, "unchanged": preserved}, indent=2)
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    (OUT / "snapshot-commands.json").write_text(
        json.dumps(records, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    if not preserved:
        raise SystemExit("protected project outputs changed")

summary = {
    "status": "PASS" if code == 0 else "FAIL",
    "exit_code": code,
    "snapshot_only": True,
    "provider_accessed": False,
    "protected_outputs_unchanged": True,
    "root_policy_sha256": "f8428a8da06fd551e6a41d3d009db69d1d31c620eda68ef21a02ff1dbcc32cdf",
}
(OUT / "snapshot-result.json").write_text(
    json.dumps(summary, indent=2) + "\n", encoding="utf-8", newline="\n"
)
print(json.dumps(summary, sort_keys=True))
raise SystemExit(code)
