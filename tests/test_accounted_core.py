"""Offline contracts for the actual Core loop and accounted provider boundary."""

import copy
import io
import hashlib
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import Mock, patch

from supportops_agents.accounted_live import (
    PROJECT,
    MODEL,
    AccountedCoreClient,
    BoundaryError,
    SubprocessGuard,
    WorkflowBinding,
    build_payload,
    diagnostic,
    input_bound,
)
from supportops_agents.contracts import Ticket
from supportops_agents.core import CoreTriageRunner, SharedState


class FixtureGuard:
    provenance = "fixture"

    def __init__(self):
        self.requests = []
        self.closed = False
        self.failure = None
        self.override = None
        self.outputs = {
            "classifier": {"category": "billing", "summary": "Review the issue.", "escalate": ""},
            "kb_researcher": {"context": "Verify before promising an outcome."},
            "billing_agent": {"context": "Records are unavailable.", "escalate": ""},
            "responder": {"response": "Please verify the records.", "approved": True},
        }

    def request(self, envelope):
        self.requests.append(copy.deepcopy(envelope))
        if self.failure is not None:
            raise self.failure
        if self.override is not None:
            return copy.deepcopy(self.override)
        worker = json.loads(envelope["payload"]["messages"][1]["content"])["worker"]
        return {
            "status": "ok",
            "model": MODEL,
            "attempt_id": f"{len(self.requests):032x}",
            "usage": {"input_tokens": 20, "output_tokens": 10},
            "latency_ms": 1.5,
            "finish_reason": "stop",
            "tool_calls": [],
            "content": json.dumps(self.outputs[worker], ensure_ascii=False),
        }

    def close(self):
        self.closed = True


