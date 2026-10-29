#!/bin/bash
# Apple's October 2026 workaround for command-line TLS trust:
# https://support.apple.com/en-us/149555
# Removes both affected trust paths, including the Sectigo cross-sign.
set -euo pipefail

bundle=/etc/ssl/cert.pem
dry_run=false
case "${1:-}" in
    --dry-run) dry_run=true ;;
    '') ;;
    *) echo "Usage: $0 [--dry-run]" >&2; exit 2 ;;
esac
if (( $# > 1 )); then
    echo "Usage: $0 [--dry-run]" >&2
    exit 2
fi

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
cp "$bundle" "$tmp/original"

subjects() {
    openssl crl2pkcs7 -nocrl -certfile "$1" |
        openssl pkcs7 -print_certs -noout
}
targets='CN=emSign ECC Root CA - G3|CN=AAA Certificate Services'
subjects "$tmp/original" > "$tmp/before"
if ! grep -Eq "$targets" "$tmp/before"; then
    echo "Already fixed: neither root is present in $bundle."
    exit 0
fi

# Match the exact section headings used in Apple's bundle. Preserve all other
# sections verbatim. Validation below rejects unfamiliar bundle layouts.
awk \
    -v emsign='=== /C=IN/OU=emSign PKI/O=eMudhra Technologies Limited/CN=emSign ECC Root CA - G3' \
    -v aaa='=== /C=GB/ST=Greater Manchester/L=Salford/O=Comodo CA Limited/CN=AAA Certificate Services' \
    '/^(===|###) / {skip=0} $0==emsign || $0==aaa {skip=1} !skip' \
    "$tmp/original" > "$tmp/fixed"
test -s "$tmp/fixed"
subjects "$tmp/fixed" > "$tmp/after"
if grep -Eq "$targets" "$tmp/after"; then
    echo "Could not remove both roots; bundle unchanged." >&2
    exit 1
fi
grep -Ev "$targets" "$tmp/before" | sed '/^$/d' > "$tmp/expected"
sed '/^$/d' "$tmp/after" > "$tmp/actual"
if ! cmp -s "$tmp/expected" "$tmp/actual"; then
    echo "Unrelated certificates changed; bundle unchanged." >&2
    exit 1
fi

echo "Removes emSign ECC Root CA - G3 and AAA Certificate Services."
echo "Some legitimate sites using these roots may stop verifying."
if "$dry_run"; then
    echo "Dry run passed; no files changed."
    exit 0
fi

sudo -v
if ! cmp -s "$bundle" "$tmp/original"; then
    echo "Bundle changed during preparation; rerun the script." >&2
    exit 1
fi
# A unique backup on every actual change also handles macOS restoring the roots.
backup=$(sudo mktemp "${bundle}.pre-emudhra.XXXXXXXX")
sudo cp -p "$bundle" "$backup"
echo "Backup: $backup"
sudo install -m 0644 -o root -g wheel "$tmp/fixed" "$bundle"
if ! cmp -s "$tmp/fixed" "$bundle"; then
    sudo cp -p "$backup" "$bundle"
    echo "Verification failed; restored backup." >&2
    exit 1
fi
echo "Fixed $bundle. Rerun after macOS updates until Apple's fix ships."
echo "Restore with: sudo cp -p '$backup' '$bundle'"
