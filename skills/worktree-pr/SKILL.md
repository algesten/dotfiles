---
name: worktree-pr
description: "Explicitly requested PR-based workflow using a nested git worktree under .wt/. All work lands via squash-merged PRs from a per-branch worktree; the main folder stays parked on main. Use only when the user asks to use the worktree-pr workflow at the outset of a change; never activate it retroactively for work already started on main."
---

## Activation boundary

Use this workflow only when the user explicitly asks for `worktree-pr` at the outset, before the change begins. Do not activate it merely because the repository follows this convention or because the user later asks to commit or push. If a change started on `main` and the user later asks to commit or push it, stay on `main` and perform that request there; do not move the change into a worktree or retroactively open a PR unless the user explicitly changes direction.

## When to use

A repo where direct pushes to `origin/main` are out and **all work lands via squash-merged PRs**, each developed in its own nested worktree under `.wt/`. Multiple agents may have PRs open in parallel, so the main checkout must stay on `main` and never get `git checkout`'d out from under them. CI does not run on every push: a branch run is requested explicitly at a ready point after local verification (see "CI request policy"), and `main` is checked on a catch-up schedule, so the cadence is iterate locally, push freely, request CI rarely.

## Path conventions

- `<main-folder>` — wherever the repo is cloned; your launch cwd (e.g. `~/code/myrepo`). Stays on `main`.
- `<wt>` — the PR-specific worktree, conventionally `<main-folder>/.wt/<branch>` (nested under the main checkout, inside the gitignored `.wt/` dir).
- `<branch>` — pick it to read as the PR's purpose.
- `<pr#>` — the PR number once created.
- `<head-remote>` — the remote that owns an existing PR branch when taking over someone else's PR; usually `origin` for same-repo branches, or a temporary remote for fork PRs.
- `<head-ref>` — the existing PR's head branch name when taking over someone else's PR.

Substitute your own paths — never hard-code anyone else's.

## CI model: request-only branches, scheduled main

Detect which model the repo uses by reading its workflow file(s) under `.github/workflows/` once at the start (`grep -l workflow_dispatch`, and whether `pull_request:` is a trigger).

- **Request-only** (no `pull_request` trigger; `workflow_dispatch` present; `main` runs on a schedule): nothing runs on push. A branch run happens only when you ask for it. This is the model the steps below assume.
- **Automatic** (`pull_request` trigger): every push runs CI; the "request a run" steps below collapse to "push", and the watcher is `gh pr checks <pr#> --watch`.

Commands for the request-only model:

```sh
cd <wt> && gh workflow run <workflow-file> --ref <branch>          # request a run on the pushed head
sleep 10 && gh run list --branch <branch> --workflow <workflow-file> --limit 1 --json databaseId,status,headSha
gh run watch <run-id> --exit-status                                 # watch it (background worker)
gh run view <run-id> --log-failed                                   # diagnose a red run
gh run list --branch main --workflow <workflow-file> --limit 1     # main's latest run
```

Dispatched runs attach to the head SHA, so they also appear in `gh pr checks <pr#>` once a PR exists. Confirm the run's `headSha` matches what you pushed — a dispatch races a push that has not landed yet.

If the project ships its own richer CI helper that can request or watch runs, prefer it — the `gh` commands are the portable baseline.

## CI request policy — confident, proportionate, rare

A CI run costs real money and queue time (macOS and other large runners are metered at a multiple), so requests are deliberate:

