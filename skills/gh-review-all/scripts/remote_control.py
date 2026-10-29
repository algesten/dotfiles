#!/usr/bin/env python3
"""Read/check only explicitly supplied beast jobs; stdout is a JSON response."""

import json
import os
from pathlib import Path
import signal
import socket
import sqlite3
import struct
import subprocess
import sys
import time
import uuid


def process(pid):
    try:
        path = Path(f"/proc/{int(pid)}")
        fields = (path / "stat").read_text().rsplit(")", 1)[1].split()
        if fields[0] == "Z":
            return None
        return {"pid": int(pid), "start_ticks": int(fields[19]),
                "comm": (path / "comm").read_text().strip()}
    except (OSError, ValueError, TypeError):
        return None


def descendants(pid):
    rows = subprocess.check_output(["ps", "-eo", "pid=,ppid="], text=True)
    parents = [(int(a), int(b)) for a, b in (line.split() for line in rows.splitlines())]
    found = {int(pid)}
    while True:
        expanded = found | {child for child, parent in parents if parent in found}
        if expanded == found:
            return [info for child in sorted(found) if (info := process(child))]
        found = expanded


def session_info(token):
    uuid.UUID(token)
    directory = Path(os.environ.get("SCR_DIR", f"/tmp/scr-{os.geteuid()}"))
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as stream:
        stream.settimeout(0.75)
        try:
            stream.connect(str(directory / f"{token}.sock"))
        except (FileNotFoundError, ConnectionRefusedError):
            return None
        stream.sendall(b"T")

        def receive(size):
            data = b""
            while len(data) < size:
                chunk = stream.recv(size - len(data))
                if not chunk:
                    raise ValueError("scr closed its status response")
                data += chunk
            return data

        magic, attached, server_pid, size = struct.unpack(">4sBIH", receive(11))
        if magic != b"SCR1" or attached not in (0, 1) or size > 1024:
            raise ValueError("Unsupported scr status protocol")
        return {"attached": bool(attached), "server_pid": server_pid,
                "title": receive(size).decode("utf-8")}


def saved_thread(job):
    cwd = str(Path.home() / "dev" / job["repo"].split("/")[1])
    databases = sorted((Path.home() / ".codex").glob("state_*.sqlite"),
                       key=lambda path: path.stat().st_mtime, reverse=True)
    for path in databases:
        with sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=1) as db:
            db.row_factory = sqlite3.Row
            columns = {row[1] for row in db.execute("pragma table_info(threads)")}
            if not {"id", "name", "cwd", "created_at", "rollout_path"} <= columns:
                continue
            if job.get("thread_id"):
                rows = db.execute(
                    "select id,name,cwd,rollout_path from threads where id=?",
                    (job["thread_id"],),
                ).fetchall()
            else:
                rows = db.execute(
                    "select id,name,cwd,rollout_path from threads "
                    "where name=? and cwd=? and created_at>=?",
                    (job["expected_name"], cwd, int(job["since"]) - 1),
                ).fetchall()
            if len(rows) > 1:
                raise ValueError("Multiple new threads match this job; refusing to guess")
            if rows:
                result = dict(rows[0])
                if result["cwd"] != cwd:
                    raise ValueError("Saved thread belongs to a different checkout")
                result["database"] = str(path)
                return result
    return None


def progress(thread, marker):
    received, started, error = False, False, None
    if thread and marker:
        try:
            source = Path(thread["rollout_path"]).open()
        except FileNotFoundError:
            return {"task_received": False, "task_started": False, "task_error": None}
        with source:
            for line in source:
                try:
                    event = json.loads(line)
                except ValueError:
                    continue
                payload = event.get("payload", {})
                if event.get("type") == "response_item":
                    if payload.get("type") == "message":
                        text = "\n".join(item.get("text", "") for item in payload.get("content", []))
                        if payload.get("role") == "user" and marker in text:
                            received = True
                        elif received and payload.get("role") == "assistant":
                            started = True
                    elif received and payload.get("type") in ("function_call", "custom_tool_call", "reasoning"):
                        started = True
                elif received and event.get("type") == "event_msg":
                    if payload.get("type") in ("task_started", "agent_message", "agent_reasoning"):
                        started = True
                    elif payload.get("type") in ("error", "turn_aborted"):
                        error = payload.get("message", payload.get("type"))
    return {"task_received": received, "task_started": started, "task_error": error}


