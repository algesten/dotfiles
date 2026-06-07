#!/bin/bash

dev="$HOME/dev"
dotfiles="$dev/dotfiles"

if [[ -d "$dotfiles" ]]; then
  echo "Symlinking dotfiles from $dotfiles"
else
  echo "$dotfiles does not exist"
  exit 1
fi

link() {
  from="$1"
  to="$2"
  echo "Linking '$from' to '$to'"
  rm -f "$to"
  ln -s "$from" "$to"
}

for location in $(find home -name '*' -type f); do
  file="${location##*/}"
  file="${file%.sh}"
  link "$dotfiles/$location" "$HOME/.${file}"
done

# Link envkeys if it exists (location may vary by machine)
if [[ -f "$HOME/Docs/Settings/envkeys" ]]; then
  link "$HOME/Docs/Settings/envkeys" "$HOME/.envkeys"
fi

mkdir -p $HOME/.config/nvim/lua


echo "Overwriting config/zed to $HOME/.config/zed"
rm -rf $HOME/.config/_zed
mv $HOME/.config/zed $HOME/.config/_zed >/dev/null 2>&1
cp -R config/zed $HOME/.config/

# COSMIC config — symlink individual files into ~/.config/cosmic.
# (cosmic-config does in-place writes, so it follows these symlinks and
#  writes through to the repo; safe to symlink rather than copy.)
# Linux/COSMIC only — skip cleanly on macOS and non-COSMIC machines.
if command -v cosmic-comp >/dev/null 2>&1 || [[ -d "$HOME/.config/cosmic" ]]; then
  cosmic_files="
com.system76.CosmicComp/v1/xkb_config
com.system76.CosmicComp/v1/input_default
com.system76.CosmicComp/v1/input_touchpad
com.system76.CosmicSettings.Shortcuts/v1/custom
com.system76.CosmicSettings.Shortcuts/v1/system_actions
"
  for rel in $cosmic_files; do
    dst="$HOME/.config/cosmic/$rel"
    mkdir -p "$(dirname "$dst")"
    link "$dotfiles/config/cosmic/$rel" "$dst"
  done
else
  echo "Skipping COSMIC config (cosmic not detected)"
fi
