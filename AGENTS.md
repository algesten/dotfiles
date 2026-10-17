# Pull request session names

- Before reviewing a PR, fetch its number and title and rename the current
  Codex session to `PR #<number>: <title>`, preserving the title verbatim.
- After updating a PR's title or description, sync the session name using
  its final title.
- Use `thread/name/set` with `CODEX_THREAD_ID`, preferably through the running
  app server (`codex app-server proxy`). A separate app-server process updates
  the saved name but may leave the terminal title stale until resume.
