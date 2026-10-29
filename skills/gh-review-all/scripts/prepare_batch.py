#!/usr/bin/env python3
"""Resolve a user-selected batch using gh only; never launch agents or browsers."""

import argparse
import json
from pathlib import Path
import subprocess
import sys

from check_batch import check_batch, identity, validate_scope


DEFAULT_SCOPE = Path(__file__).resolve().parent.parent / "state" / "retry-scope.json"


def prepare_batch(scope_path, pending_only=False):
    scope = json.loads(Path(scope_path).read_text())
    validate_scope(scope)
    if pending_only and scope.get("retry_status") != "pending":
        raise ValueError("The saved retry batch is not pending; supply a new user selection")

    repos, seen = {}, set()
    for item in scope["items"]:
        key = identity(item)
        if key not in seen:
            repos.setdefault(item["repo"], []).append(item["number"])
            seen.add(key)

    fields = []
    for index, (repo, numbers) in enumerate(repos.items()):
        owner, name = repo.split("/")
        items = " ".join(
            f"i{number}: issueOrPullRequest(number: {number}) {{ __typename "
            "... on Issue { number title url state } "
            "... on PullRequest { number title url state } }"
            for number in numbers
        )
        fields.append(
            f"r{index}: repository(owner: {json.dumps(owner)}, name: {json.dumps(name)}) "
            f"{{ nameWithOwner {items} }}"
        )

    plan = {"items": []}
    if fields:
        query = "query { " + " ".join(fields) + " }"
        result = subprocess.run(
            ["gh", "api", "graphql", "--input", "-"],
            input=json.dumps({"query": query}),
            text=True,
            capture_output=True,
        )
        if result.returncode:
            detail = result.stderr.strip() or "GitHub CLI request failed"
            raise ValueError(f"gh failed: {detail}")
        response = json.loads(result.stdout)
        if response.get("errors"):
            details = "; ".join(error.get("message", "GraphQL error") for error in response["errors"])
            raise ValueError(f"gh returned GraphQL errors: {details}")

        for index, (repo, numbers) in enumerate(repos.items()):
            repo_data = response.get("data", {}).get(f"r{index}")
            if not isinstance(repo_data, dict) or not repo_data.get("nameWithOwner"):
                raise ValueError(f"gh could not resolve repository {repo}")
            for number in numbers:
                item = repo_data.get(f"i{number}")
                if not isinstance(item, dict):
                    raise ValueError(f"gh could not resolve {repo}#{number}")
                plan["items"].append(
                    {
                        "repo": repo_data["nameWithOwner"],
                        "number": item.get("number"),
                        "kind": item.get("__typename"),
                        "state": item.get("state"),
                        "title": item.get("title"),
                        "url": item.get("url"),
                    }
                )

    checked = check_batch(scope, plan)
    checked["scope_path"] = str(Path(scope_path).resolve())
    checked["scope_source"] = scope["source"]
    return checked


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", type=Path, help="Explicit user selection; otherwise use the pending retry")
    args = parser.parse_args()
    scope_path = args.scope or DEFAULT_SCOPE
    try:
        if not scope_path.is_file():
            raise ValueError(
                "No saved Inbox selection. Supply --scope with the user's item list. "
                "GitHub's read-notification history is not an Inbox selection."
            )
        result = prepare_batch(scope_path, pending_only=args.scope is None)
    except (OSError, ValueError, TypeError) as exc:
        print(f"BATCH PREPARATION BLOCKED: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
