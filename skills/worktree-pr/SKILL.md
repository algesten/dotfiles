---
name: worktree-pr
description: "PR-based workflow using a nested git worktree under .wt/. All work lands via squash-merged PRs from a per-branch worktree; the main folder stays parked on main. Use when starting, iterating on, or merging a PR in a repo that follows this convention."
---

## When to use

A repo where direct pushes to `origin/main` are out and **all work lands via squash-merged PRs**, each developed in its own nested worktree under `.wt/`. Multiple agents may have PRs open in parallel, so the main checkout must stay on `main` and never get `git checkout`'d out from under them. Where CI is configured to cancel superseded runs (a new push to a branch interrupts the older run), the cadence is rapid iterate-and-push rather than push-and-wait.

## Path conventions

- `<main-folder>` — wherever the repo is cloned; your launch cwd (e.g. `~/code/myrepo`). Stays on `main`.
- `<wt>` — the PR-specific worktree, conventionally `<main-folder>/.wt/<branch>` (nested under the main checkout, inside the gitignored `.wt/` dir).
- `<branch>` — pick it to read as the PR's purpose.
- `<pr#>` — the PR number once created.

Substitute your own paths — never hard-code anyone else's.

## CI status commands

The steps below check CI with the standard `gh` CLI, which works on any GitHub repo:

- **Check a PR's checks once:** `gh pr checks <pr#>`
- **Watch until they finish:** `gh pr checks <pr#> --watch`
- **Check a branch's latest run:** `gh run list --branch <branch> --limit 1`

If the project ships its own richer CI helper that can inspect GitHub check failures or watch PR CI, prefer it where noted — but the `gh` commands are the portable baseline.

## Gitignoring `.wt`

The `.wt/` directory holds nested worktrees and **must be gitignored** so worktree contents never get committed into the parent checkout. Before creating the first worktree, check:

```sh
git -C <main-folder> check-ignore .wt/ >/dev/null 2>&1 || echo "NOT IGNORED"
```

If it prints `NOT IGNORED`, add `.wt/` to the repo's `.gitignore` (commit it on a branch via the normal PR flow — don't push to `main` directly) or, to keep it out of the shared repo, add it to `.git/info/exclude` for a purely local ignore:

```sh
echo ".wt/" >> <main-folder>/.git/info/exclude
```

## Workflow

### 1. Sync the main folder and verify its CI is green

```sh
git -C <main-folder> pull --ff-only origin main
gh run list --branch main --limit 1     # confirm main's CI is green
```

The pull keeps the main folder current so Read ops reflect latest; `--ff-only` flags drift if the main folder somehow isn't on `main` or carries local commits — investigate before forcing. The CI check avoids burying an unrelated regression in your PR's CI run: green or in-progress is fine; red warrants a pause and a flag to the user before continuing.

### 2. Create the worktree (stay launched from the main folder)

The main folder is the launch cwd that binds Claude's memory path under `~/.claude/projects/`, so launching elsewhere loses memory; it also stays parked on `main` so parallel PRs don't collide on the working tree.

```sh
git -C <main-folder> worktree add -b <branch> <wt> origin/main
```

`origin/main` is fresh from step 1's pull. **Never `git checkout` in the main folder.** From here on, prefix all git ops with `git -C <wt> ...`, run build/test commands as `cd <wt> && ...` one-shots, and use absolute paths into the worktree for Read/Edit/Write. `gh` reads the repo from cwd too — run it as `cd <wt> && gh pr ...`.

### 3. Iterate

Commit (HEREDOC + `Co-Authored-By` trailer) → push → check CI:

```sh
git -C <wt> push origin <branch>
cd <wt> && gh pr checks <pr#>
```

**Do NOT wait on CI (`--watch`) during iteration.** If `gh pr checks` shows a visible failure while CI is still running on later steps, fix and push immediately — the new push cancels the old run, so waiting is wasted.

After the final push for an iteration — when you believe the PR is ready for user review or the latest requested fixes are complete — start a GitHub CI watcher in the background so you get notified immediately while staying available to the user:

```sh
cd <wt> && gh pr checks <pr#> --watch
```

Use a background worker/session for that watcher. If it reports a failure, stop the watcher if needed, diagnose from the GitHub check output and failing logs, fix, commit, push, and start a fresh background watcher for the new head. If the project has a richer CI helper, use it instead of `gh pr checks <pr#> --watch`.

First push: `cd <wt> && gh pr create` with a **Summary** body only — no Test plan section, no `🤖 Generated with [Claude Code]` attribution line. The body becomes the squash commit message verbatim, and the commit's `Co-Authored-By: Claude ...` trailer already handles attribution; double-attributing litters `git log`. Subsequent pushes update the existing PR — no re-create needed.

