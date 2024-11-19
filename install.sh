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

link "$HOME/Docs/Settings/envkeys" "$HOME/.envkeys"

mkdir -p $HOME/.config/nvim/lua

for location in $(find config/nvim -type f); do
  link $dotfiles/$location $HOME/.${location}
done


echo "Overwriting config/zed to $HOME/.config/zed"
rm -rf $HOME/.config/_zed
mv $HOME/.config/zed $HOME/.config/_zed >/dev/null 2>&1
cp -R config/zed $HOME/.config/
