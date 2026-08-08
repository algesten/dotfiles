# widget-codex-usage

Codex weekly quotas in a macOS widget, via Terminal Widget.

```text
wk      72%        Tue 14:20
█████████████████░░░░░░░

Spark   38%        Thu 13:33
█████████░░░░░░░░░░░░░░░
```

Bars show **remaining** allowance, coloured green (>50%) → amber (>20%) →
red, with the reset time dimmed on the right. The default “Graphite Night”
theme uses a quiet charcoal background with soft, desaturated status colours.

## Install

Requires `codex`, `jq`, and `terminal-widget`, plus an authenticated Codex CLI
session.

```sh
ln -s ~/dev/dotfiles/widget-codex-usage/codex-usage-widget ~/bin/codex-usage-widget
```

Add a medium Terminal Widget in Notification Center and set its target name to
`widget2` (`widget1` is used by the sibling Claude widget). Then test it:

```sh
codex-usage-widget --demo
codex-usage-widget --dump
codex-usage-widget
```

Install the one-minute launchd timer:

```sh
cp ~/dev/dotfiles/widget-codex-usage/io.lookback.codex-usage-widget.plist \
   ~/Library/LaunchAgents/
launchctl bootstrap gui/$(id -u) \
  ~/Library/LaunchAgents/io.lookback.codex-usage-widget.plist
```

Verify or uninstall:

```sh
launchctl print gui/$(id -u)/io.lookback.codex-usage-widget | head -20
tail -f ~/Library/Logs/codex-usage-widget.log
launchctl bootout gui/$(id -u)/io.lookback.codex-usage-widget
```

## Usage

```text
codex-usage-widget [--once|--watch [SECS]|--demo|--dump] [options]
```

| Flag | Purpose |
|---|---|
| `--once` | Single update (default) |
| `--watch [SECS]` | Poll continuously; prefer launchd |
| `--demo` | Render canned values without the network |
| `--dump` | Print the raw and normalized usage response |
| `--force` | Ignore cache freshness and query now |
| `--target NAME` | Widget target; default `widget2` |
| `--bar-width N` | Bar cells; default 24 |

Environment equivalents use the `CXUW_` prefix: `CXUW_TARGET`,
`CXUW_INTERVAL`, `CXUW_BAR_WIDTH`, `CXUW_FONT`, `CXUW_FONT_SIZE`,
`CXUW_BACKGROUND`, `CXUW_FOREGROUND`, `CXUW_CACHE`, `CXUW_MIN_AGE`,
`CXUW_MAX_AGE`, and `CXUW_SESSIONS`. Colours accept the same formats as
Terminal Widget, including hex values such as `#1F3454`.

## How it works

The script starts the installed Codex app-server and calls the authenticated
`account/rateLimits/read` method—the same snapshot used by the Codex TUI. This
requires the network but does **not** make an inference request or spend model
tokens. The response contains `usedPercent`, `windowDurationMins`, and
`resetsAt` for the general Codex allowance and any named model-specific limits.

Launchd may invoke the script every minute, but the network is queried only
when the cache is older than two minutes and a Codex session JSONL file has
changed, or whenever the cache reaches 30 minutes. On a transient failure, a
cached result remains visible for up to an hour. Expired idle windows are rolled
forward and displayed full until the next live query.

`--background-mode` prevents Terminal Widget from stealing focus while still
refreshing the placed widget. Notification Center is preferable to the Desktop,
where macOS may desaturate widget colours.
