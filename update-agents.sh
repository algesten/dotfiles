#!/bin/bash

dotfiles="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)" || exit 1

# macOS may put its older system Python ahead of Homebrew on PATH.
for python in python3 /opt/homebrew/bin/python3 /usr/local/bin/python3 python3.{20..11}; do
  if "$python" -c 'import tomllib' >/dev/null 2>&1; then
    exec "$python" "$dotfiles/scripts/install-agent-configs.py"
  fi
done

echo "Agent config installation requires Python 3.11+. Install it, then rerun ./agents.sh." >&2
exit 1
