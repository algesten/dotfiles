# widget-github-ci-budget

A colourful native view of the dollars remaining in a monthly GitHub Actions
budget, for [Terminal Widget](https://terminalwidget.app/).

The widget uses Terminal Widget's native scalable text, caption, and
`desktopcomputer` SF Symbol modes—there is no ASCII or box-drawing art. The
large main value is the estimated number of remaining macOS runner minutes,
with an approximate number of `podocle` runs and the reset date in the native
caption.

The balance is mint above 50%, amber below 50%, and coral below 20%. The widget
uses the semantic Terminal Widget target `github-ci-budget`, rather than a
positional name such as `widget3`.

For the configured `algesten` account, available headroom combines the `$18.00`
value of GitHub Pro's 3,000 included minutes with the `$20.00` repository-level
Actions budget for `podocle`. The widget subtracts private-repository
`discountAmount` from the included allowance and `podocle`'s `netAmount` from
its paid budget. Public repository activity appears in billing reports but does
not draw down the included allowance, so repository visibility is checked
before adding usage.

## Setup

Requires `gh`, `jq`, `terminal-widget`, and access to GitHub's enhanced billing
platform. Authenticate `gh` with billing read access. A fine-grained token needs
**Plan: read** for a personal account, or **Administration: read** for an
organization.

```sh
gh auth login -h github.com
ln -s ~/dev/dotfiles/widget-github-ci-budget/github-ci-budget-widget \
  ~/bin/github-ci-budget-widget
github-ci-budget-widget --demo
github-ci-budget-widget --budget 10 --force
```

Add a medium Terminal Widget and set its target to `github-ci-budget`.

For an organization, add `--org ORGANIZATION` or set `GCB_ORG`. The dollar
budget is always explicit: pass `--budget USD` or set `GCB_BUDGET`.

To run through launchd, add the budget (and optionally the organization) inside
the plist's `EnvironmentVariables` dictionary:

```xml
<key>GCB_BUDGET</key>
<string>10</string>
<key>GCB_ORG</key>
<string>my-organization</string>
```

Then install it:

```sh
cp ~/dev/dotfiles/widget-github-ci-budget/io.lookback.github-ci-budget-widget.plist \
  ~/Library/LaunchAgents/
launchctl bootstrap gui/$(id -u) \
  ~/Library/LaunchAgents/io.lookback.github-ci-budget-widget.plist
```

It refreshes every five minutes and caches successful results for 15 minutes.
GitHub reports `netAmount`, so included minutes and other discounts are already
deducted before the widget calculates `budget - spend`.

## Configuration

Environment variables use the `GCB_` prefix: `GCB_BUDGET`, `GCB_ORG`,
`GCB_INCLUDED`, `GCB_REPOSITORY`, `GCB_ACCOUNT`, `GCB_TARGET`, `GCB_FONT`, `GCB_FONT_SIZE`, `GCB_BACKGROUND`,
`GCB_FOREGROUND`, `GCB_CACHE`, `GCB_MAX_AGE`, `GCB_API_VERSION`, `GCB_MAC_RATE`,
and `GCB_MAC_MINS_PER_RUN`. The defaults are `$0.062` per macOS minute and 16
minutes per representative full `podocle` run.

Use `--dump --budget USD` to inspect GitHub's response and the computed spend.
