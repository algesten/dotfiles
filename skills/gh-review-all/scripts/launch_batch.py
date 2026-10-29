#!/usr/bin/env python3
"""Launch a validated batch, name live CLIs, hand off tasks, and detach."""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
import pty
import re
import select
import shlex
import struct
import subprocess
import sys
import termios
import threading
import time
import uuid

from prepare_batch import DEFAULT_SCOPE, prepare_batch


SKILL = Path(__file__).resolve().parent.parent
STATE = SKILL / "state"
HOST = "martin@beast"
ANSI = re.compile(r"\x1b\].*?(?:\x07|\x1b\\)|\x1b\[[0-?]*[ -/]*[@-~]|\x1b[()][A-Z0-9]|\x1b[=>]", re.S)


@contextmanager
def selection_lock(scope_path):
    lock_path = Path(str(scope_path) + ".launch.lock")
    fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError("Another launcher is already handling this selection") from None
        yield
    finally:
        os.close(fd)


class Cancellation:
    def __init__(self, path):
        self.path = path
        self.event = threading.Event()

    def is_set(self):
        return self.event.is_set() or self.path.exists()

    def set(self):
        self.event.set()
        fd = os.open(self.path, os.O_CREAT | os.O_WRONLY, 0o600)
        os.close(fd)


def private_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as output:
        json.dump(value, output, indent=2)
        output.write("\n")
    os.replace(temporary, path)


class Remote:
    def __init__(self):
        source = (SKILL / "scripts/remote_control.py").read_text()
        self.command = ["ssh", HOST, shlex.join(["python3", "-c", source])]

    def call(self, operation, **values):
        result = subprocess.run(self.command, input=json.dumps(dict(operation=operation, **values)),
                                text=True, capture_output=True, timeout=12)
        if not result.stdout.strip():
            raise RuntimeError(result.stderr.strip() or "No response from beast")
        response = json.loads(result.stdout)
        if not response["ok"]:
            raise RuntimeError(response["error"])
        return response["value"]


class Terminal:
    def __init__(self, token, cancelled):
        if cancelled.is_set():
            raise RuntimeError("Launch cancelled")
        self.cancelled = cancelled
        self.buffer = b""
        self.master, slave = pty.openpty()
        fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", 40, 180, 0, 0))
        try:
            self.process = subprocess.Popen(
                ["bash", "-ic", "scr"], stdin=slave, stdout=slave, stderr=slave,
                env=dict(os.environ, SCR_SESSION_TOKEN=token), start_new_session=True,
            )
        finally:
            os.close(slave)

    def read(self, duration=0.1):
        until = time.monotonic() + duration
        while time.monotonic() < until:
            ready, _, _ = select.select([self.master], [], [], min(0.1, max(0, until-time.monotonic())))
            if not ready:
                continue
            try:
                chunk = os.read(self.master, 65536)
            except OSError:
                break
            if not chunk:
                break
            self.buffer = (self.buffer + chunk)[-1_000_000:]

    def plain(self):
        return ANSI.sub("", self.buffer.decode(errors="replace")).replace("\r", "")

    def send(self, text):
        data = text.encode()
        while data:
            count = os.write(self.master, data)
            data = data[count:]

    def paste(self, text):
        self.send("\x1b[200~" + text + "\x1b[201~\r")

    def wait(self, predicate, timeout, description):
        until = time.monotonic() + timeout
        while time.monotonic() < until:
            if self.cancelled.is_set():
                raise RuntimeError("Launch cancelled")
            self.read()
            if predicate():
                return
            if self.process.poll() is not None:
                raise RuntimeError(f"Terminal exited while waiting for {description}")
        raise RuntimeError(f"Timed out waiting for {description}")

    def detach(self):
        self.send("\x02d")
        until = time.monotonic() + 6
        while self.process.poll() is None and time.monotonic() < until:
            self.read()
        if self.process.poll() != 0:
            raise RuntimeError("scr detachment did not close its SSH client cleanly")

    def close(self):
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=2)
        os.close(self.master)


def shell_command(job):
    title = shlex.quote(job["expected_name"])
    repo = shlex.quote(job["repo"].split("/")[1])
    return (f"printf '\\036{job['shell_marker']}:%s\\n' \"$$\"\n"
            f"printf '\\033]0;%s\\007' {title}\n"
            f"cd ~/dev/{repo} || exit 1\n"
            "cxlow -c 'tui.terminal_title=[]'")


