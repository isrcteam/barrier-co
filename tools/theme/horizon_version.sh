#!/usr/bin/env bash
set -uo pipefail
ROOT="${1:-.}"
UPSTREAM_URL="https://github.com/Shopify/horizon.git"
cd "$ROOT" || exit 1

read_version() {
  python3 -c "
import json,sys
try:
    d=json.load(sys.stdin)
    print(next((x.get('theme_name','?')+' '+x.get('theme_version','?') for x in d if x.get('name')=='theme_info'),'unknown'))
except Exception:
    print('unknown')
"
}

if [ -f config/settings_schema.json ]; then
  LOCAL=$(read_version < config/settings_schema.json)
else
  LOCAL="no config/settings_schema.json"
fi

if git rev-parse --git-dir >/dev/null 2>&1; then
  git remote get-url upstream >/dev/null 2>&1 || git remote add upstream "$UPSTREAM_URL"
  git fetch --quiet upstream main || { echo "Could not fetch upstream"; exit 1; }
  REF="upstream/main"
  GIT="git"
else
  TMP=$(mktemp -d)
  git clone --quiet --filter=blob:none --no-checkout "$UPSTREAM_URL" "$TMP" || { echo "Could not clone Horizon"; exit 1; }
  REF="origin/main"
  GIT="git -C $TMP"
fi

LATEST=$($GIT show "$REF:config/settings_schema.json" | read_version)
COMMIT=$($GIT log -1 --format='%h %cs' "$REF")
BUMP=$($GIT log -1 --format='%h %cs' -G'"theme_version"' "$REF" -- config/settings_schema.json)

echo "This theme:        $LOCAL"
echo "Latest Horizon:    $LATEST"
echo "Upstream main:     $COMMIT"
echo "Version bump at:   $BUMP"

if [ "$LOCAL" = "$LATEST" ]; then
  echo "Status: up to date."
else
  echo "Status: behind or different. Release notes for the latest version:"
  echo
  $GIT show "$REF:release-notes.md" | sed -n '1,40p'
  echo
  echo "Don't merge yet. Write a reasoning entry and get 'Approved: horizon <version>' first."
fi
