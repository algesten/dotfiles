---
name: review-cycle
description: "Run an iterative adversarial PR review loop with fresh subagents. Each reviewer inspects the full PR, posts actionable findings, and commits failing regression tests when a defect can be demonstrated; the primary agent fixes validated problems and repeats until a clean independent review. Use when the user says `run review-cycle skill`, asks for a review cycle, or requests adversarial subagent review until convergence."
---

# Review Cycle

Drive an open pull request to a clean independent review. The primary agent owns orchestration and fixes; a fresh subagent acts as the adversarial reviewer in every round.

## Preconditions

- Identify the current PR, its base branch, and its head branch. Work on the PR's existing worktree and branch.
- Read the repository instructions and gather the original brief, acceptance criteria, linked issue, PR description, and relevant discussion. Give the reviewer the best available statement of intent; do not reduce that intent to a checklist invented by this skill.
- Start each round with committed prior-round changes. Do not overwrite unrelated user changes. If uncommitted changes make reviewer commits unsafe, preserve them or pause and explain the conflict.
- Confirm that the user has authorized posting to and pushing commits onto the PR. Invoking this skill is that authorization.

## Review Loop

Repeat the following sequence until the convergence condition is met.

### 1. Launch a fresh adversarial reviewer

Spawn one new subagent for the round. Never reuse a reviewer from an earlier round; independence is part of the check.

Give the reviewer the PR number, base and head refs, repository path, repository instructions, original brief, acceptance criteria, linked context, and prior review discussion. Tell it the desired outcome, then leave the review approach and areas of investigation to its judgment.

Require only that the reviewer:

- Review the complete cumulative PR against its brief and intended outcome, not only the latest fix or the textual diff. It may inspect any surrounding code, history, documentation, behavior, or other context it considers relevant.
- Decide for itself what deserves scrutiny. Examples or findings from earlier rounds are context, not an exhaustive taxonomy or a restriction on the review.
- Substantiate actionable findings with enough evidence to distinguish them from speculation. When useful, check a suspected finding against git history, earlier PRs, and local repository documentation to understand prior decisions and confirm that it is genuinely inconsistent with the project's intent.
- For each substantiated problem where a regression test is useful, add the smallest test that demonstrates the problem on the current PR head and captures the intended outcome. Do not weaken or delete existing tests.
- Modify test code or test fixtures only. Do not fix production code, generated files, or unrelated issues.
- Group its regression tests into a clearly named commit, push that commit to the PR head, and report the commit SHA. A deliberately failing test commit is expected at this stage.
- Post each location-specific finding as an inline GitHub review comment attached to the most relevant changed row, so the discussion stays linked to the code. Include the supporting evidence and regression-test commit when applicable, and say when no useful regression test applies. Use a standalone PR comment only for a finding that genuinely applies to the PR as a whole rather than to a specific row.
- If there are no actionable findings, post a clean-review comment and make no commit.

The reviewer must not amend, rebase, reset, force-push, merge, or change the PR description.

### 2. Adjudicate the findings

Wait for the reviewer to finish. Inspect every finding and any test commit rather than accepting the review mechanically.

- Treat a regression test as evidence only when it fails because of the claimed defect and expresses intended behavior.
- Correct invalid or overly coupled tests before proceeding, and explain rejected false positives in a PR comment when useful to future reviewers.
- Preserve valid reviewer regression tests in the PR history; do not squash them away during the cycle unless the repository's required workflow later squashes the whole PR.

### 3. Fix validated problems

Fix all validated findings in production code. Run the new regression tests first, then the relevant broader test, lint, type-check, and build commands. Commit and push the fixes to the same PR.

After pushing, reply to every originating GitHub review comment or PR comment with the finding's disposition. For a fix, include the fix commit and relevant validation result; for a rejected finding, briefly explain the evidence. Reply in the existing thread rather than starting a duplicate discussion. Do not resolve review conversations—the reviewer or human owner decides when a thread is resolved.

Do not stop merely because the reported tests now pass. The next reviewer must inspect the entire updated PR for incomplete fixes and regressions introduced by the repair.

### 4. Start the next round

Launch another fresh subagent and repeat. Include prior review-comment links and the new head SHA for context, but ask for an independent review rather than limiting it to earlier findings.

## Convergence and Stop Rules

The cycle converges only when:

- a fresh reviewer finds no actionable gap between the complete updated PR and its brief, intended outcome, or repository quality bar;
- it adds no regression-test commit; and
- the relevant validation suite passes on the final head.

Style preferences, optional refactors, and explicitly non-blocking suggestions do not prevent convergence. Report them separately without extending the loop.

If the same unresolved blocker survives three consecutive rounds, or progress requires a product/design decision, unavailable secret, external permission, or destructive action, stop and ask the user for the smallest decision or access needed. Do not claim convergence.

## Final Report

When converged, tell the user:

- how many independent review rounds ran;
- which defects and regression tests were added;
- the final validation commands and results; and
- the final PR URL and head SHA.

Do not merge unless the user separately asks to merge.
