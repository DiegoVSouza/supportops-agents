#!/usr/bin/env python3
"""Run repeatable fast checks and save command/output/exit status."""
import os
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "artifacts" / "evidence" / "check-fast.txt"


def main() -> int:
    os.environ.setdefault("LLM_MODE", "fake")
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    os.environ["PYTHONPATH"] = str(ROOT / "src") + os.pathsep + os.environ.get("PYTHONPATH", "")
    commands = [
        [sys.executable, "-m", "compileall", "-q", "src", "tests"],
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
    ]
    sections = []
    exit_code = 0
    for command in commands:
        result = subprocess.run(command, cwd=ROOT, text=True, encoding="utf-8", errors="replace",
                                capture_output=True, env=os.environ.copy())
        sections.append(f"command={' '.join(command)}\nexit_code={result.returncode}\n{result.stdout}{result.stderr}")
        exit_code = result.returncode
        if result.returncode:
            break
    EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE.write_text("\n\n".join(sections), encoding="utf-8")
    print("\n\n".join(sections))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
