"""Fixture-only bridge between framework runners and the accounted Core boundary."""

from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Any, Mapping

from .accounted_live import AccountedCoreClient, BoundaryError, SubprocessGuard, WORKERS, WorkflowBinding
from .contracts import Ticket
from .registry import RUNNER_NAMES, get_runner

_FIELDS = {"ticket", "category", "classification", "kb_context", "billing_context", "response"}


class _OrderedFixtureClient:
    """Serialize the graph's parallel pair without changing their framework scheduling."""

    def __init__(self, client: AccountedCoreClient):
        self.client = client
        self.condition = threading.Condition()
        self.stopped = False

    def complete(self, agent: str, state: Mapping[str, Any]) -> Mapping[str, Any]:
        with self.condition:
            deadline = time.monotonic() + 5
            # Only the parallel graph pair may arrive in reverse order.
            while not self.stopped and agent == "billing_agent" and self.client.started == 1:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    self.stopped = True
                    self.condition.notify_all()
                    raise BoundaryError("worker_order")
                self.condition.wait(remaining)
            if self.stopped:
                raise BoundaryError("workflow_stopped")
            try:
                if self.client.started >= len(WORKERS) or agent != WORKERS[self.client.started]:
                    raise BoundaryError("worker_order")
                clean = {key: value for key, value in state.items() if key in _FIELDS}
                result = self.client.complete(agent, clean)
                self.condition.notify_all()
                return result
            except BaseException:
                self.stopped = True
                self.condition.notify_all()
                raise


def run_fixture(name: str, case: dict[str, Any], transport: Any, workdir: Path):
    """Run a synthetic case; refuse live transports and never allocate a campaign."""
    if name not in RUNNER_NAMES[1:] or getattr(transport, "provenance", None) != "fixture":
        raise ValueError("framework and fixture transport required")
    runner = get_runner(name)
    if name == "langgraph":
        runner.checkpoint_path = workdir / "framework-checkpoint.sqlite"
    binding = WorkflowBinding("fixture-framework-029", case["case_id"], 1)
    client = AccountedCoreClient(transport, binding)
    ticket = Ticket(case["case_id"], "Synthetic support request", case["input"])
    try:
        result = runner.run(ticket, llm=_OrderedFixtureClient(client), max_steps=4)
        return result, list(client.receipts)
    finally:
        client.close()


def run_live(name: str, case: dict[str, Any], project: Path, binding: WorkflowBinding):
    """Execute one framework workflow only through the sealed P01 subprocess guard."""
    if name not in RUNNER_NAMES[1:] or binding.campaign_id != "p01-framework-smoke-v1":
        raise ValueError("framework smoke binding required")
    guard = SubprocessGuard(binding, project=project)
    client = AccountedCoreClient(guard, binding, project=project)
    try:
        runner = get_runner(name, allow_live=True)
        if name == "langgraph":
            checkpoint_dir = project / "artifacts/evals/live" / binding.campaign_id / "checkpoints"
            checkpoint_dir.mkdir(parents=True, exist_ok=True)
            runner.checkpoint_path = checkpoint_dir / f"{binding.case_id}.sqlite"
        ticket = Ticket(case["case_id"], "Synthetic support request", case["input"])
        result = runner.run(ticket, llm=_OrderedFixtureClient(client), max_steps=4)
        return result, list(client.receipts)
    finally:
        client.close()
