"""Behavioral checks for naming gates, prompt handoff, and complete cancellation."""

import io
import json
from pathlib import Path
import re
import stat
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import launch_batch
import remote_control


class FakeTerminal:
    def __init__(self, job, events):
        self.job, self.events = job, events
        self.buffer = b"remote$ "
        self.detached = False

    def plain(self):
        return self.buffer.decode()

    def wait(self, predicate, timeout, description):
        if not predicate():
            raise RuntimeError("Not ready: " + description)

    def paste(self, text):
        if "cxlow -c" in text:
            self.events.append("start_cli")
            self.buffer += (f"\x1e{self.job['shell_marker']}:1234\nOpenAI Codex").encode()
        else:
            self.events.append("task")
            self.prompt = text

    def send(self, text):
        if text.startswith("/rename "):
            self.events.append("rename")

    def read(self, duration=0.1):
        pass

    def detach(self):
        self.events.append("detach")
        self.detached = True

    def close(self):
        self.events.append("close")


class FakeRemote:
    def __init__(self, events):
        self.events = events
        self.terminal = None
        self.mode = "success"

    def call(self, operation, **values):
        if operation == "terminate":
            self.events.append("verify_cleanup")
            return {"remaining_processes": [], "sessions_remaining": int(self.mode == "cleanup_failure")}
        if operation == "inspect":
            job = values["job"]
            if not self.terminal:
                return {"session": None, "processes": []}
            shell = {"pid": 1234, "start_ticks": 10, "comm": "bash"}
            codex = {"pid": 1235, "start_ticks": 20, "comm": "codex"}
            name = "wrong name" if self.mode == "saved_mismatch" else job["expected_name"]
            title = "abbreviated title" if self.mode == "visible_mismatch" else job["expected_name"]
            if name == title == job["expected_name"]:
                self.events.append("names_verified")
            task_sent = "task" in self.events
            return {
                "session": {"title": title, "attached": not self.terminal.detached},
                "shell": shell, "codex": codex, "processes": [shell, codex],
                "thread": {"id": "test-thread", "name": name, "database": "/test/state.sqlite"},
                "task_received": task_sent, "task_started": task_sent,
                "task_error": "quota exceeded" if task_sent and self.mode == "task_error" else None,
            }
        raise AssertionError(operation)


class LaunchTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.state = Path(self.directory.name)
        self.patch_state = patch.object(launch_batch, "STATE", self.state)
        self.patch_state.start()
        self.addCleanup(self.patch_state.stop)
        self.events = []
        self.remote = FakeRemote(self.events)
        item = {"repo": "owner/repo", "number": 123, "kind": "PullRequest", "state": "OPEN",
                "title": "Exact title", "expected_name": "#123: Exact title",
                "url": "https://github.com/owner/repo/pull/123"}
        self.batch = launch_batch.Batch({"launch": [item], "skipped": []}, remote=self.remote)
        self.job = self.batch.manifest["jobs"][0]

        def terminal(token, cancelled):
            self.remote.terminal = FakeTerminal(self.job, self.events)
            return self.remote.terminal

        self.batch.terminal_factory = terminal
        self.run_patch = patch("launch_batch.subprocess.run", return_value=subprocess.CompletedProcess([], 0, "", ""))
        self.run_mock = self.run_patch.start()
        self.addCleanup(self.run_patch.stop)
        self.output = io.StringIO()
        self.stdout = patch("sys.stdout", self.output)
        self.stdout.start()
        self.addCleanup(self.stdout.stop)

    def test_rename_and_both_name_checks_precede_single_task_handoff(self):
        self.assertTrue(self.batch.start_job(self.job, timeout=0.01))
        self.assertLess(self.events.index("rename"), self.events.index("names_verified"))
        self.assertLess(self.events.index("names_verified"), self.events.index("task"))
        self.assertLess(self.events.index("task"), self.events.index("detach"))
        self.assertEqual(self.events.count("task"), 1)
        self.assertEqual(self.job["status"], "started_detached")
        self.assertIn(self.job["marker"], self.remote.terminal.prompt)
        self.assertNotIn(self.job["token"], self.output.getvalue())

    def test_saved_name_mismatch_never_hands_over_task(self):
        self.remote.mode = "saved_mismatch"
        self.assertFalse(self.batch.start_job(self.job, timeout=0.001))
        self.assertNotIn("task", self.events)
        self.assertIn("verify_cleanup", self.events)
        self.assertEqual(self.job["status"], "cancelled")

    def test_abbreviated_visible_name_is_not_accepted(self):
        self.remote.mode = "visible_mismatch"
        self.assertFalse(self.batch.start_job(self.job, timeout=0.001))
        self.assertNotIn("task", self.events)
        self.assertEqual(self.job["status"], "cancelled")

    def test_failed_task_start_is_cancelled(self):
        self.remote.mode = "task_error"
        self.assertFalse(self.batch.start_job(self.job, timeout=0.01))
        self.assertIn("verify_cleanup", self.events)
        self.assertEqual(self.job["status"], "cancelled")

    def test_killing_processes_without_removing_terminal_is_not_complete(self):
        self.remote.mode = "cleanup_failure"
        self.remote.terminal = FakeTerminal(self.job, self.events)
        with self.assertRaisesRegex(RuntimeError, "Cancellation incomplete"):
            self.batch.cancel_job(self.job)
        self.assertEqual(self.job["status"], "cancellation_failed")
        self.run_mock.assert_called_once()
        self.assertIn("scr kill", self.run_mock.call_args.args[0][-1])

    def test_persisted_cancellation_prevents_new_terminal(self):
        self.batch.cancelled.set()
        self.assertFalse(self.batch.start_job(self.job, timeout=0.01))
        self.assertIsNone(self.remote.terminal)
        self.assertNotIn("task", self.events)

    def test_private_manifest_contains_recovery_identifiers(self):
        self.assertEqual(stat.S_IMODE(self.batch.path.stat().st_mode), 0o600)
        saved = json.loads(self.batch.path.read_text())
        self.assertEqual(saved["jobs"][0]["token"], self.job["token"])

    def test_concurrent_launchers_cannot_lock_the_same_selection(self):
        path = self.state / "scope.json"
        path.write_text("{}")
        with launch_batch.selection_lock(path):
            with self.assertRaisesRegex(RuntimeError, "already handling"):
                with launch_batch.selection_lock(path):
                    self.fail("Duplicate launcher acquired the selection lock")


class ProcessAndQuotingTests(unittest.TestCase):
    @patch("remote_control.time.sleep")
    @patch("remote_control.session_info", return_value=None)
    @patch("remote_control.os.kill")
    @patch("remote_control.process", return_value={"pid": 123, "start_ticks": 99})
    def test_cancellation_never_signals_a_reused_pid(self, process, kill, session, sleep):
        result = remote_control.terminate([{"pid": 123, "start_ticks": 10}], ["test-token"])
        kill.assert_not_called()
        self.assertEqual(result["remaining_processes"], [])

    def test_shell_title_is_quoted_as_data(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "must-not-be-created"
            job = {"repo": "owner/nonexistent-gh-review-quote-test", "shell_marker": "TEST_MARKER",
                   "expected_name": f"#1: apostrophe ' and $(touch {target})"}
            result = subprocess.run(["bash", "-c", launch_batch.shell_command(job)],
                                    capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)  # The intentionally absent checkout stops cxlow.
            self.assertFalse(target.exists())
            self.assertIn(job["expected_name"], result.stdout)


if __name__ == "__main__":
    unittest.main()
