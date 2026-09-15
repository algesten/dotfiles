# Dotfiles

Originally stolen from paulmillr.

Manage Claude and Codex settings with `./agents.sh`; no arguments or environment
variables are needed. It automatically finds Python 3.11+ on PATH or in the
standard Homebrew locations. The script works from any directory.
`./install.sh` manages the other dotfiles separately.

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
`codex.d/90-local.toml`. Rerun `./agents.sh` after changing shared
files or fragments; this is an installer feature, not a live include mechanism.

Like the other dotfiles, the active files live in this repository and are
symlinked into place:

- `~/.claude/settings.json` → `agents/claude-config.json`
- `~/.codex/config.toml` → `agents/codex-config.toml`

These merged files and their last-installed snapshots in `agents/` are
gitignored. On first installation, existing files
are backed up beside the originals with a `.pre-dotfiles` suffix, and values
that differ from shared defaults become `00-imported` fragments. Codex's
`[projects]` entries are excluded: only global settings are imported, and the
original project trust entries remain in the backup. Review these
fragments: imported values override future shared defaults until removed.
Machine-specific paths and runtime state stay out of git unless you explicitly
choose to track their fragments.

Edit the shared files or local fragments, rather than the generated files.
Running `./update-agents.sh` overwrites changes to the live settings with the
shared files and local fragments, and restores any symlinks replaced by apps.
To keep a setting across updates, put it in a shared file or local fragment.

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
