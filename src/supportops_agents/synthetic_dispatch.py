"""Durable, fixture-only read dispatcher; adapters are injected by the caller."""

from __future__ import annotations

import json
import re
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Callable


class DispatchBlocked(RuntimeError):
    """A fixed, non-sensitive refusal at the dispatch boundary."""


class SyntheticDispatcher:
    """Execute at most two allowlisted synthetic reads once per durable run ID."""

    def __init__(self, path: Path, adapters: dict[str, Callable[[dict], str]]):
        if not adapters or set(adapters) - {"search_knowledge", "lookup_billing"}:
            raise DispatchBlocked("invalid_adapters")
        if any(not callable(adapter) for adapter in adapters.values()):
            raise DispatchBlocked("invalid_adapters")
        self.path = path
        self.adapters = dict(adapters)
        with self._connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, request TEXT NOT NULL, result TEXT)")

    @contextmanager
    def _connect(self):
        db = sqlite3.connect(self.path, timeout=5)
        try:
            db.execute("PRAGMA synchronous=FULL")
            with db:
                yield db
        finally:
            db.close()

    def run(self, run_id: str, plan: list[str], context: dict) -> list[str]:
        if not isinstance(run_id, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", run_id):
            raise DispatchBlocked("invalid_run")
        if (not isinstance(plan, list) or not 1 <= len(plan) <= 2
                or any(not isinstance(name, str) or name not in self.adapters for name in plan)
                or len(set(plan)) != len(plan)):
            raise DispatchBlocked("invalid_plan")
        if (not isinstance(context, dict) or set(context) != {"tenant"}
                or not isinstance(context["tenant"], str)
                or not re.fullmatch(r"fixture-[A-Za-z0-9_-]{1,48}", context["tenant"])):
            raise DispatchBlocked("invalid_synthetic_context")
        request = json.dumps({"plan": plan, "context": context}, sort_keys=True)
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT request, result FROM runs WHERE id=?", (run_id,)).fetchone()
            if row is not None:
                if row[0] != request or row[1] is None:
                    raise DispatchBlocked("mismatch_or_unknown_work")
                return json.loads(row[1])
            db.execute("INSERT INTO runs(id, request) VALUES(?, ?)", (run_id, request))
        try:
            results = [self.adapters[name](dict(context)) for name in plan]
            if any(not isinstance(item, str) or len(item) > 4096 for item in results):
                raise ValueError("invalid synthetic result")
        except Exception:
            raise DispatchBlocked("unknown_work") from None
        with self._connect() as db:
            db.execute("UPDATE runs SET result=? WHERE id=? AND result IS NULL", (json.dumps(results), run_id))
        return results