def task_prompt(job):
    text = (SKILL / "SKILL.md").read_text()
    heading = "PR task" if job["kind"] == "PullRequest" else "Issue task"
    section = text.split("### " + heading + "\n", 1)[1]
    task = next(line[2:] for line in section.splitlines() if line.startswith("> "))
    task = task.replace("<PR URL>", job["url"]).replace("<issue URL>", job["url"])
    setup = (
        f"Launch job: {job['marker']}\n"
        f"The launcher's first live CLI action was /rename {job['expected_name']}. "
        "It independently verified the saved name and full scr title before sending this task. "
        f"Your first action is to independently read back your saved name from {job['database']} "
        "using a read-only sqlite3 connection: select name from threads where id=CODEX_THREAD_ID. "
        f"Your thread ID is {job['thread_id']}; compare with your own CODEX_THREAD_ID environment value. "
        f"The exact expected name is {json.dumps(job['expected_name'], ensure_ascii=False)}. "
        "Explicitly confirm the matching readback before other work. If it mismatches, report the blocker. "
        "Do not research or retry app-server proxy, /title, or other naming interfaces. "
        "The launcher used the live /rename operation and disabled automatic title shortening only "
        "for this invocation with tui.terminal_title=[]; keep that setting. "
        "Then read and follow applicable AGENTS.md instructions. Keep the main checkout on its primary "
        "branch and do not disturb other agents or worktrees. Use authenticated gh outside the sandbox "
        "for GitHub network requests; never use Safari MCP or browser fallbacks. "
        "Before the final recommendation, fetch the current GitHub title and recheck the saved name. "
        "If the title changed, report it so the launcher can synchronize both saved and visible names. "
        "Do not publish GitHub comments or reviews, apply fixes, or merge.\n\n"
    )
    if job["kind"] == "PullRequest":
        task += (" If its worktree is already in use, leave it untouched and use a separate "
                 "review checkout or report the conflict.")
    else:
        task += " Use the existing checkout read-only; do not change branches or create a worktree."
    return setup + task


def validate_names(job, observed, detached=False):
    thread, session = observed.get("thread"), observed.get("session")
    return bool(thread and session and observed.get("codex")
                and thread["name"] == job["expected_name"]
                and session["title"] == job["expected_name"]
                and (not detached or not session["attached"]))


