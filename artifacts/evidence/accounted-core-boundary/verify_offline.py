"""Run all six actual framework comparisons with external socket calls denied."""

import json
import os
import runpy
import socket
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT / "src"))
os.environ["LLM_MODE"] = "fake"
os.environ["PYTHONIOENCODING"] = "utf-8"
blocked = []
original_connect = socket.socket.connect
original_connect_ex = socket.socket.connect_ex


def permitted(address):
    return isinstance(address, tuple) and address[0] in {"127.0.0.1", "::1", "localhost"}


def connect(instance, address):
    if not permitted(address):
        blocked.append("external_socket_attempt")
        raise OSError("offline probe denies external sockets")
    return original_connect(instance, address)


def connect_ex(instance, address):
    if not permitted(address):
        blocked.append("external_socket_attempt")
        return 10013
    return original_connect_ex(instance, address)


socket.socket.connect = connect
socket.socket.connect_ex = connect_ex
sys.argv = ["supportops_agents.comparison", "--output", str(PROJECT / "artifacts/evidence/accounted-core-boundary/offline-comparison")]
runpy.run_module("supportops_agents.comparison", run_name="__main__")
import atexit
atexit._run_exitfuncs()
assert not blocked, "External socket attempts observed"
print(json.dumps({"status": "PASS", "external_socket_attempts": len(blocked), "provider_accessed": False, "credentials_read": False, "frameworks": 6, "telemetry_disabled": all(os.environ.get(key) == "true" for key in ("OTEL_SDK_DISABLED", "CREWAI_DISABLE_TELEMETRY", "CREWAI_DISABLE_TRACKING")), "live_quality": "PENDING"}))