class AccountedCoreTests(unittest.TestCase):
    def setUp(self):
        self.binding = WorkflowBinding("fixture-pilot", "fixture-case", 1)
        self.guard = FixtureGuard()
        self.client = AccountedCoreClient(self.guard, self.binding)
        self.ticket = Ticket(
            "fixture-ticket", "Charge question", "Please explain the policy. Ação."
        )

    def test_actual_core_loop_has_four_indexed_receipts_and_no_extra_effects(self):
        result = CoreTriageRunner().run(self.ticket, llm=self.client, max_steps=4)
        self.assertEqual(result.stop_reason, "approved")
        self.assertEqual(
            [step.agent for step in result.trace],
            ["classifier", "kb_researcher", "billing_agent", "responder"],
        )
        self.assertEqual([row["call_index"] for row in self.guard.requests], [1, 2, 3, 4])
        self.assertTrue(
            all(
                (row["campaign_id"], row["case_id"], row["trial"])
                == ("fixture-pilot", "fixture-case", 1)
                for row in self.guard.requests
            )
        )
        self.assertEqual(len(self.client.receipts), 4)
        self.assertTrue(self.guard.closed)
        self.assertTrue(all(row["provenance"] == "fixture" for row in self.client.receipts))
        self.assertTrue(all(input_bound(row["payload"]) <= 2048 for row in self.guard.requests))
        with self.assertRaisesRegex(BoundaryError, "workflow_stopped"):
            self.client.complete("responder", SharedState(self.ticket).as_payload())
        self.assertEqual(len(self.guard.requests), 4)

    def test_early_escalation_stops_actual_core_and_cannot_continue(self):
        self.guard.outputs["classifier"]["escalate"] = "Human safety review required."
        result = CoreTriageRunner().run(self.ticket, llm=self.client, max_steps=4)
        self.assertEqual(result.stop_reason, "escalated")
        self.assertEqual(len(self.guard.requests), 1)
        self.assertTrue(self.guard.closed)
        with self.assertRaisesRegex(BoundaryError, "workflow_stopped"):
            self.client.complete("kb_researcher", SharedState(self.ticket).as_payload())
        self.assertEqual(len(self.guard.requests), 1)

    def test_out_of_order_worker_stops_before_transport(self):
        with self.assertRaisesRegex(BoundaryError, "worker_order"):
            self.client.complete("billing_agent", SharedState(self.ticket).as_payload())
        with self.assertRaisesRegex(BoundaryError, "workflow_stopped"):
            self.client.complete("classifier", SharedState(self.ticket).as_payload())
        self.assertEqual(self.guard.requests, [])

    def test_quota_denial_keeps_only_allowlisted_diagnostics_and_never_retries(self):
        self.guard.override = {
            "status": "INCOMPLETE",
            "reason": "quota",
            "http_status": 429,
            "provider_error_code": "insufficient_quota",
            "attempt_id": "a" * 32,
            "raw_error": "fixture-private-content",
            "headers": {"authorization": "fixture-key"},
        }
        with self.assertRaisesRegex(BoundaryError, "quota"):
            CoreTriageRunner().run(self.ticket, llm=self.client, max_steps=4)
        self.assertEqual(
            self.client.last_failure,
            {
                "reason": "quota",
                "http_status": 429,
                "provider_error_code": "insufficient_quota",
                "attempt_id": "a" * 32,
            },
        )
        self.assertIsNone(self.client.receipts[0]["usage"])
        with self.assertRaisesRegex(BoundaryError, "workflow_stopped"):
            self.client.complete("classifier", SharedState(self.ticket).as_payload())
        self.assertEqual(len(self.guard.requests), 1)

    def test_timeout_and_interrupt_keep_workflow_uncertain_without_replay(self):
        for failure in (TimeoutError("fixture-private-content"), KeyboardInterrupt()):
            guard = FixtureGuard()
            guard.failure = failure
            client = AccountedCoreClient(guard, self.binding)
            expected = (
                KeyboardInterrupt if isinstance(failure, KeyboardInterrupt) else BoundaryError
            )
            with self.subTest(failure=type(failure).__name__), self.assertRaises(expected):
                client.complete("classifier", SharedState(self.ticket).as_payload())
            self.assertEqual(client.last_failure["reason"], "provider_timeout_uncertain")
            with self.assertRaisesRegex(BoundaryError, "workflow_stopped"):
                client.complete("classifier", SharedState(self.ticket).as_payload())
            self.assertEqual(len(guard.requests), 1)

    def test_invalid_worker_contract_is_terminal_not_a_semantic_retry(self):
        self.guard.outputs["classifier"] = {
            "category": "billing",
            "summary": "Valid summary",
            "escalate": "",
            "extra": "not allowed",
        }
        with self.assertRaisesRegex(BoundaryError, "worker_contract"):
            self.client.complete("classifier", SharedState(self.ticket).as_payload())
        self.assertEqual(len(self.client.receipts), 1)
        with self.assertRaisesRegex(BoundaryError, "workflow_stopped"):
            self.client.complete("classifier", SharedState(self.ticket).as_payload())
        self.assertEqual(len(self.guard.requests), 1)

    def test_oversized_or_grading_state_is_rejected_before_transport(self):
        for update in (
            {"response": "\ud800"},
            {"response": "x" * 5000},
            {"expected": {"category": "billing"}},
            {"rubric": "fixture"},
        ):
            guard = FixtureGuard()
            client = AccountedCoreClient(guard, self.binding)
            state = {**SharedState(self.ticket).as_payload(), **update}
            with self.subTest(update=list(update)), self.assertRaises(BoundaryError):
                client.complete("classifier", state)
            self.assertEqual(guard.requests, [])
        payload = build_payload("classifier", SharedState(self.ticket).as_payload())
        content = json.loads(payload["messages"][1]["content"])
        self.assertEqual(set(content), {"worker", "contract", "input"})
        self.assertNotIn("required_facts", json.dumps(content))

    def test_disabled_and_unallocated_owner_denies_before_process_or_credentials(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "evals").mkdir()
            owner = {
                "project": "p01",
                "protocol_version": 1,
                "execution_enabled": False,
                "synthetic_only": True,
                "account_policy": "groq-free-live-readiness-v1",
                "approved_campaigns": [],
            }
            path = project / "evals/live-execution.json"
            with patch(
                "subprocess.Popen", side_effect=AssertionError("provider process forbidden")
            ) as process:
                for enabled in (False, True):
                    owner["execution_enabled"] = enabled
                    owner["approved_campaigns"] = [self.binding.campaign_id] if enabled else []
                    path.write_text(json.dumps(owner), encoding="utf-8")
                    with self.assertRaisesRegex(BoundaryError, "guard_denied"):
                        SubprocessGuard(self.binding, project=project)
                process.assert_not_called()

    def test_diagnostics_drop_raw_values_and_reject_bool_status(self):
        self.assertEqual(
            diagnostic(
                {
                    "reason": "fixture-secret",
                    "http_status": True,
                    "provider_error_code": {"raw": "fixture-secret"},
                    "attempt_id": "invalid",
                    "content": "fixture-secret",
                }
            ),
            {
                "reason": "OTHER",
                "http_status": None,
                "provider_error_code": "OTHER",
                "attempt_id": None,
            },
        )

    def test_root_transport_encoder_parity_is_offline_and_utf8(self):
        payload = build_payload("classifier", SharedState(self.ticket).as_payload())
        script = "import sys,json; sys.path.insert(0,sys.argv[1]); from live_provider_transport import encode_payload; payload=json.load(sys.stdin); body,bound,out=encode_payload(payload,{'input_tokens_per_call':2048,'output_tokens_per_call':256}); print(json.dumps({'bound':bound,'output':out}))"
        environment = {
            name: os.environ[name]
            for name in ("PATH", "SystemRoot", "WINDIR", "TEMP", "TMP")
            if name in os.environ
        }
        environment.update(LLM_MODE="fake", PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
        result = subprocess.run(
            [sys.executable, "-S", "-c", script, str(PROJECT.parents[1] / "scripts/harness")],
            input=json.dumps(payload, ensure_ascii=False),
            text=True,
            encoding="utf-8",
            capture_output=True,
            timeout=10,
            env=environment,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {"bound": input_bound(payload), "output": 256})

    def test_legacy_cli_is_stdlib_only_and_denies_without_reading_credentials(self):
        result = subprocess.run(
            [sys.executable, "-S", str(PROJECT / "scripts/run_live_groq_eval.py")],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=10,
            env={
                "LLM_MODE": "live",
                "PYTHONIOENCODING": "utf-8",
                "SystemRoot": os.environ.get("SystemRoot", ""),
            },
        )
        self.assertEqual(result.returncode, 2, result.stderr)
        record = json.loads(result.stdout)
        self.assertIs(record["provider_accessed"], False)
        self.assertIs(record["credentials_read"], False)
        self.assertEqual(record["generation_calls"], 0)

    def test_subprocess_frames_are_utf8_and_never_inherit_provider_keys(self):
        guard = object.__new__(SubprocessGuard)
        guard.project, guard.binding = PROJECT, self.binding
        guard.process, guard.stopped, guard.next_index = None, False, 1
        reply = {"status": "ok", "attempt_id": "a" * 32}
        process = Mock()
        process.stdin = io.BytesIO()
        process.stdout = io.BytesIO(
            (
                json.dumps({"protocol_version": 1, "status": "ready"})
                + "\n"
                + json.dumps(reply)
                + "\n"
            ).encode("utf-8")
        )
        process.wait.return_value = 0
        envelope = {
            "operation": "complete",
            "campaign_id": self.binding.campaign_id,
            "case_id": self.binding.case_id,
            "trial": 1,
            "call_index": 1,
            "timeout_seconds": 20,
            "payload": build_payload("classifier", SharedState(self.ticket).as_payload()),
        }
        with (
            patch.dict(os.environ, {"GROQ_API_KEY_1": "fixture-parent-key"}),
            patch("subprocess.Popen", return_value=process) as factory,
        ):
            self.assertEqual(guard.request(envelope), reply)
            environment = factory.call_args.kwargs["env"]
            self.assertFalse(any(name.startswith("GROQ_API_KEY") for name in environment))
            self.assertEqual(factory.call_args.args[0][-2:], ["--project", "p01"])
        frame = process.stdin.getvalue()
        self.assertTrue(frame.endswith(b"\n"))
        self.assertIn("Ação".encode("utf-8"), frame)
        self.assertNotIn(b"fixture-parent-key", frame)
        guard.close()

    def test_subprocess_invalid_reply_stops_without_echoing_or_replaying(self):
        guard = object.__new__(SubprocessGuard)
        guard.project, guard.binding = PROJECT, self.binding
        guard.stopped, guard.next_index = False, 1
        process = Mock()
        process.stdin, process.stdout = io.BytesIO(), io.BytesIO(b"fixture-private-content\xff\n")
        process.wait.return_value = 0
        guard.process = process
        envelope = {
            "operation": "complete",
            "campaign_id": self.binding.campaign_id,
            "case_id": self.binding.case_id,
            "trial": 1,
            "call_index": 1,
            "timeout_seconds": 20,
            "payload": build_payload("classifier", SharedState(self.ticket).as_payload()),
        }
        with self.assertRaisesRegex(BoundaryError, "protocol_failure") as error:
            guard.request(envelope)
        self.assertNotIn("fixture-private-content", str(error.exception))
        with self.assertRaisesRegex(BoundaryError, "workflow_stopped"):
            guard.request(envelope)
        self.assertTrue(guard.stopped)

    def test_subprocess_timeout_is_uncertain_and_cannot_restart(self):
        guard = object.__new__(SubprocessGuard)
        guard.project, guard.binding = PROJECT, self.binding
        guard.stopped, guard.next_index = False, 1
        process = Mock()
        process.stdin, process.stdout = io.BytesIO(), io.BytesIO()
        process.wait.return_value = 0
        guard.process = process
        import queue

        replies = Mock()
        replies.get.side_effect = queue.Empty
        with (
            patch("supportops_agents.accounted_live.queue.Queue", return_value=replies),
            self.assertRaisesRegex(BoundaryError, "provider_timeout_uncertain"),
        ):
            guard._read()
        self.assertTrue(guard.stopped)

    def test_framework_scope_and_telemetry_are_set_before_import(self):
        from supportops_agents.registry import RunnerUnavailable, get_runner

        with (
            patch.dict(os.environ, {"LLM_MODE": "live"}, clear=True),
            patch("supportops_agents.registry.import_module") as load,
        ):
            with self.assertRaisesRegex(RunnerUnavailable, "offline-only"):
                get_runner("crewai")
            load.assert_not_called()
        observed = {}

        def load_framework(name):
            observed.update(
                {
                    key: os.environ.get(key)
                    for key in (
                        "OTEL_SDK_DISABLED",
                        "CREWAI_DISABLE_TELEMETRY",
                        "CREWAI_DISABLE_TRACKING",
                    )
                }
            )
            return Mock()

        with (
            patch.dict(os.environ, {"LLM_MODE": "fake"}, clear=True),
            patch("supportops_agents.registry.import_module", side_effect=load_framework),
        ):
            get_runner("crewai")
        self.assertEqual(
            observed,
            {
                key: "true"
                for key in (
                    "OTEL_SDK_DISABLED",
                    "CREWAI_DISABLE_TELEMETRY",
                    "CREWAI_DISABLE_TRACKING",
                )
            },
        )

    def authorized_fixture(self, directory):
        root = Path(directory) / "lab"
        project = root / "projects/p01"
        project.mkdir(parents=True)
        own_names = [
            "src/supportops_agents/worker.py",
            "scripts/campaign_ledger.py",
            "scripts/run_live_campaign.py",
            "scripts/run_live_groq_eval.py",
            "agent/prompts/live-core.md",
            "evals/live-execution.json",
            "evals/live-campaign.json",
            "evals/datasets/live-v1/cases.jsonl",
            "evals/datasets/live-v1/manifest.json",
            "evals/rubrics/live-v1/rubric.md",
            "pyproject.toml",
            "uv.lock",
        ]
        shared_names = [
            "scripts/harness/live_free_account.py",
            "scripts/harness/live_provider_transport.py",
            "shared/policies/groq-free-campaign.json",
        ]
        own = [project / name for name in own_names]
        shared = [root / name for name in shared_names]
        for path in own + shared:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("fixture\n", encoding="utf-8")
        owner = {
            "project": "p01",
            "protocol_version": 1,
            "execution_enabled": True,
            "synthetic_only": True,
            "account_policy": "groq-free-live-readiness-v1",
            "provider_timeout_seconds": 20,
            "authorized_paid_spend_usd": "0.00",
            "approved_campaigns": [self.binding.campaign_id],
            "allocations": {
                self.binding.campaign_id: {
                    "stage": "pilot",
                    "case_ids": [self.binding.case_id],
                    "trials_per_case": 1,
                    "max_trials": 6,
                }
            },
        }
        (project / "evals/live-execution.json").write_text(json.dumps(owner), encoding="utf-8")
        (root / ".gitignore").write_text("projects/\n", encoding="utf-8")
        for repository, names in ((root, [".gitignore", *shared_names]), (project, own_names)):
            for command in (
                ["git", "init", "-q"],
                ["git", "config", "user.name", "Offline Fixture"],
                ["git", "config", "user.email", "fixture@example.invalid"],
                ["git", "add", *names],
                ["git", "commit", "-q", "-m", "test(fixture): freeze public sources"],
            ):
                subprocess.run(command, cwd=repository, check=True, capture_output=True)
        candidate = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=project, text=True
        ).strip()
        manifest = {
            "candidate_commit": candidate,
            "campaign_id": self.binding.campaign_id,
            "stage": "pilot",
            "sampling_order": [self.binding.case_id],
            "trials_per_case": 1,
            "files_sha256": {
                path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in own + shared
            },
        }
        path = project / "artifacts/evals/live" / self.binding.campaign_id / "manifest.json"
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(manifest), encoding="utf-8")
        ledger = project / "artifacts/evals/live/ledger.sqlite"
        with closing(sqlite3.connect(ledger)) as db:
            db.execute(
                "CREATE TABLE events(sequence INTEGER PRIMARY KEY,campaign_id TEXT,case_id TEXT,trial INTEGER,event TEXT,reserved_calls INTEGER,reserved_input_tokens INTEGER,reserved_output_tokens INTEGER,reserved_cost_usd TEXT,actual_input_tokens INTEGER,actual_output_tokens INTEGER,actual_cost_usd TEXT)"
            )
            db.execute(
                "INSERT INTO events VALUES(1,?,?,1,'reserved',4,8192,1024,'0.0009216',NULL,NULL,NULL)",
                (self.binding.campaign_id, self.binding.case_id),
            )
            db.commit()
        return root, project, path

    def test_frozen_binding_accepts_only_committed_public_source_before_any_process(self):
        with tempfile.TemporaryDirectory() as directory:
            root, project, manifest_path = self.authorized_fixture(directory)
            guard = SubprocessGuard(self.binding, project=project)
            self.assertIsNone(guard.process)
            guard.close()
            source = project / "src/supportops_agents/worker.py"
            source.write_text("changed public source\n", encoding="utf-8")
            manifest = json.loads(manifest_path.read_text())
            manifest["files_sha256"][source.relative_to(root).as_posix()] = hashlib.sha256(
                source.read_bytes()
            ).hexdigest()
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(BoundaryError, "guard_denied"):
                SubprocessGuard(self.binding, project=project)
            subprocess.run(
                ["git", "add", str(source)], cwd=project, check=True, capture_output=True
            )
            with self.assertRaisesRegex(BoundaryError, "guard_denied"):
                SubprocessGuard(self.binding, project=project)

    def test_untracked_source_cannot_be_added_to_a_manifest_to_bypass_git(self):
        with tempfile.TemporaryDirectory() as directory:
            root, project, manifest_path = self.authorized_fixture(directory)
            source = project / "src/supportops_agents/untracked.py"
            source.write_text("fixture\n", encoding="utf-8")
            manifest = json.loads(manifest_path.read_text())
            manifest["files_sha256"][source.relative_to(root).as_posix()] = hashlib.sha256(
                source.read_bytes()
            ).hexdigest()
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(BoundaryError, "guard_denied"):
                SubprocessGuard(self.binding, project=project)

    def test_unknown_reservations_across_ids_exhaust_primary_without_confirmation(self):
        with tempfile.TemporaryDirectory() as directory:
            _root, project, _manifest = self.authorized_fixture(directory)
            ledger = project / "artifacts/evals/live/ledger.sqlite"
            with closing(sqlite3.connect(ledger)) as db:
                for sequence in range(2, 187):
                    db.execute(
                        "INSERT INTO events VALUES(?,?,?,1,'reserved',4,8192,1024,'0.0009216',NULL,NULL,NULL)",
                        (sequence, f"historical-{sequence}", f"case-{sequence}"),
                    )
                db.commit()
            guard = SubprocessGuard(self.binding, project=project)
            self.assertIsNone(guard.process)
            guard.close()
            with closing(sqlite3.connect(ledger)) as db:
                db.execute(
                    "INSERT INTO events VALUES(187,'another-id','another-case',1,'reserved',4,8192,1024,'0.0009216',NULL,NULL,NULL)"
                )
                db.commit()
            with self.assertRaisesRegex(BoundaryError, "guard_denied"):
                SubprocessGuard(self.binding, project=project)

    def test_prior_provider_receipt_blocks_uncertain_workflow_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            _root, project, _manifest = self.authorized_fixture(directory)
            with closing(
                sqlite3.connect(project / "artifacts/evals/live/provider-usage.sqlite")
            ) as db:
                db.execute("CREATE TABLE usage_events(campaign TEXT,case_id TEXT,trial INTEGER)")
                db.execute(
                    "INSERT INTO usage_events VALUES(?,?,1)",
                    (self.binding.campaign_id, self.binding.case_id),
                )
                db.commit()
            with self.assertRaisesRegex(BoundaryError, "guard_denied"):
                SubprocessGuard(self.binding, project=project)

    def test_dirty_root_policy_cannot_be_rehashed_to_bypass_committed_sources(self):
        with tempfile.TemporaryDirectory() as directory:
            root, project, manifest_path = self.authorized_fixture(directory)
            source = root / "shared/policies/groq-free-campaign.json"
            source.write_text("changed fixture policy\n", encoding="utf-8")
            manifest = json.loads(manifest_path.read_text())
            manifest["files_sha256"][source.relative_to(root).as_posix()] = hashlib.sha256(
                source.read_bytes()
            ).hexdigest()
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(BoundaryError, "guard_denied"):
                SubprocessGuard(self.binding, project=project)
            subprocess.run(["git", "add", str(source)], cwd=root, check=True, capture_output=True)
            with self.assertRaisesRegex(BoundaryError, "guard_denied"):
                SubprocessGuard(self.binding, project=project)


if __name__ == "__main__":
    unittest.main()