def inspect(job, set_title=False, check_progress=False):
    session = session_info(job["token"])
    result = {"session": session, "processes": [], "thread": None, "codex": None}
    if not session:
        return result
    server = process(session["server_pid"])
    tree = descendants(session["server_pid"]) if server else []
    result["processes"] = tree
    shell = process(job.get("shell_pid"))
    if shell and job.get("shell_start_ticks") not in (None, shell["start_ticks"]):
        raise ValueError("Remote shell PID was reused")
    if not shell or shell["pid"] not in {item["pid"] for item in tree}:
        return result
    result["shell"] = shell
    codexes = [item for item in descendants(shell["pid"]) if item["comm"] == "codex"]
    if job.get("codex_pid"):
        codexes = [item for item in codexes if item["pid"] == job["codex_pid"]
                   and item["start_ticks"] == job.get("codex_start_ticks")]
    if len(codexes) != 1:
        return result
    result["codex"] = codexes[0]
    thread = saved_thread(job)
    result["thread"] = thread
    if set_title and thread and thread["name"] == job["expected_name"]:
        target = Path(f"/proc/{shell['pid']}/fd/1")
        if not str(target.resolve()).startswith("/dev/pts/"):
            raise ValueError("Recorded shell does not own a PTY")
        fd = os.open(target, os.O_WRONLY | os.O_NOCTTY)
        try:
            os.write(fd, ("\x1b]0;" + job["expected_name"] + "\x07").encode())
        finally:
            os.close(fd)
    if check_progress:
        result.update(progress(thread, job.get("marker")))
    return result


def preflight(items):
    result = {}
    if items:
        available = subprocess.run(["bash", "-ic", "type cxlow"], text=True, capture_output=True)
        if available.returncode:
            raise ValueError("cxlow is not available in the remote interactive bash")
    for item in items:
        repo = item["repo"]
        if repo in result:
            continue
        path = Path.home() / "dev" / repo.split("/")[1]
        origin = subprocess.check_output(
            ["git", "-C", str(path), "remote", "get-url", "origin"], text=True,
            stderr=subprocess.PIPE,
        ).strip()
        normalized = origin.removesuffix(".git").replace("git@github.com:", "https://github.com/")
        if normalized.lower() != f"https://github.com/{repo}".lower():
            raise ValueError(f"Clone origin mismatch for {repo}")
        result[repo] = str(path)
    if any(item["kind"] == "PullRequest" for item in items):
        if not (Path.home() / ".codex/skills/worktree-pr/SKILL.md").is_file():
            raise ValueError("worktree-pr skill is missing on beast")
    return result


def terminate(records, tokens):
    for sig in (signal.SIGTERM, signal.SIGKILL):
        for record in reversed(records):
            current = process(record["pid"])
            if current and current["start_ticks"] == record["start_ticks"]:
                try:
                    os.kill(record["pid"], sig)
                except ProcessLookupError:
                    pass
        time.sleep(0.15)
    remaining = [record for record in records if (current := process(record["pid"]))
                 and current["start_ticks"] == record["start_ticks"]]
    return {"remaining_processes": remaining,
            "sessions_remaining": sum(session_info(token) is not None for token in tokens)}


def main():
    try:
        request = json.load(sys.stdin)
        operation = request["operation"]
        if operation == "preflight":
            value = preflight(request["items"])
        elif operation == "inspect":
            value = inspect(request["job"], request.get("set_title", False),
                            request.get("check_progress", False))
        elif operation == "terminate":
            value = terminate(request["processes"], request["tokens"])
        elif operation == "alive":
            value = [info for pid in request["pids"] if (info := process(pid))]
        else:
            raise ValueError("Unknown operation")
        print(json.dumps({"ok": True, "value": value}))
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
