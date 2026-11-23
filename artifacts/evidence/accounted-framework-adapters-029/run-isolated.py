"""Run the project's checks in a disposable source snapshot, preserving dirty evidence."""
from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile

root = Path(__file__).resolve().parents[3]
out = Path(__file__).resolve().parent
tracked = subprocess.run(["git", "ls-files", "-z"], cwd=root, capture_output=True, check=True).stdout.decode("utf-8").split("\0")
extra = ["src/supportops_agents/accounted_frameworks.py", "tests/test_accounted_frameworks.py"]
with tempfile.TemporaryDirectory(prefix="p01-framework-check-") as temporary:
    lab_snapshot = Path(temporary)
    snapshot = lab_snapshot / "projects" / "p01"
    snapshot.mkdir(parents=True)
    for name in set(tracked + extra):
        if not name:
            continue
        source = root / name
        if source.is_file():
            destination = snapshot / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
    for name in ("scripts/harness/live_free_account.py", "scripts/harness/live_provider_transport.py", "shared/policies/groq-free-campaign.json"):
        source = root.parents[1] / name
        destination = lab_snapshot / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    env = os.environ.copy()
    env["LLM_MODE"] = "fake"
    env["PYTHONIOENCODING"] = "utf-8"
    for script in ("scripts/check_fast.py", "scripts/check_full.py"):
        command = [sys.executable, script]
        result = subprocess.run(command, cwd=snapshot, env=env, text=True, encoding="utf-8", errors="replace", capture_output=True)
        log = "command=" + " ".join(command) + "\nworking_directory=isolated source snapshot\nexit_code=" + str(result.returncode) + "\n" + result.stdout + result.stderr
        (out / (Path(script).stem + "-attempt2.txt")).write_text(log, encoding="utf-8")
        print(script, "exit", result.returncode, flush=True)
        if result.returncode:
            sys.exit(result.returncode)
