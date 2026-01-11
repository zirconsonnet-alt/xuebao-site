#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 {home|24game}" >&2
  exit 1
fi

site="$1"
root="$(cd "$(dirname "$0")" && pwd)"

case "$site" in
  home)
    src="$root/apps/home"
    dest="/var/www/html"
    ;;
  24game)
    src="$root/apps/24game"
    dest="/var/www/24game"
    ;;
  *)
    echo "Unknown site: $site" >&2
    exit 1
    ;;
esac

if [[ ! -d "$src" ]]; then
  echo "Source not found: $src" >&2
  exit 1
fi

if ! command -v rsync >/dev/null 2>&1; then
  echo "rsync is required for deployment." >&2
  exit 1
fi

rsync -a --delete "$src"/ "$dest"/
echo "Deployed $site to $dest"