class Batch:
    def __init__(self, plan, scope_path=None, remote=None, terminal_factory=Terminal):
        self.remote = remote or Remote()
        self.terminal_factory = terminal_factory
        self.scope_path = Path(scope_path) if scope_path else None
        self.lock = threading.Lock()
        self.started = time.monotonic()
        run_id = uuid.uuid4().hex
        self.path = STATE / "runs" / run_id / "manifest.json"
        self.cancelled = Cancellation(self.path.parent / "cancel.request")
        self.manifest = {"version": 1, "run_id": run_id, "scope_path": str(self.scope_path) if self.scope_path else None,
                         "status": "starting", "skipped": plan["skipped"], "jobs": []}
        for item in plan["launch"]:
            job = dict(item, token=str(uuid.uuid4()), status="planned",
                       shell_marker="GH_REVIEW_SHELL_" + uuid.uuid4().hex,
                       marker=run_id + "/" + item["repo"] + "#" + str(item["number"]))
            self.manifest["jobs"].append(job)
        self.save()

    def save(self):
        with self.lock:
            private_json(self.path, self.manifest)

    def log(self, job, message):
        with self.lock:
            label = f"{job['repo']}#{job['number']}" if job else "batch"
            print(f"[{time.monotonic()-self.started:5.1f}s] {label}: {message}", flush=True)

    def record(self, job, observed):
        if observed.get("shell"):
            job["shell_start_ticks"] = observed["shell"]["start_ticks"]
        if observed.get("codex"):
            job["codex_pid"] = observed["codex"]["pid"]
            job["codex_start_ticks"] = observed["codex"]["start_ticks"]
        if observed.get("thread"):
            job.update(thread_id=observed["thread"]["id"], database=observed["thread"]["database"])
        job["processes"] = observed.get("processes", job.get("processes", []))
        self.save()

    def cancel_job(self, job):
        # Capture descendants before scr closes the PTY and they are reparented.
        observed = self.remote.call("inspect", job=job)
        processes = observed["processes"] or job.get("processes", [])
        if observed["session"]:
            result = subprocess.run(["bash", "-ic", 'scr kill "$SCR_SESSION_TOKEN"'],
                                    env=dict(os.environ, SCR_SESSION_TOKEN=job["token"]),
                                    capture_output=True, text=True, timeout=8)
            if result.returncode:
                self.log(job, "scr kill returned an error; checking recorded processes")
        cleanup = self.remote.call("terminate", processes=processes, tokens=[job["token"]])
        if cleanup["remaining_processes"] or cleanup["sessions_remaining"]:
            job["status"] = "cancellation_failed"
            self.save()
            raise RuntimeError("Cancellation incomplete: a recorded process or persistent terminal remains")
        job["status"] = "cancelled"
        self.save()

    def start_job(self, job, timeout=40, naming_only=False):
        terminal = None
        try:
            if self.cancelled.is_set():
                raise RuntimeError("Launch cancelled")
            job.update(since=time.time(), status="opening_terminal")
            self.save()
            terminal = self.terminal_factory(job["token"], self.cancelled)
            terminal.wait(lambda: bool(re.search(r"[$#] \s*$", terminal.plain())), timeout, "remote shell")
            terminal.paste(shell_command(job))
            shell_pattern = re.compile(rb"\x1e" + job["shell_marker"].encode() + rb":(\d+)")
            terminal.wait(lambda: shell_pattern.search(terminal.buffer) is not None, timeout, "shell identity")
            job["shell_pid"] = int(shell_pattern.search(terminal.buffer).group(1))
            job["status"] = "naming"
            self.save()
            terminal.wait(lambda: "OpenAI Codex" in terminal.plain(), timeout, "Codex UI")
            terminal.read(0.6)
            terminal.send("/rename " + job["expected_name"] + "\r")
            terminal.read(0.2)
            terminal.send("\r")
            until = time.monotonic() + timeout
            while time.monotonic() < until:
                if self.cancelled.is_set():
                    raise RuntimeError("Launch cancelled")
                observed = self.remote.call("inspect", job=job, set_title=True)
                self.record(job, observed)
                if validate_names(job, observed):
                    break
                terminal.read(0.2)
            else:
                raise RuntimeError("Saved or visible name did not match before task handoff")
            job["status"] = "naming_verified"
            self.save()
            self.log(job, "saved name and full scr title verified")
            if not naming_only:
                if self.cancelled.is_set():
                    raise RuntimeError("Launch cancelled before task handoff")
                terminal.paste(task_prompt(job))
                until = time.monotonic() + timeout
                while time.monotonic() < until:
                    if self.cancelled.is_set():
                        raise RuntimeError("Launch cancelled")
                    terminal.read(0.2)
                    observed = self.remote.call("inspect", job=job, check_progress=True)
                    self.record(job, observed)
                    if observed.get("task_error"):
                        raise RuntimeError(str(observed["task_error"]))
                    if observed.get("task_received") and observed.get("task_started"):
                        break
                else:
                    raise RuntimeError("Task handoff was not acknowledged in the assigned thread")
            terminal.detach()
            observed = self.remote.call("inspect", job=job)
            self.record(job, observed)
            if not validate_names(job, observed, detached=True):
                raise RuntimeError("Final saved-name, visible-name, process, or detachment check failed")
            job["status"] = "named_detached" if naming_only else "started_detached"
            self.save()
            self.log(job, "named and detached" if naming_only else "task started; detached")
            return True
        except Exception as exc:
            message = str(exc).replace(job["token"], "[private session]")
            job["error"] = message
            self.save()
            try:
                self.cancel_job(job)
            except Exception as cleanup_error:
                job["status"] = "cancellation_failed"
                job["cleanup_error"] = str(cleanup_error).replace(job["token"], "[private session]")
                self.save()
            self.log(job, "failed: " + message + "; " + job["status"])
            return False
        finally:
            if terminal:
                terminal.close()

    def run(self, timeout=40):
        self.log(None, f"{len(self.manifest['jobs'])} jobs; manifest {self.path}")
        for job in self.manifest["jobs"]:
            self.log(job, "selected: " + job["expected_name"])
        pool = ThreadPoolExecutor(max_workers=min(4, max(1, len(self.manifest["jobs"]))))
        results = []
        try:
            futures = [pool.submit(self.start_job, job, timeout) for job in self.manifest["jobs"]]
            for future in as_completed(futures):
                results.append(future.result())
        except KeyboardInterrupt:
            self.cancelled.set()
            self.log(None, "interrupt received; cancelling only this batch")
            for job in self.manifest["jobs"]:
                self.cancel_job(job)
            self.manifest["status"] = "cancelled"
            self.save()
            self.update_scope("cancelled")
            raise
        finally:
            pool.shutdown(wait=True, cancel_futures=True)
        if self.cancelled.is_set():
            for job in self.manifest["jobs"]:
                if job["status"] not in ("cancelled", "cancellation_failed"):
                    self.cancel_job(job)
            self.manifest["status"] = "cancelled"
            self.save()
            self.update_scope("cancelled")
            return False
        self.manifest["status"] = "started_detached" if all(results) else "partial_failure"
        self.save()
        self.update_scope("completed" if all(results) else "pending")
        return all(results)

    def update_scope(self, status):
        if self.scope_path:
            scope = json.loads(self.scope_path.read_text())
            expected = {(job["repo"].lower(), job["number"]) for job in self.manifest["jobs"] + self.manifest["skipped"]}
            actual = {(item["repo"].lower(), item["number"]) for item in scope["items"]}
            if expected != actual:
                raise RuntimeError("Saved selection changed concurrently; refusing to overwrite it")
            scope.update(retry_status=status, launch_manifest=str(self.path))
            scope["launches"] = [{key: job[key] for key in (
                "repo", "number", "expected_name", "status", "thread_id", "shell_pid", "codex_pid"
            ) if key in job} for job in self.manifest["jobs"]]
            private_json(self.scope_path, scope)


