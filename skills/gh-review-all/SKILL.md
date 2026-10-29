---
name: gh-review-all
description: Launch parallel GitHub notification PR reviews and cursory issue triage on beast using the local scr bash function and cxlow, then detach the sessions and leave them running. Use when asked to review all inbox notifications or a selected batch this way.
---

# GitHub inbox reviews on beast

Launch one independent Codex CLI per distinct open issue or PR in the requested notification batch, using `scr` and `cxlow` on beast. PRs receive a full review; issues receive a cursory triage. Leave the agents running in detached sessions; completing their work is not part of the launch task.

## GitHub CLI only

**Use authenticated `gh` outside the sandbox for every GitHub network request. Never discover, probe, or call Safari MCP or any browser automation tool in this workflow, including as a fallback for Inbox selection or authentication.** Browser availability and browser sign-in are irrelevant; do not ask the user to sign in to a browser. If a `gh` request fails inside the sandbox, retry with `sandbox_permissions: "require_escalated"` before concluding that GitHub access failed.

For a retry from a fresh agent, use the pending user-selected batch in `state/retry-scope.json`. **Check this saved selection before asking the user to repeat an item list or screenshot.** The launch command below resolves that selection with `gh` and validates it internally; do not reconstruct the launch plan manually.

## Lock the Inbox scope

**“All” means the current GitHub Inbox, including read items. Never substitute the full notification API result or its open items for that Inbox.** A supplied Inbox screenshot or item list defines the batch. Being open, recent, subscribed, or related to an Inbox item does not make another item part of it. A broader history review requires an explicit request for that broader scope.

**“Run gh outside the sandbox” changes command execution only; it never authorizes adding items.** Preserve this boundary when updating the skill, fixing authentication, or retrying a failed command.

