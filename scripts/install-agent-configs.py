#!/usr/bin/env python3
"""Merge shared agent settings with private fragments and install symlinks."""
import datetime
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

try:
    import tomllib
except ImportError:
    sys.exit("Agent config installation requires Python 3.11+. Run ./agents.sh to detect it automatically.")

REPO = Path(__file__).resolve().parent.parent


def read(path):
    text = path.read_text()
    data = json.loads(text) if path.suffix == ".json" else tomllib.loads(text)
    if not isinstance(data, dict):
        raise ValueError(f"Expected a configuration object: {path}")
    return data


def merge(base, override):
    result = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = merge(result[key], value)
        else:
            result[key] = value
    return result


def difference(current, base):
    """Keep existing values that differ from the shared defaults on migration."""
    result = {}
    for key, value in current.items():
        if key not in base or value != base[key]:
            if isinstance(value, dict) and isinstance(base.get(key), dict):
                value = difference(value, base[key])
            result[key] = value
    return result


def toml_value(value):
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, (int, float)):
        return repr(value)
    if isinstance(value, (datetime.datetime, datetime.date, datetime.time)):
        return value.isoformat()
    if isinstance(value, list):
        return "[" + ", ".join(toml_value(v) for v in value) + "]"
    if isinstance(value, dict):
        return "{ " + ", ".join(f"{toml_value(k)} = {toml_value(v)}" for k, v in value.items()) + " }"
    raise ValueError(f"Unsupported TOML value: {type(value).__name__}")


def serialize(data, suffix):
    if suffix == ".json":
        return json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    lines = []

    def table(values, path):
        if path:
            lines.append("[" + ".".join(toml_value(k) for k in path) + "]")
        for key, value in values.items():
            if not isinstance(value, dict):
                lines.append(f"{toml_value(key)} = {toml_value(value)}")
        for key, value in values.items():
            if isinstance(value, dict):
                lines.append("")
                table(value, path + [key])

    table(data, [])
    text = "\n".join(lines) + "\n"
    if tomllib.loads(text) != data:
        raise ValueError("TOML serialization failed round-trip validation")
    return text


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(fd, "w") as stream:
            stream.write(text)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def install(home, repo=REPO):
    root = repo / "agents"
    plans = []
    for name, source, destination in (
        ("claude", "claude-settings.json", ".claude/settings.json"),
        ("codex", "codex-config.toml", ".codex/config.toml"),
    ):
        target = home / destination
        suffix = target.suffix
        fragments = repo / (name + ".d")
        generated = root / (name + "-config" + suffix)
        snapshot = root / (name + ".last-installed" + suffix)
        base = read(repo / source)
        migration = None
        # After migration, shared defaults and fragments replace any live edits.
        if not snapshot.exists() and target.exists():
            backup = target.with_name(target.name + ".pre-dotfiles")
            if backup.exists() or backup.is_symlink():
                raise ValueError(f"Backup already exists; preserve or move it first: {backup}")
            migration = difference(read(target), base)
            if name == "codex":
                # Import global preferences only, not per-directory trust decisions.
                migration.pop("projects", None)
            if (fragments / ("00-imported" + suffix)).exists():
                raise ValueError(f"Refusing to overwrite existing imported settings in {fragments}")
        merged = merge(base, migration or {})
        for fragment in sorted(fragments.glob("*" + suffix)):
            merged = merge(merged, read(fragment))
        plans.append((target, fragments, generated, snapshot, migration, serialize(merged, suffix)))

    # Validate both configurations before changing either destination.
    for target, fragments, generated, snapshot, migration, text in plans:
        fragments.mkdir(parents=True, exist_ok=True)
        if not snapshot.exists() and target.exists():
            backup = target.with_name(target.name + ".pre-dotfiles")
            if backup.exists() or backup.is_symlink():
                raise ValueError(f"Backup already exists; preserve or move it first: {backup}")
            shutil.copy2(target, backup)
            backup.chmod(0o600)
        if migration is not None:
            write(fragments / ("00-imported" + target.suffix), serialize(migration, target.suffix))
        write(generated, text)
        write(snapshot, text)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.is_symlink() or target.exists():
            target.unlink()
        target.symlink_to(generated)
        print(f"Linked {target} -> {generated}; local fragments: {fragments}")


if __name__ == "__main__":
    try:
        install(Path.home())
    except (ValueError, OSError) as error:
        sys.exit(str(error))