1. **Earn reasonable confidence locally first.** Before requesting a run, run the local equivalents of the CI steps the change can actually break. Read the workflow once to know what those steps are (formatting, lint with warnings denied, the affected tests, repo guard scripts, shell syntax, a cross-target `cargo check`). Capture real exit codes. A request is a statement that you expect green.
2. **Proportionate, not exhaustive.** Do not run every large, slow check locally for every small change. Pick the checks by blast radius: a docs/comment change needs the guard script that asserts doc contents (if any) and nothing else; a one-crate Rust change needs fmt, clippy and that crate's tests, not a full cross-compile of every platform; a workflow/script/build change is the case that needs the broad local pass and the CI run itself.
3. **At most two requests per PR, never per push.** Request once when the PR is ready for user review, and once after the pre-merge rebase — skip the second when the rebase was a no-op on top of the already-green head (same tree, nothing landed on `main` in between). Iterating on review feedback does not re-request until the next ready point.
4. **Skip the request when CI cannot learn anything.** A change whose every CI-visible effect was verified locally (pure docs/comments with the guard script run, a trivially mechanical rename with tests run) needs no branch run; say so in the ready message. `main`'s scheduled run remains the backstop after merge.
5. **Red run → fix locally, then re-request.** Reproduce the failing step locally, fix, verify that step passes, push, request again. Do not push-and-request speculatively.

## Gitignoring `.wt`

The `.wt/` directory holds nested worktrees and **must be gitignored** so worktree contents never get committed into the parent checkout. Before creating the first worktree, check:

```sh
git -C <main-folder> check-ignore .wt/ >/dev/null 2>&1 || echo "NOT IGNORED"
```

If it prints `NOT IGNORED`, add `.wt/` to the repo's `.gitignore` (commit it on a branch via the normal PR flow — don't push to `main` directly) or, to keep it out of the shared repo, add it to `.git/info/exclude` for a purely local ignore:

```sh
echo ".wt/" >> <main-folder>/.git/info/exclude
```

## Local worktree handling

Because the same PR may be handled from multiple machines, do not assume the PR worktree already exists locally, and do not assume an existing local worktree is current with GitHub. Before creating a worktree for an existing PR, inspect local worktrees and prefer reusing the PR's existing `<wt>` when present:

```sh
git -C <main-folder> worktree list
cd <main-folder> && gh pr view <pr#> --json headRefName,headRepositoryOwner,headRepository,isCrossRepository,url
```

If a local worktree for the PR branch is present, resume it instead of creating another `.wt/` entry for the same PR. Fetch the PR head, verify the worktree has no uncommitted work you would overwrite, then resync the local branch to the PR head:

```sh
git -C <wt> status --short
git -C <main-folder> fetch <head-remote> <head-ref>
git -C <wt> switch <branch>
git -C <wt> reset --hard FETCH_HEAD
```

Only use `reset --hard` when the worktree is clean or its local changes are known to be disposable; otherwise inspect and preserve the local work first. For same-repo PRs, `<head-remote>` is usually `origin`. For fork PRs, add or reuse the temporary fork remote before fetching, as described in step 2b.

If no suitable local worktree exists, create one using the workflow below. Avoid creating multiple worktrees for the same PR unless there is a deliberate reason, and call that reason out to the user before doing it.

## Workflow

### 1. Sync the main folder and verify its CI is green

```sh
git -C <main-folder> pull --ff-only origin main
gh run list --branch main --limit 1     # confirm main's last run is green
```

The pull keeps the main folder current so Read ops reflect latest; `--ff-only` flags drift if the main folder somehow isn't on `main` or carries local commits — investigate before forcing. The CI check avoids burying an unrelated regression in your PR's CI run: green, in-progress, or a skipped catch-up run ("no change since last run") is fine; red warrants a pause and a flag to the user before continuing. Under the scheduled model main's latest run may be up to one schedule window behind the newest commit; that is expected.

### 2. Create the worktree (stay launched from the main folder)

The main folder is the launch cwd and stays parked on `main` so parallel PRs don't collide on the working tree.

```sh
git -C <main-folder> worktree add -b <branch> <wt> origin/main
```

`origin/main` is fresh from step 1's pull. **Never `git checkout` in the main folder.** From here on, prefix all git ops with `git -C <wt> ...`, run build/test commands as `cd <wt> && ...` one-shots, and use absolute paths into the worktree for Read/Edit/Write. `gh` reads the repo from cwd too — run it as `cd <wt> && gh pr ...`.