The [documented notification API](https://docs.github.com/en/rest/activity/notifications#list-notifications-for-the-authenticated-user) defaults to unread items; `all=true` adds read notification history without an Inbox-versus-Done selector. Neither response establishes the complete current Inbox: an empty unread response does not mean an empty Inbox, and filtering history to open items still adds unrelated work. Use the user's supplied selection or a saved pending selection, not an inferred subset of history. If neither is available, report that specific CLI scope limitation and ask only for the item list; never try a browser, invent an unsupported API filter, or broaden the batch.

Before opening terminals, cloning repositories, or starting agents:

1. Use a supplied item list/screenshot or the pending selection in `state/retry-scope.json`. When the user supplies a batch, save that selection there with `retry_status: "pending"` so a new agent can retry without the previous conversation. Record the evidence, visible item count, and exact repository/number identities independently of API results. Never generate or expand the selection from notification candidates. For example:

   ```json
   {"source":"user_screenshot","evidence":"User's attached Inbox screenshot and source conversation","retry_status":"pending","item_count":2,"items":[{"repo":"owner/repo","number":123},{"repo":"owner/repo","number":124}]}
   ```

   Allowed sources are `user_screenshot`, `user_list`, or `explicit_user_batch`. The last requires an explicit user-selected scope; do not relabel API history or browser output as user evidence. This saved state is a selected retry batch, not a claim to have freshly discovered the current Inbox. Preserve that distinction in reports. Do not reuse a `completed` or `cancelled` selection as a new Inbox.
2. Use the launch command below. It calls `prepare_batch.py` internally to perform one scoped `gh api graphql` request, including closed items so skips stay accounted for. It never requests notification history. Do not run preparation separately during a normal launch.
3. Preparation calls `check_batch.py` internally. Any extra, missing, duplicate, misidentified, or unresolved item rejects the entire plan before launch output is emitted. Correct the plan to match the evidence; never enlarge the scope file to make a rejected plan pass. The standalone preparation and checking commands are for diagnosing actual failures, not extra steps on every run.
4. Identify the selected batch in commentary, then let the script report the validated count, exact identities, PR/issue counts, and skips before opening terminals. This is a progress report, not a permission request. It launches only the checker's `launch` output. Do not reconstruct jobs or add API results afterward. An unverified or mismatched batch must launch zero agents.

Treat issues as targets in their own right; a linked PR is not an additional target unless it is also in the verified batch. Deduplicate by repository/number, skip closed issues and closed or merged PRs, and do not mark notifications read or done. Map `owner/repo` to `~/dev/repo` on beast and verify the clone's origin before assigning it. Resolve missing or ambiguous clones only for validated launch targets.

## Launch with the script

After establishing the selected scope, run this single command outside the sandbox:

```bash
python3 <skill-dir>/scripts/launch_batch.py launch
```

Use `--scope /path/to/scope.json` for an explicit selection, or `--dry-run` to resolve metadata and check clones without opening terminals. The default uses only a pending saved selection. A completed batch or recorded live agents must not be silently launched again. Missing clones or skills are reported before any terminal opens; resolve those preflight errors within the selected scope and retry.

The script owns the routine launch mechanics. It locks the selection against concurrent launches, validates metadata, checks clone origins, and starts up to four jobs concurrently using the local interactive `scr` function and remote `cxlow` alias. It records fresh private tokens, process fingerprints, and thread IDs in `state/runs/<run-id>/manifest.json` before handing over work.

Each terminal is titled immediately. The **first live Codex CLI action is `/rename <expected_name>`**, before any model prompt or review/triage. The script uses `cxlow -c 'tui.terminal_title=[]'` for that invocation only and writes the full title to the recorded PTY, avoiding Codex's automatic title abbreviation. It verifies the saved name through read-only SQLite and the visible title/detachment through scr's status protocol for that known session token. It never lists other session tokens, edits global configuration, or changes model, reasoning, or permission settings.

Only after both names match does it send one review/triage prompt. The agent's first model action is an independent saved-name readback. The script verifies task receipt/start in that exact thread, detaches with the actual Ctrl-B/d bytes, performs one final saved-name/title/process/detachment check, and returns. It marks the saved selection completed only after every item is accounted for. **When the script reports success, report the launch and stop: do not redo its checks, browse naming documentation, inspect review progress, or wait for results.**

Startup checks have bounded timeouts. A failed job is cancelled completely and retained in the manifest with its error; successful jobs remain available. Do not invent new proxy, `/title`, or configuration workarounds during a normal run. Diagnose an actual script failure instead. Parallel remote jobs are authorized by this workflow; orchestration subagents are unnecessary.

The two supporting preparation/checking scripts remain available for inspecting scope failures. To test terminal mechanics after a Codex/scr update, `launch_batch.py smoke` creates one empty CLI, verifies its name and detachment, and removes it without sending a model prompt.

## Cancel agents and persistent terminals completely

If the user corrects the batch or any launched job falls outside the verified scope, cancel the extra jobs immediately, before further investigation, skill edits, or reporting. Do not wait for reviews to finish: they can keep spending tokens.

```bash
python3 <skill-dir>/scripts/launch_batch.py status /path/to/manifest.json
python3 <skill-dir>/scripts/launch_batch.py cancel /path/to/manifest.json
```

Run these outside the sandbox too. `cancel` removes only that manifest's terminals with the local `scr kill` function and stops remaining recorded child processes only while their process fingerprints still match. Use `--item owner/repo#number` to cancel one item after startup. Ctrl-C during launch cancels that batch; the cancellation command can also request cancellation of an in-progress batch. Killing Codex alone can leave its shell and a `DETACHED` entry behind; detaching does not cancel anything.

Cancellation is complete only when **both** the job's processes are gone and its persistent session is gone from `scr list` relative to the baseline. Preserve in-scope jobs unless the user cancels all sessions; never use a broad process kill that could affect unrelated work. Do not claim complete cancellation while leftover shells or session entries remain. If the user says they killed the sessions, accept that cancellation and do not relaunch unless explicitly asked.

## Agent instructions

The launcher generates the shared instructions in `scripts/launch_batch.py`, including the exact name, thread ID, read-only database path, and GitHub-only CLI rule. It appends the appropriate task below. Preserve these task sections when editing the skill: they are the script's prompt source.

### PR task

> Adopt <PR URL> using the worktree-pr skill, then review the full PR. Read and follow that skill and use the PR's isolated worktree. Report actionable findings and relevant validation. Explicitly conclude whether you recommend continuing with the PR and explain why. Assess whether it fits the overall API and established code style, and whether it is the minimal change needed to address the problem. Before reaching that recommendation, find and consider all relevant prior discussions in GitHub issues and PRs, including review threads, and the relevant git history. Cite the evidence informing your recommendation and disclose any gaps in access or unresolved context. Do not merge.

The `worktree-pr` skill must be available on beast for PR tasks. The launch request authorizes adopting and reviewing existing PRs, not automatically merging them or applying every proposed review fix. If another agent already owns the PR's worktree, avoid resetting or modifying it; use a separate review checkout or report the conflict.

### Issue task

> Give <issue URL> a cursory triage. Read the issue and its comments, then make a few targeted searches for prior discussions, related issues or PRs, and relevant current code and git history. Check whether the reported behavior has been discussed before, is already tracked elsewhere, or has already been addressed in code. Keep this to a preliminary assessment from readily available evidence; do not attempt exhaustive validation, build a reproduction, or implement a fix. Explicitly recommend whether it appears to be a real bug or issue, explain why, and separately note whether it is already tracked or addressed. Cite the relevant discussion or code changes and disclose uncertainty when the cursory check is inconclusive. Treat this as issue triage even if a linked PR exists.

Issue triage uses the existing checkout for read-only inspection; it does not require adopting or creating a PR, changing branches, or creating a worktree.

## Report

Briefly list the verified Inbox/selected count, which PR reviews and issue triage sessions actually started, any skipped or blocked items, and whether all launched sessions were confirmed detached with correct saved and visible names. Setup-only sessions have not started a review. Tell the user they can reattach with `scr attach`; provide a recorded token only if requested. Distinguish “started” from “review or triage completed.” Report cancellation as complete only after checking both process termination and removal of the persistent terminal.
