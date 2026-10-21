# Dotfiles

Originally stolen from paulmillr.

Manage Claude and Codex settings with `./update-agents.sh`; no arguments or environment
variables are needed. It automatically finds Python 3.11+ on PATH or in the
standard Homebrew locations. The script works from any directory.
`./install.sh` manages the other dotfiles separately.

To install into another directory, pass it as the optional argument:

```sh
./update-agents.sh ~/wurk
CODEX_HOME=~/wurk/.codex codex
```

This creates `~/wurk/.codex` and `~/wurk/.claude`, with the same configuration,
instructions, and skill symlinks as the default installation. Generated configs
and local fragments remain shared in this repository; credentials and session
state belong to the selected agent home.

Shared defaults live in `claude-settings.json` and `codex-config.toml`. Local
additions live in this repository:

- `claude.d/*.json`
- `codex.d/*.toml`

Fragments are gitignored by default. To check in a particular fragment, use
`git add -f claude.d/example.json` or `git add -f codex.d/example.toml`.
Once tracked, subsequent edits appear in git normally.

The installer recursively merges shared defaults, then fragments in filename
order. Later values win; arrays are replaced as a whole (including permission
lists). For example, put `{"effortLevel": "high"}` in
`claude.d/90-local.json`, or `model_reasoning_effort = "high"` in
`codex.d/90-local.toml`. Rerun `./update-agents.sh` after changing shared
files or fragments; this is an installer feature, not a live include mechanism.

Like the other dotfiles, the active files live in this repository and are
symlinked into place:

- `~/.claude/settings.json` → `agents/claude-config.json`
- `~/.codex/config.toml` → `agents/codex-config.toml`
- `~/.codex/AGENTS.md` → `AGENTS.md`

`AGENTS.md` provides global Codex instructions for naming sessions when reviewing
pull requests and keeping session names in sync after PR title or description
changes. The updater preserves an existing global instructions file or symlink
as `~/.codex/AGENTS.md.pre-dotfiles` before installing the link. Repeated updates
keep the managed link; a conflicting existing backup stops installation without
overwriting either file. Start a new Codex session to load the instructions.

`./update-agents.sh` also links each directory in `skills/` containing a
`SKILL.md` into both `~/.claude/skills/` and `~/.codex/skills/`. Existing
entries with the same name are kept and reported, rather than overwritten.

These merged files and their last-installed snapshots in `agents/` are
gitignored. On first installation, existing files
are backed up beside the originals with a `.pre-dotfiles` suffix, and values
that differ from shared defaults become `00-imported` fragments. Codex's
`[projects]` entries are excluded: only global settings are imported, and the
original project trust entries remain in the backup. Review these
fragments: imported values override future shared defaults until removed.
Machine-specific paths and runtime state stay out of git unless you explicitly
choose to track their fragments.

Codex MCP servers are preserved from the live `~/.codex/config.toml` on every
update, so you can keep using `codex mcp add` and `codex mcp remove`. The live
`[mcp_servers]` section takes precedence over shared defaults and fragments,
including imported settings. Removing a server, or the entire section, stays
removed on later updates. Shared and fragment MCP definitions are used when no
live Codex config exists. If the live file is invalid, the updater stops before
changing either configuration so it cannot discard MCP settings it cannot read.

For other settings, edit the shared files or local fragments. Running
`./update-agents.sh` overwrites other changes to the live settings with the
shared files and local fragments, and restores any symlinks replaced by apps.
To keep a non-MCP setting across updates, put it in a shared file or local fragment.

Neither tool documents a general user-level `include`/`conf.d` facility.
[Claude](https://code.claude.com/docs/en/settings) supports project
`.claude/settings.local.json` and CLI `--settings` overlays; a home-level
`~/.claude/settings.local.json` is not a global override.
[Codex](https://learn.chatgpt.com/docs/config-file/config-basic) supports trusted
project `.codex/config.toml`, selected profile files and system defaults at
`/etc/codex/config.toml`. Native precedence still applies: project overrides
outrank user settings, while system defaults sit below them. We use an installer
merge to get machine-wide local additions
for both tools without wrappers or system-wide installation.