### 2b. Or take over an existing PR

When the user wants you to finish someone else's open PR, keep the same invariant: the main folder stays on `main`, and all edits happen in a nested worktree. First inspect where the PR branch lives:

```sh
cd <main-folder> && gh pr view <pr#> --json headRefName,headRepositoryOwner,headRepository,maintainerCanModify,isCrossRepository,url
```

If the branch is in the same repo, fetch it and create the worktree from that head:

```sh
git -C <main-folder> fetch origin <head-ref>
git -C <main-folder> worktree add <wt> FETCH_HEAD
```

If the branch is from a fork, confirm `maintainerCanModify` is true before making commits. Add/fetch a temporary remote for the fork, then create the worktree from that fork head:

```sh
git -C <main-folder> remote add <head-remote> <fork-url>
git -C <main-folder> fetch <head-remote> <head-ref>
git -C <main-folder> worktree add <wt> FETCH_HEAD
```

Immediately create or attach a local branch in the worktree so later commits and force-pushes have a named branch. For takeover PRs, prefer using the PR's `<head-ref>` as the local `<branch>` unless there is already a conflicting local branch:

```sh
git -C <wt> switch -c <branch>
```

For takeover PRs, your commits may be additional tweaks on top of someone else's work, but every later PR-description update must describe the **entire PR as it will be squash-merged**, not just your extra commits. Push back to the PR head, not a replacement branch: same-repo PRs use `origin <branch>` only when `<branch>` equals `<head-ref>`; otherwise use `origin <branch>:<head-ref>`. Fork PRs use `<head-remote> <branch>:<head-ref>`.

### 3. Iterate

Commit → verify locally → push. Pushing does not start CI:

```sh
git -C <wt> push origin <branch>
```

For takeover PRs whose local `<branch>` differs from `<head-ref>`, substitute the push target with `git -C <wt> push origin <branch>:<head-ref>` for same-repo PRs, or `git -C <wt> push <head-remote> <branch>:<head-ref>` for fork PRs, so the existing PR updates in place.

**Do not request CI during iteration.** Local checks are the feedback loop while the change is moving; a CI run on a head you are about to replace is wasted money.

After the final push for an iteration — when you believe the PR is ready for user review or the latest requested fixes are complete — apply the CI request policy: run the proportionate local checks, then, if the change can affect anything CI checks beyond what you verified, request one run and watch it in a background worker so you get notified while staying available to the user:

```sh
cd <wt> && gh workflow run <workflow-file> --ref <branch>
sleep 10 && gh run list --branch <branch> --workflow <workflow-file> --limit 1 --json databaseId,headSha
gh run watch <run-id> --exit-status        # background worker
```

If it reports a failure, diagnose with `gh run view <run-id> --log-failed`, reproduce and fix locally, commit, push, and request a fresh run for the new head. If the change needed no CI run, say which local checks stood in for it in the ready message. If the project has a richer CI helper, use it instead of the `gh` commands.

First push for new PRs: `cd <wt> && gh pr create` with a **Summary** body only — no Test plan section, no generated-by or co-author attribution lines, and **no follow-up / deferred-work / "next PR" / "known limitation" notes** (see the body-is-the-commit-message guardrail below). The body becomes the squash commit message verbatim. Subsequent pushes update the existing PR — no re-create needed. Takeover PRs already have a PR; push to the existing head branch instead of creating a replacement PR.

Standing authorization: commit and push to feature branches freely as work lands — no per-action OK. Surface the commit message + scope inline so the user can redirect, but it's informational, not a gate.

### 4. Wait for the merge signal

**Wait for the user to say "merge this"** (or equivalent). Don't squash-merge unilaterally — the user reviews what the PR became before it lands. **Merge is the only user-gated step.**

### 5. Once told to merge, drive to a clean squash-merge — steps 6–10, looping as needed

"Merge this" authorizes the **whole loop**, not a single pass. No "should I proceed?" pauses between steps 6–10. Keep going until `gh pr view <pr#> --json state` reports `MERGED`. The loop is not linear: any of these sends you back to an earlier step, and that's expected, not a reason to stop and ask —

