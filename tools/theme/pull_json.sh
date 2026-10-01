#!/usr/bin/env bash
# Pulls the theme-owned JSON (templates, section groups, settings_data.json) from a theme into this repo.
# Core rule 18: after the first push those files belong to the theme editor; this brings them back into git.
# Usage: bash tools/theme/pull_json.sh [--theme <id or name>] [--store <shop>] [--live]
#   Default theme: the unpublished theme named after the current git branch (what deploy.yml pushes to).
#   Store: --store, or SHOPIFY_FLAG_STORE, or the development environment in shopify.theme.toml.
set -euo pipefail
THEME=""; STORE="${SHOPIFY_FLAG_STORE:-}"; LIVE=0
while [ $# -gt 0 ]; do
  case "$1" in
    --theme) THEME="$2"; shift 2 ;;
    --store) STORE="$2"; shift 2 ;;
    --live) LIVE=1; shift ;;
    -h|--help) sed -n '2,6p' "$0"; exit 0 ;;
    *) echo "Unknown option $1" >&2; exit 1 ;;
  esac
done
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

# The same list deploy.yml ignores after the first push. Change both together.
ONLY=(--only "templates/*.json" --only "templates/customers/*.json" --only "templates/metaobject/*.json" --only "sections/*.json" --only "config/settings_data.json")
WHERE=()
if [ -n "$STORE" ]; then WHERE=(--store "$STORE"); elif [ -f shopify.theme.toml ]; then WHERE=(-e development); fi

if [ "$LIVE" -eq 1 ]; then
  shopify theme pull --live ${WHERE[@]+"${WHERE[@]}"} "${ONLY[@]}" --no-color
  echo "Pulled the live theme's JSON. Review the diff and commit it as: chore: pull theme JSON"
  exit 0
fi

[ -n "$THEME" ] || THEME="$(git symbolic-ref --short -q HEAD || git rev-parse --abbrev-ref HEAD)"
if [[ "$THEME" =~ ^[0-9]+$ ]]; then
  ID="$THEME"
else
  ID=$(shopify theme list --name "$THEME" --json ${WHERE[@]+"${WHERE[@]}"} | THEME_NAME="$THEME" node -e "let d='';process.stdin.on('data',c=>d+=c).on('end',()=>{const m=JSON.parse(d||'[]').find(t=>t.name===process.env.THEME_NAME&&t.role!=='live');process.stdout.write(m?String(m.id):'')})")
fi
if [ -z "$ID" ]; then
  echo "No theme named '$THEME' on the store. Push the branch first (deploy.yml creates it), or pass --theme <id>." >&2
  exit 1
fi
shopify theme pull --theme "$ID" ${WHERE[@]+"${WHERE[@]}"} "${ONLY[@]}" --no-color
echo "Pulled the theme's JSON from theme $ID ($THEME). Review the diff and commit it as: chore: pull theme JSON"