Standing authorization: commit and push to feature branches freely as work lands — no per-action OK. Surface the commit message + scope inline so the user can redirect, but it's informational, not a gate.

### 4. Wait for the merge signal

**Wait for the user to say "merge this"** (or equivalent). Don't squash-merge unilaterally — the user reviews what the PR became before it lands. **Merge is the only user-gated step.**

### 5. Once told to merge, drive to a clean squash-merge — steps 6–10, looping as needed

"Merge this" authorizes the **whole loop**, not a single pass. No "should I proceed?" pauses between steps 6–10. Keep going until `gh pr view <pr#> --json state` reports `MERGED`. The loop is not linear: any of these sends you back to an earlier step, and that's expected, not a reason to stop and ask —

- **CI goes red** (step 8) → fix, push, relaunch the watcher.
- **Another PR lands on `main` while you were watching CI or auditing** → your branch is now behind. Re-rebase (back to step 6), force-push, re-watch. Other agents merging in parallel makes this normal.
- **The merge is rejected** (step 9) because the branch is out of date, has conflicts, or isn't mergeable → resolve (rebase again from step 6, fix conflicts), then retry the merge.

Only stop early for something you genuinely can't resolve autonomously — a conflict whose resolution is a real design decision, or repeated CI failures you can't diagnose. Otherwise the exit condition is a confirmed clean squash-merge, full stop.

### 6. Rebase onto latest `origin/main` and kick off the CI watcher

```sh
git -C <wt> fetch origin && git -C <wt> rebase origin/main
git -C <wt> push --force-with-lease origin <branch>
```

Force-push to a PR branch after rebase is part of the standing authorization; **force-push to `main` itself remains off-limits.** Other agents' PRs may have landed since you opened this one, so rebase is mandatory, not conditional. **Right after the force-push, launch a GitHub CI watcher as a background worker** (`cd <wt> && gh pr checks <pr#> --watch`, or a richer project CI helper when available) — don't sit idle; the next step does useful work in parallel.

### 7. Audit the PR description (in parallel with the step-6 watcher)

```sh
cd <wt> && gh pr view <pr#> --json title,body
```

The PR's scope may have drifted. Update title + body via `gh api -X PATCH repos/.../pulls/<pr#>` (or `gh pr edit` if it works — the GraphQL projects-classic deprecation sometimes breaks the latter) so they describe **what the squashed commit will contain**, not the chronological journey. Title + body become the squash commit message verbatim — write the body to read as the final commit message: just a Summary section, no Test plan, no Claude attribution line.

### 8. Await the CI watcher's notification

Kicked off in step 6, ran in parallel with the step-7 audit. If green, proceed; if red, fix + push, relaunch the watcher.

### 9. Merge

```sh
cd <wt> && gh pr merge --squash <pr#>     # or --squash --auto if CI was still completing
```

If the merge is **rejected** — "not mergeable", "base branch was modified", conflicts — your branch went stale again; loop back to step 6 (rebase, force-push, re-watch CI) and retry. Don't escalate a stale-branch rejection to the user; resolving it is part of the merge mandate.

On success: the repo's `delete_branch_on_merge` removes the remote branch automatically; the local branch survives because it's checked out in the worktree (step 10 cleans it up). Verify MERGED: `gh pr view <pr#> --json state`. **Don't gate on post-merge CI for the squash commit on `main`** — once merged, merged; if main turns red after, that's a separate fix-forward.

### 10. Clean up

Run these from the main folder (the worktree is about to be removed, so don't be `cd`'d inside it):

```sh
git -C <main-folder> worktree remove <wt>
git -C <main-folder> branch -D <branch>
```

If the project provides a cleanup target that also tears down per-branch build artifacts (simulators, emulators, containers, scratch dirs), prefer it — those can cost real disk and ports if left behind, so cleanup is mandatory, not optional. The remote branch is already gone — GitHub deleted it at merge (when `delete_branch_on_merge` is enabled; otherwise `gh pr merge --squash --delete-branch` handles it).

## Guardrails

- **Don't unilaterally defer agreed scope.** Once a PR's scope is agreed, never mid-implementation decide a piece is "too much for this PR," mark it a follow-up, and call the PR ready — ask first. "Fully implemented" means it **runs end-to-end on the target surface**, not "it compiles." A `What's deferred to follow-up PRs` section requires explicit user authorization for each item.
- **Surface quality red flags as a question before opening the PR**, not as a buried follow-up.
- **Capture real exit codes** — never pipe a build/test you're judging into `tail`/`head`/`grep`; the pipeline's status is the last stage's. Redirect to a file and check `$?`.