- **CI goes red** (step 8) → reproduce and fix locally, push, request a fresh run, relaunch the watcher.
- **Another PR lands on `main` while you were watching CI or auditing** → your branch is now behind. Re-rebase (back to step 6), force-push, re-request, re-watch. Other agents merging in parallel makes this normal.
- **The merge is rejected** (step 9) because the branch is out of date, has conflicts, or isn't mergeable → resolve (rebase again from step 6, fix conflicts), then retry the merge.

Only stop early for something you genuinely can't resolve autonomously — a conflict whose resolution is a real design decision, or repeated CI failures you can't diagnose. Otherwise the exit condition is a confirmed clean squash-merge, full stop.

### 6. Rebase onto latest `origin/main` and request the pre-merge run

```sh
git -C <wt> fetch origin && git -C <wt> rebase origin/main
git -C <wt> push --force-with-lease origin <branch>
```

For takeover PRs whose local `<branch>` differs from `<head-ref>`, use `git -C <wt> push --force-with-lease origin <branch>:<head-ref>` for same-repo PRs, or `git -C <wt> push --force-with-lease <head-remote> <branch>:<head-ref>` for fork PRs. Force-push to a PR branch after rebase is part of the standing authorization; **force-push to `main` itself remains off-limits.** Other agents' PRs may have landed since you opened this one, so rebase is mandatory, not conditional. **Right after the force-push, decide whether the pre-merge run is needed:** if the rebase was a no-op on the head that already ran green (nothing landed on `main` since, tree unchanged), reuse that result and skip; otherwise request a run (`gh workflow run <workflow-file> --ref <branch>`) and launch `gh run watch <run-id> --exit-status` as a background worker — don't sit idle; the next step does useful work in parallel. A rebase that only replays onto unrelated `main` commits still counts as a new head: the combination has not been tested.

### 7. Audit the PR description (in parallel with the step-6 watcher)

```sh
cd <wt> && gh pr view <pr#> --json title,body
```

The PR's scope may have drifted. Update title + body via `gh api -X PATCH repos/.../pulls/<pr#>` (or `gh pr edit` if it works — the GraphQL projects-classic deprecation sometimes breaks the latter) so they describe **what the squashed commit will contain**, not the chronological journey. For takeover PRs, this means describing the **entire PR**, including the original author's changes and your later fixes, not just the additional tweaks you made. Title + body form the descriptive portion of the squash commit message — write the body as just a Summary section, with no Test plan, generated-by lines, co-author attribution lines, or **follow-up / deferred / "next PR" notes** (see the guardrail below). If a forward-pointer or attribution trailer crept into the body during iteration, strip it now — the merge step appends the audited attribution block.

Before merging, inspect every commit in `origin/main..HEAD` and collect its `Co-Authored-By:` trailers. Build the final squash-commit body from the audited PR body, followed by one blank line and the deduplicated trailers at the very bottom. Treat trailers with the same email address case-insensitively as the same attributor, retain one canonical spelling for each, and preserve each distinct attributor exactly once. Remove duplicate or misplaced copies rather than allowing GitHub's generated squash message to repeat them.

### 7b. Audit `CHANGELOG.md` when present

If `<main-folder>/CHANGELOG.md` exists, ensure the PR includes an appropriate changelog line before merge. Read nearby existing entries and follow the repo's format to the letter:

- Preserve section placement, bullet style, prefixes, wrapping, and line length.
- Incorporate the PR number exactly the way surrounding entries do; don't invent a new `#<pr#>` or `PR <pr#>` style if the file uses another convention.
- The entry must describe the user-visible change from the whole PR, not merely your additional tweaks on a takeover PR.
- If the PR is not user-visible and the changelog has a clear convention for skipping such entries, follow that convention; otherwise ask before omitting it.

