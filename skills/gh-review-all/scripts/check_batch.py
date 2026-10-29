#!/usr/bin/env python3
"""Check an Inbox scope against resolved metadata without launching anything."""

import argparse
import json
from pathlib import Path
import re
import sys


SOURCES = {"user_screenshot", "user_list", "explicit_user_batch"}


def identity(item):
    if not isinstance(item, dict):
        raise ValueError("Every item must be an object")
    repo, number = item.get("repo"), item.get("number")
    if not isinstance(repo, str) or not re.fullmatch(
        r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo
    ):
        raise ValueError("Every item needs an owner/repository identity")
    if type(number) is not int or number < 1:
        raise ValueError(f"Invalid item number for {repo}")
    return f"{repo.lower()}#{number}"


def validate_scope(scope):
    if not isinstance(scope, dict) or scope.get("source") not in SOURCES:
        raise ValueError("Scope must come from Inbox evidence or an explicit user batch")
    evidence = scope.get("evidence")
    if not isinstance(evidence, str) or not evidence.strip():
        raise ValueError("Scope evidence is required")
    scoped_items = scope.get("items")
    if not isinstance(scoped_items, list):
        raise ValueError("Scope items must be a list")
    count = scope.get("item_count")
    if type(count) is not int or count != len(scoped_items):
        raise ValueError("Scope item_count must match the evidence's transcribed items")
    return count, {identity(item) for item in scoped_items}


def check_batch(scope, plan):
    count, allowed = validate_scope(scope)

    if not isinstance(plan, dict) or not isinstance(plan.get("items"), list):
        raise ValueError("Plan must contain an items list")
    resolved = {}
    for item in plan["items"]:
        key = identity(item)
        if key in resolved:
            raise ValueError(f"Duplicate plan item: {key}")
        resolved[key] = item
    extras, missing = set(resolved) - allowed, allowed - set(resolved)
    if extras or missing:
        details = []
        if extras:
            details.append("OUT OF SCOPE: " + ", ".join(sorted(extras)))
        if missing:
            details.append("MISSING: " + ", ".join(sorted(missing)))
        raise ValueError("; ".join(details))

    launch, skipped = [], []
    for key, item in resolved.items():
        kind, state = item.get("kind"), item.get("state")
        if kind not in {"PullRequest", "Issue"}:
            raise ValueError(f"Unresolved item kind: {key}")
        if state not in {"OPEN", "CLOSED", "MERGED"}:
            raise ValueError(f"Unresolved item state: {key}")
        if kind == "Issue" and state == "MERGED":
            raise ValueError(f"An issue cannot have merged state: {key}")
        if not isinstance(item.get("title"), str) or not item["title"].strip():
            raise ValueError(f"Missing exact GitHub title: {key}")
        if any(ord(char) < 32 or ord(char) == 127 for char in item["title"]):
            raise ValueError(f"The title contains terminal control characters: {key}")
        if len(f"#{item['number']}: {item['title']}".encode()) > 1024:
            raise ValueError(f"The exact session name exceeds scr's title limit: {key}")
        route = "pull" if kind == "PullRequest" else "issues"
        expected_url = f"https://github.com/{item['repo']}/{route}/{item['number']}"
        if item.get("url") != expected_url:
            raise ValueError(f"URL does not match the assigned item: {key}")
        checked_item = dict(item, expected_name=f"#{item['number']}: {item['title']}")
        (launch if state == "OPEN" else skipped).append(checked_item)

    return {
        "item_count": count,
        "distinct_item_count": len(allowed),
        "pr_review_count": sum(item["kind"] == "PullRequest" for item in launch),
        "issue_triage_count": sum(item["kind"] == "Issue" for item in launch),
        "launch": launch,
        "skipped": skipped,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", type=Path, required=True)
    parser.add_argument("--plan", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = check_batch(
            json.loads(args.scope.read_text()), json.loads(args.plan.read_text())
        )
    except (OSError, ValueError) as exc:
        print(f"BATCH REJECTED: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
