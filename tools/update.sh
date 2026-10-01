#!/usr/bin/env bash
# Refreshes this repo's tools/ from the installed isrc plugin. Keeps stores.json and .env.
# Usage: bash tools/update.sh            update from the installed plugin
#        bash tools/update.sh --check    only report the repo's tools version against the plugin's
#        bash tools/update.sh <plugin folder or isrc-plugin.zip>
set -euo pipefail
CHECK=0; GIVEN=""
for a in "$@"; do
  case "$a" in
    --check) CHECK=1 ;;
    -h|--help) sed -n '2,5p' "$0"; exit 0 ;;
    *) GIVEN="$a" ;;
  esac
done
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
MINE=""; [ -f "$HERE/VERSION" ] && MINE="$(tr -d '[:space:]' < "$HERE/VERSION")"
TMP=""
cleanup() { if [ -n "$TMP" ]; then rm -rf "$TMP"; fi; }
trap cleanup EXIT

plugin_ok() {  # plugin_ok <dir>: prints the dir that holds setup_tools.sh and tools/VERSION
  local d="$1"
  if [ -f "$d/tools/VERSION" ] && [ -f "$d/skills/pull/scripts/setup_tools.sh" ]; then echo "$d"; return 0; fi
  if [ -f "$d/tools/VERSION" ] && [ -f "$d/scripts/setup_tools.sh" ]; then echo "$d"; return 0; fi
  return 1
}

PLUGIN=""
if [ -n "$GIVEN" ]; then
  if [ -f "$GIVEN" ]; then
    TMP="$(mktemp -d)"
    unzip -q "$GIVEN" -d "$TMP"
    for d in "$TMP" "$TMP"/*; do PLUGIN="$(plugin_ok "$d" || true)"; [ -n "$PLUGIN" ] && break; done
  else
    PLUGIN="$(plugin_ok "$GIVEN" || true)"
  fi
  [ -n "$PLUGIN" ] || { echo "$GIVEN doesn't look like the isrc plugin (needs tools/VERSION and skills/pull/scripts/setup_tools.sh)" >&2; exit 1; }
elif [ -n "${CLAUDE_PLUGIN_ROOT:-}" ] && PLUGIN="$(plugin_ok "$CLAUDE_PLUGIN_ROOT" || true)" && [ -n "$PLUGIN" ]; then
  :
else
  best=""; bestv=""
  while IFS= read -r v; do
    d="$(dirname "$(dirname "$v")")"
    plugin_ok "$d" >/dev/null 2>&1 || continue
    grep -q '"name": *"isrc"' "$d/.claude-plugin/plugin.json" 2>/dev/null || continue
    ver="$(tr -d '[:space:]' < "$v")"
    if [ -z "$bestv" ] || [ "$(printf '%s\n%s\n' "$bestv" "$ver" | sort -V | tail -1)" = "$ver" ]; then best="$d"; bestv="$ver"; fi
  done < <(find "$HOME/.claude/plugins" -maxdepth 7 -path '*/tools/VERSION' 2>/dev/null)
  PLUGIN="$best"
fi

if [ -z "$PLUGIN" ]; then
  echo "Can't find the isrc plugin on this machine." >&2
  echo "Install it in Claude Code, or pass its folder or zip: bash tools/update.sh <path>" >&2
  exit 1
fi
THEIRS="$(tr -d '[:space:]' < "$PLUGIN/tools/VERSION")"

if [ "$CHECK" -eq 1 ]; then
  if [ "$MINE" = "$THEIRS" ]; then
    echo "tools $MINE: up to date with the plugin"
    exit 0
  fi
  echo "tools ${MINE:-none} in this repo, plugin has $THEIRS. Run: bash tools/update.sh"
  exit 1
fi

if [ -f "$PLUGIN/skills/pull/scripts/setup_tools.sh" ]; then
  bash "$PLUGIN/skills/pull/scripts/setup_tools.sh" "$ROOT"
else
  bash "$PLUGIN/scripts/setup_tools.sh" "$ROOT"
fi