Commit and push any changelog correction; a changelog-only head needs no new CI request beyond the local guard checks, unless the project's CI asserts changelog contents.

### 8. Await the CI watcher's notification

Kicked off in step 6 (or reused from the ready-point run), ran in parallel with the step-7 audit. If green, proceed; if red, reproduce and fix locally, push, request a fresh run, relaunch the watcher.

### 9. Merge

Use the audited PR title as `<final-subject>` and the step-7 body plus its deduplicated attribution block as `<final-body>`, then pass both explicitly so GitHub cannot synthesize repeated trailers from the individual commits:

```sh
cd <wt> && gh pr merge --squash <pr#> --subject <final-subject> --body <final-body>
# Add --auto if CI is still completing.
```

Immediately before running the merge, verify that `<final-body>` contains each unique `Co-Authored-By:` attributor exactly once and that all such trailers are contiguous at the bottom, after a blank line.

If the merge is **rejected** — "not mergeable", "base branch was modified", conflicts — your branch went stale again; loop back to step 6 (rebase, force-push, re-request CI if the head changed, and re-watch it) and retry. Don't escalate a stale-branch rejection to the user; resolving it is part of the merge mandate.

On success: the repo's `delete_branch_on_merge` removes the remote branch automatically; the local branch survives because it's checked out in the worktree (step 10 cleans it up). Verify MERGED: `gh pr view <pr#> --json state`. **Don't gate on post-merge CI for the squash commit on `main`** — once merged, merged; main's scheduled catch-up run covers it, and if that turns red it's a separate fix-forward.

### 10. Clean up

Run these from the main folder (the worktree is about to be removed, so don't be `cd`'d inside it):

```sh
git -C <main-folder> worktree remove <wt>
git -C <main-folder> branch -D <branch>
```

If the project provides a cleanup target that also tears down per-branch build artifacts (simulators, emulators, containers, scratch dirs), prefer it — those can cost real disk and ports if left behind, so cleanup is mandatory, not optional. The remote branch is already gone — GitHub deleted it at merge (when `delete_branch_on_merge` is enabled; otherwise `gh pr merge --squash --delete-branch` handles it).

After cleanup, if the main folder is still on `main` and clean, pull it forward so the parked checkout contains the squash-merged result and any other latest changes:

```sh
git -C <main-folder> status --short
git -C <main-folder> branch --show-current
git -C <main-folder> pull --ff-only origin main
```

If the main folder is dirty, do not pull over local changes; report that the final main-folder refresh was skipped because the checkout was not clean.

## Guardrails

- **The PR body is the descriptive portion of the commit message — it states only what the change is, never what comes next.** At merge time, step 9 appends only the deduplicated `Co-Authored-By:` block. The body itself must contain *only* a description of the change that landed: no attribution trailers, "Known follow-up", "next PR", "deferred to a later PR", "known limitation", "TODO", or any other forward-pointer — not even a single sentence. Those read fine in a GitHub PR but are wrong in `git log` forever. Deferred/follow-up work goes where the project tracks it (a STATUS-style doc, an issue, a backlog) — **never** the PR body. This trap is one-way: once squashed, the only way to remove the note is `git commit --amend` + **force-push to `main`, which is off-limits** — so it can't be cleanly undone. Catch it at write time (step 3) and again at the pre-merge audit (step 7). If you have a genuine follow-up to record, mention it to the user in chat and/or add it to the tracker; keep it out of the commit message.
- **Don't unilaterally defer agreed scope.** Once a PR's scope is agreed, never mid-implementation decide a piece is "too much for this PR," mark it a follow-up, and call the PR ready — ask first. "Fully implemented" means it **runs end-to-end on the target surface**, not "it compiles." A `What's deferred to follow-up PRs` section requires explicit user authorization for each item.
- **Surface quality red flags as a question before opening the PR**, not as a buried follow-up.
- **Capture real exit codes** — never pipe a build/test you're judging into `tail`/`head`/`grep`; the pipeline's status is the last stage's. Redirect to a file and check `$?`.