def load_batch(path, remote=None):
    batch = object.__new__(Batch)
    batch.path = Path(path)
    batch.manifest = json.loads(batch.path.read_text())
    if batch.manifest.get("version") != 1:
        raise ValueError("Unsupported launch manifest")
    batch.remote = remote or Remote()
    batch.scope_path = Path(batch.manifest["scope_path"]) if batch.manifest.get("scope_path") else None
    batch.cancelled = Cancellation(batch.path.parent / "cancel.request")
    batch.lock, batch.started = threading.Lock(), time.monotonic()
    return batch


def launch_selected(args):
    scope_path = args.scope or DEFAULT_SCOPE
    with selection_lock(scope_path):
        plan = prepare_batch(scope_path, pending_only=args.scope is None)
        remote = Remote()
        remote.call("preflight", items=plan["launch"])
        scope = json.loads(scope_path.read_text())
        prior_pids = [item.get("codex_pid", item.get("remote_codex_pid"))
                      for item in scope.get("launches", [])]
        if remote.call("alive", pids=[pid for pid in prior_pids if pid]):
            raise RuntimeError("The selected batch already has live agents; inspect its saved manifest instead of duplicating them")
        if args.dry_run:
            print(json.dumps(plan, indent=2))
            return 0
        print(f"Selected {plan['item_count']} items: {plan['pr_review_count']} PR reviews, "
              f"{plan['issue_triage_count']} issue triages, {len(plan['skipped'])} skips.", flush=True)
        batch = Batch(plan, scope_path, remote)
        batch.update_scope("pending")
        return 0 if batch.run(args.timeout) else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    launch = commands.add_parser("launch")
    launch.add_argument("--scope", type=Path)
    launch.add_argument("--dry-run", action="store_true")
    launch.add_argument("--timeout", type=float, default=40)
    for command in ("status", "cancel"):
        sub = commands.add_parser(command)
        sub.add_argument("manifest", type=Path)
        sub.add_argument("--item", help="Limit to owner/repo#number")
    commands.add_parser("smoke", help="Test one empty CLI, send no model prompt, then cancel it")
    args = parser.parse_args()
    try:
        if args.command == "launch":
            return launch_selected(args)
        if args.command == "smoke":
            name = "gh-review-all automation smoke " + uuid.uuid4().hex[:8]
            item = {"repo": "algesten/str0m", "number": 0, "kind": "Issue", "expected_name": name}
            batch = Batch({"launch": [item], "skipped": []})
            job = batch.manifest["jobs"][0]
            try:
                success = batch.start_job(job, timeout=20, naming_only=True)
                if not success:
                    return 1
            finally:
                batch.cancel_job(job)
            batch.log(None, "empty CLI test removed; no model prompt sent")
            return 0
        batch = load_batch(args.manifest)
        if args.command == "cancel":
            if args.item and batch.manifest["status"] == "starting":
                raise ValueError("During startup cancel the whole batch, or wait for detachment before cancelling one item")
            if not args.item:
                batch.cancelled.set()
        jobs = [job for job in batch.manifest["jobs"] if not args.item or f"{job['repo']}#{job['number']}" == args.item]
        if args.item and not jobs:
            raise ValueError("The requested item is not in this manifest")
        for job in jobs:
            if args.command == "cancel":
                batch.cancel_job(job)
                batch.log(job, "processes stopped and persistent terminal removed")
            else:
                observed = batch.remote.call("inspect", job=job)
                print(json.dumps({"item": f"{job['repo']}#{job['number']}", "status": job["status"],
                                  "names_verified": validate_names(job, observed),
                                  "session_present": observed["session"] is not None,
                                  "detached": bool(observed["session"] and not observed["session"]["attached"])}))
        if args.command == "cancel" and all(job["status"] == "cancelled" for job in batch.manifest["jobs"]):
            batch.manifest["status"] = "cancelled"
            batch.save()
            batch.update_scope("cancelled")
        return 0
    except KeyboardInterrupt:
        print("Batch launch interrupted; see its manifest for cancellation status.", file=sys.stderr)
        return 130
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        print(f"BATCH LAUNCH BLOCKED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
