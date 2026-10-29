"""Regression checks for the four-item retry and CLI-only batch preparation."""

import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from prepare_batch import prepare_batch


class PrepareBatchTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "scope.json"
        self.scope = {
            "source": "user_screenshot",
            "evidence": "User-supplied four-item Inbox screenshot",
            "retry_status": "pending",
            "item_count": 4,
            "items": [
                {"repo": "algesten/str0m", "number": 1082},
                {"repo": "algesten/dimpl", "number": 202},
                {"repo": "algesten/dimpl", "number": 201},
                {"repo": "algesten/str0m", "number": 1104},
            ],
        }
        self.response = {"data": {}}
        for index, (repo, numbers) in enumerate(
            [("algesten/str0m", [1082, 1104]), ("algesten/dimpl", [202, 201])]
        ):
            data = {"nameWithOwner": repo}
            for number in numbers:
                kind = "PullRequest" if number in (1082, 201) else "Issue"
                route = "pull" if kind == "PullRequest" else "issues"
                data[f"i{number}"] = {
                    "__typename": kind,
                    "number": number,
                    "state": "OPEN",
                    "title": f"Exact title {number}",
                    "url": f"https://github.com/{repo}/{route}/{number}",
                }
            self.response["data"][f"r{index}"] = data
        self.write_scope()

    def write_scope(self):
        self.path.write_text(json.dumps(self.scope))

    def gh_result(self):
        return subprocess.CompletedProcess([], 0, json.dumps(self.response), "")

    @patch("prepare_batch.subprocess.run")
    def test_pending_retry_resolves_only_the_four_selected_items(self, run):
        run.return_value = self.gh_result()
        result = prepare_batch(self.path, pending_only=True)
        self.assertEqual(result["item_count"], 4)
        self.assertEqual(result["pr_review_count"], 2)
        self.assertEqual(result["issue_triage_count"], 2)
        self.assertEqual({item["number"] for item in result["launch"]}, {1082, 1104, 201, 202})
        run.assert_called_once()
        self.assertEqual(run.call_args.args[0], ["gh", "api", "graphql", "--input", "-"])
        query = json.loads(run.call_args.kwargs["input"])["query"]
        for number in (1082, 1104, 201, 202):
            self.assertIn(f"number: {number})", query)
        self.assertNotIn("number: 1105)", query)
        for item in result["launch"]:
            self.assertEqual(item["expected_name"], f"#{item['number']}: {item['title']}")

    @patch("prepare_batch.subprocess.run")
    def test_gh_failure_has_no_browser_or_other_fallback(self, run):
        run.return_value = subprocess.CompletedProcess([], 1, "", "authentication failed")
        with self.assertRaisesRegex(ValueError, "gh failed: authentication failed"):
            prepare_batch(self.path)
        run.assert_called_once()
        self.assertEqual(run.call_args.args[0][0], "gh")

    @patch("prepare_batch.subprocess.run")
    def test_browser_or_api_history_is_not_scope_evidence(self, run):
        for source in ("browser_inbox", "notifications_api"):
            with self.subTest(source=source):
                self.scope["source"] = source
                self.write_scope()
                with self.assertRaises(ValueError):
                    prepare_batch(self.path)
        run.assert_not_called()

    @patch("prepare_batch.subprocess.run")
    def test_completed_retry_is_not_reused_as_current_inbox(self, run):
        self.scope["retry_status"] = "completed"
        self.write_scope()
        with self.assertRaisesRegex(ValueError, "not pending"):
            prepare_batch(self.path, pending_only=True)
        run.assert_not_called()

    @patch("prepare_batch.subprocess.run")
    def test_wrong_item_returned_by_api_is_rejected(self, run):
        item = self.response["data"]["r0"]["i1082"]
        item["number"] = 1105
        item["url"] = "https://github.com/algesten/str0m/pull/1105"
        run.return_value = self.gh_result()
        with self.assertRaisesRegex(ValueError, "OUT OF SCOPE"):
            prepare_batch(self.path)


if __name__ == "__main__":
    unittest.main()
