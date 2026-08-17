# widget-claude-usage

Claude Code 5h / weekly quota in a macOS widget, via
[Terminal Widget](https://brettterpstra.com/projects/terminal-widget/).

```
5h      20%        13:47
█████░░░░░░░░░░░░░░░░░░░

wk      30%    Mon 08:24
███████░░░░░░░░░░░░░░░░░

Fable   58%    Mon 08:24
██████████████░░░░░░░░░░
```

Bars show **remaining**, coloured green (>50%) → amber (>20%) → red, with the
window reset time dimmed on the right.

The panel is pinned to a dark theme — warm `#3A2A22` on `#F2E9E4`, sharing the
palette (but not the navy background) of
[widget-codex-usage](../widget-codex-usage) so the two read as a set while
staying tellable apart. Override with `CUW_BACKGROUND` / `CUW_FOREGROUND`.

## Install

Requires `curl`, `jq`, and `terminal-widget` (`brew install --cask terminal-widget`,
or [download](https://brettterpstra.com/projects/terminal-widget/)).

```sh
ln -s ~/dev/lk/jot/martin/widget-claude-usage/claude-usage-widget ~/bin/claude-usage-widget
```

Place the widget — **use Notification Center, not the Desktop** (see Gotchas):

1. Open Notification Center → scroll to the bottom → **Edit Widgets**
2. Pick **Terminal Widget**, size **medium** or **large**
3. Right-click the placed widget → **Edit Widget** → set **Target name** to `widget1`

Check the layout without touching the API:

```sh
claude-usage-widget --demo
```

Then run it for real, and once the numbers look right, install the timer:

```sh
claude-usage-widget --dump          # verify the API parse
claude-usage-widget                 # one real update

cp ~/dev/lk/jot/martin/widget-claude-usage/io.lookback.claude-usage-widget.plist \
   ~/Library/LaunchAgents/
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/io.lookback.claude-usage-widget.plist
```

The plist hardcodes `/Users/martin` — edit the `ProgramArguments`,
`StandardErrorPath` and `PATH` if you're not me.

Verify and inspect:

```sh
launchctl print gui/$(id -u)/io.lookback.claude-usage-widget | head -20
tail -f ~/Library/Logs/claude-usage-widget.log
```

Uninstall:

```sh
launchctl bootout gui/$(id -u)/io.lookback.claude-usage-widget
rm ~/Library/LaunchAgents/io.lookback.claude-usage-widget.plist
```

## Usage

```
claude-usage-widget [--once|--watch [SECS]|--demo|--dump] [options]
```

| Flag | |
|---|---|
| `--once` | Single update (default) |
| `--watch [SECS]` | Poll forever, default 60s. Prefer launchd. |
| `--demo` | Canned numbers, no API call — for tuning appearance |
| `--dump` | Raw quota response + the normalized rows parsed from it |
| `--source WHICH` | `probe` (default) or `endpoint` — see [How it works](#how-it-works) |
| `--force` | Ignore cache freshness *and* any active backoff |
| `--target NAME` | Widget target (default `widget1`) |
| `--interval SECS` | Poll interval for `--watch` |
| `--bar-width N` | Bar cells (default 24) |

Env equivalents: `CUW_TARGET`, `CUW_INTERVAL`, `CUW_BAR_WIDTH`, `CUW_FONT`,
`CUW_FONT_SIZE`, `CUW_SOURCE`, `CUW_BACKGROUND`, `CUW_FOREGROUND`. Tune without
editing the script:

```sh
CUW_BAR_WIDTH=20 CUW_FONT_SIZE=11 claude-usage-widget --demo
```

Refresh and backoff behaviour:

| Env | Default | |
|---|---|---|
| `CUW_MIN_AGE` | `120` | Floor between probes, even under constant activity |
| `CUW_MAX_AGE` | `1800` | Probe once this stale regardless of activity |
| `CUW_CACHE` | `~/.cache/claude-usage-widget/state` | Snapshot + `.cooldown` sibling |
| `CUW_RETRIES` | `3` | In-process retries for 429 / 5xx / transport errors |
| `CUW_RETRY_MAX` | `30` | Longest one backoff may block a refresh |
| `CUW_PROBE_MODEL` | `claude-fable-5` | Model the probe asks for |
| `CUW_OI_LABEL` | `Fable` | Label for the `7d_oi` row |
| `CUW_PROJECTS` | `~/.claude/projects` | Transcript dir used as the activity signal |

## How it works

Quota comes from the `anthropic-ratelimit-unified-*` headers on an ordinary
inference request (`--source probe`, the default). The dedicated
`/api/oauth/usage` endpoint is still reachable with `--source endpoint`, but it
is no longer the default: polling a bare quota-lookup route once a minute earns
a `429` that does not clear quickly.

```
⚠ API error 429
```

### The probe

`POST /v1/messages`, `max_tokens: 1`, one `"."` — 31 input + 1 output token.
Four things were established by probing, each of which constrains the design:

* **Only `/v1/messages` emits the headers.** `/v1/models`, `/api/oauth/profile`
  and `/v1/messages/count_tokens` all answer `200` with no
  `anthropic-ratelimit-*` at all.
* **A free probe is not available.** A deliberately malformed body is rejected
  by request validation *before* the quota gateway runs, so `400` responses
  carry no headers either. Paying a token is the price of asking quietly.
* **The Claude Code system prompt is mandatory.** An OAuth token posting to
  `/v1/messages` without `"You are Claude Code, Anthropic's official CLI for
  Claude."` as the first system block gets a `400`.
* **`7d_oi` is only reported for the model it applies to.** A Haiku probe
  returns `5h` / `7d` / `overage`; the overage-included (Fable) channel appears
  only when the request is *for* Fable. Hence `CUW_PROBE_MODEL=claude-fable-5`.

A successful probe returns:

```
anthropic-ratelimit-unified-5h-utilization: 0.03
anthropic-ratelimit-unified-5h-reset: 1786123200
anthropic-ratelimit-unified-7d-utilization: 0.71
anthropic-ratelimit-unified-7d-reset: 1786136400
anthropic-ratelimit-unified-7d_oi-utilization: 0.83
anthropic-ratelimit-unified-7d_oi-reset: 1786136400
anthropic-ratelimit-unified-overage-utilization: 0.0
```

Utilization is a 0–1 fraction of quota **used**, so the bars show `100 - u*100`;
reset is plain unix seconds. Channels map to rows `5h` → `5h`, `7d` → `wk`,
`7d_oi` → `Fable` (`$CUW_OI_LABEL`). `overage` is dropped — it is the
usage-credit balance rather than a quota window, and the endpoint path never
showed it either.

### Not probing

A token per refresh only stays cheap because most refreshes do not probe. The
last snapshot is cached to `$CUW_CACHE`, and a refresh re-probes only when:

* there is no cache, or the cache is older than `CUW_MAX_AGE` (30 min); **or**
* it is older than `CUW_MIN_AGE` (2 min) **and** Claude Code has written a
  session transcript since the cache was last written.

That second clause is the useful one: these numbers cannot move unless you have
actually used Claude, and `find ~/.claude/projects -newer "$CACHE" -print -quit`
answers that in one cheap call. Idle days cost 48 probes; a hard working day
costs a few hundred. Everything else is a 70 ms re-render off disk, so leaving
launchd on a 60s tick is still fine — the countdown stays live.

The cache also knows each window's length, so a row whose reset has passed is
rolled forward and shown full without asking anyone. No activity means no
usage, so that is not a guess.

### When it is rate limited anyway

`429`, `5xx` and transport errors are retried in-process, `CUW_RETRIES` times.
`Retry-After` is honoured when present — the server knows when the window opens
and guessing shorter just burns another rejected request. Failing that, backoff
is exponential (2s, 4s, 8s).

If the server asks for longer than `CUW_RETRY_MAX` (30s), the run gives up
immediately rather than blocking a widget refresh for minutes — but it *records*
the requested delay, so the next launchd tick honours it instead of re-asking.
That cooldown lives in `$CUW_CACHE.cooldown` as `<until>\t<consecutive-fails>`;
without a `Retry-After` it escalates `CUW_MIN_AGE × 2ⁿ`, capped at `2 ×
CUW_MAX_AGE`. A success deletes it. `--force` ignores it, since that is you
asking on purpose.

Through all of this the widget keeps showing the cached numbers rather than an
error, until the cache passes `2 × CUW_MAX_AGE` and stops being evidence of
anything — at which point `⚠ rate limited — backing off` takes over.

### Auth

Auth is the OAuth access token Claude Code already stores — Keychain item
`Claude Code-credentials`, falling back to `~/.claude/.credentials.json`. The
token is **re-read on every poll**, so Claude Code's own refresh keeps it valid
and this script never implements a refresh flow. On 401 the widget shows
`⚠ token expired — run claude` rather than going quietly stale.

**Never echo the credential blob.** It holds every MCP server's OAuth tokens
next to the Claude one, so `read_token` reports *which* step failed and never
the value. Note also that several MCP entries have an empty `accessToken`, so a
recursive "first `accessToken`" search silently returns `""` — read
`.claudeAiOauth.accessToken` by path.

### The endpoint source

`--source endpoint` does a `GET /api/oauth/usage` — the same call the CLI's
`/usage` command makes. Confirmed against the Claude Code 2.1.224 binary:

```js
Bi.get("/api/oauth/usage", { timeout: 5000,
  headers: { "Content-Type": "application/json" }, refreshOAuth: true })
```

It costs no tokens and names each scoped model properly, which is why it is
worth keeping for `--dump` and for a spot check. It is just not something you
can poll. The useful part of the response is a `limits` array (alongside
top-level `five_hour` / `seven_day` objects carrying the same numbers, and an
`extra_usage` block for credits):

```json
{ "limits": [
    { "kind": "session",       "group": "session", "percent": 88,
      "severity": "warning", "resets_at": "2026-08-07T12:20:00.499402+00:00",
      "scope": null, "is_active": true },
    { "kind": "weekly_all",    "group": "weekly",  "percent": 71, … },
    { "kind": "weekly_scoped", "group": "weekly",  "percent": 84,
      "scope": { "model": { "id": null, "display_name": "Fable" } }, … } ] }
```

Two things to note: `percent` is **used**, 0–100, so the bars show `100 -
percent`; and `resets_at` is **ISO-8601 with fractional seconds and an
offset**, which `fromdateiso8601` rejects — the `epoch` jq helper strips the
fraction and normalises the offset to `Z`.

Rows are matched *structurally* rather than against a fixed schema: any object
carrying a reset timestamp plus a utilization number, bucketed by `kind`
(`five_hour|5h|session…` → 5h, `seven_day|weekly|week|7d` → wk, anything with
a `scope.model` → a per-model row labelled from `scope.model.display_name`).
Utilization is auto-detected as 0–1 or 0–100. This is deliberate: the endpoint
is undocumented and its shape has already shifted once (the `7d_oi` channel is
recent), so it degrades to `⚠ unrecognized API response` instead of silently
showing wrong numbers.

For reference, the label map inside the 2.1.224 binary — note that
`seven_day_opus` and `seven_day_overage_included` are *distinct* channels, and
it's the latter that is Fable:

| `kind` | Label |
|---|---|
| `five_hour` | session limit |
| `seven_day` | weekly limit |
| `seven_day_opus` | Opus limit |
| `seven_day_sonnet` | Sonnet limit |
| `seven_day_overage_included` | Fable 5 limit |
| `overage` | usage credit limit |

## Gotchas

**Put it in Notification Center, not on the Desktop.** Desktop widgets are
rendered de-saturated by macOS until you click the desktop, so the
green/amber/red is invisible most of the time. Desktop placements also carry
per-display coordinates — placements made while docked with the lid open end
up off-canvas when you clamshell. Notification Center has neither problem.

If you do want it on the Desktop, System Settings → Desktop & Dock → Widgets →
**Show widgets: On Desktop** must be on (`StandardHideWidgets = 0` in
`com.apple.WindowManager`), and re-add the widget in the display configuration
you actually use.

**`--background-mode` is deliberate.** It skips only the LaunchServices URL
handoff (the focus-stealing part); the SIGUSR1 and Darwin notification still
fire, which is what refreshes an already-running app. Without it a 60s poller
steals focus every minute.

**The probe spends the quota it reports.** 32 tokens a time, against the same
Fable weekly window shown in the third row. At the default cadence that is
noise, but do not lower `CUW_MIN_AGE` to something like 10s and expect it to
stay noise — the widget would start moving its own needle.

**The activity signal is transcript mtime, not prompts.** `~/.claude/history.jsonl`
updates once per submitted prompt, which would miss a long agentic run burning
quota off a single prompt. The per-session `*.jsonl` transcripts are written
continuously, so those are what `claude_active()` watches. Point `CUW_PROJECTS`
elsewhere if your setup differs; a missing directory is treated as "active",
which degrades to plain `CUW_MIN_AGE` polling rather than to silence.

**Rows are fixed on the probe path.** The headers carry channel ids, not display
names, so the three rows are hardcoded and `7d_oi` is labelled from
`$CUW_OI_LABEL`. `--source endpoint` is the one that adapts: it emits a row per
`weekly_scoped` entry, labelled from `scope.model.display_name`, which on a plan
with more scoped models crowds a medium widget — trim with `--bar-width`, a
large widget, or by dropping the `select(.model != null)` branch from
`NORMALIZE_JQ`.

**Both sources are undocumented.** The header names are as unofficial as the
endpoint's JSON. The parse is deliberately narrow — a channel that stops
appearing simply loses its row, and if nothing parses at all the widget shows
`⚠ unrecognized API response` instead of confidently wrong numbers.
