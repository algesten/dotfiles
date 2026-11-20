# Pull request session names

- Before reviewing a PR, fetch its number and title and rename the current
  Codex session to `PR #<number>: <title>`, preserving the title verbatim.
- After updating a PR's title or description, sync the session name using
  its final title.
- Use `thread/name/set` with `CODEX_THREAD_ID`, preferably through the running
  app server (`codex app-server proxy`). A separate app-server process updates
  the saved name but may leave the terminal title stale until resume.

# Function order

Order functions depth-first by first mention, starting with the entry point.
When adding functions to existing code, place them among the existing functions
according to the same order.

# Monitoring shorthand

When the user writes `m` by itself, monitor the active subagents until their work
converges.
