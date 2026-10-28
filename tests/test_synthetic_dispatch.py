import tempfile
import threading
import unittest
from pathlib import Path

from supportops_agents.synthetic_dispatch import DispatchBlocked, SyntheticDispatcher


class SyntheticDispatchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "dispatch.sqlite"
        self.calls = []
        self.dispatcher = SyntheticDispatcher(self.path, {"search_knowledge": self.adapter})

    def adapter(self, context):
        self.calls.append(context)
        return "synthetic result"

    def test_completed_receipt_prevents_duplicate_dispatch(self):
        args = ("run-1", ["search_knowledge"], {"tenant": "fixture-a"})
        self.assertEqual(self.dispatcher.run(*args), ["synthetic result"])
        self.assertEqual(self.dispatcher.run(*args), ["synthetic result"])
        self.assertEqual(self.calls, [{"tenant": "fixture-a"}])
        with self.assertRaises(DispatchBlocked):
            self.dispatcher.run("run-1", ["search_knowledge"], {"tenant": "fixture-b"})

    def test_invalid_plans_never_call_adapter(self):
        for plan in ([], ["search_knowledge"] * 2, ["write"], ["search_knowledge", "write"]):
            with self.subTest(plan=plan), self.assertRaises(DispatchBlocked):
                self.dispatcher.run("run-2", plan, {"tenant": "fixture-a"})
        self.assertEqual(self.calls, [])

    def test_interruption_blocks_restart_without_replay(self):
        def interrupted(_):
            raise RuntimeError("synthetic interruption")
        dispatcher = SyntheticDispatcher(self.path, {"search_knowledge": interrupted})
        with self.assertRaises(DispatchBlocked):
            dispatcher.run("run-3", ["search_knowledge"], {"tenant": "fixture-a"})
        with self.assertRaises(DispatchBlocked):
            self.dispatcher.run("run-3", ["search_knowledge"], {"tenant": "fixture-a"})
        self.assertEqual(self.calls, [])

    def test_concurrent_duplicate_is_not_dispatched_twice(self):
        started, release = threading.Event(), threading.Event()
        def slow(context):
            started.set()
            release.wait(5)
            return self.adapter(context)
        dispatcher = SyntheticDispatcher(self.path, {"search_knowledge": slow})
        thread = threading.Thread(target=lambda: dispatcher.run("run-4", ["search_knowledge"], {"tenant": "fixture-a"}))
        thread.start()
        self.assertTrue(started.wait(5))
        try:
            with self.assertRaises(DispatchBlocked):
                dispatcher.run("run-4", ["search_knowledge"], {"tenant": "fixture-a"})
        finally:
            release.set()
            thread.join(5)
        self.assertEqual(len(self.calls), 1)


if __name__ == "__main__":
    unittest.main()
