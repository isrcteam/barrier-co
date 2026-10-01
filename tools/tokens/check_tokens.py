#!/usr/bin/env python3
"""Fail if any token value is defined twice, or a colour is typed outside the token files.

Usage: check_tokens.py [docs/tokens.json] [--theme .]
Errors (exit 1):
  - the same hex under two palette names
  - a scheme or fixed colour that isn't a palette reference
  - a hex, rgb(), hsl() or named-colour value in src/scss, or in sections, blocks, snippets and layout Liquid
  - a font-family typed in src/scss instead of $font-family-<name> (fonts are tokens too; Shopify-library fonts reach SCSS as var(--font-<name>))
Warnings:
  - the same number under two names in space, layout, radius, border or icon (use a reference instead)
  - the same type role spec defined twice
Hex values are allowed in exactly two places: docs/tokens.json, and the config/settings_*.json values generated from it.
"""
import argparse, collections, glob, json, os, re, sys

HEX = re.compile(r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})\b")
FUNC = re.compile(r"\b(?:rgba?|hsla?|oklch|lab|lch)\(")
NAMED = re.compile(r":\s*(?:white|black|red|blue|green|grey|gray|orange|yellow|purple|pink)\s*[;}!]", re.I)
REF = re.compile(r"^\{[^}]+\}$")
FONT_DECL = re.compile(r"font-family\s*:\s*([^;}]+)")
FONT_OK = re.compile(r"^\s*(\$font-family-[a-z0-9-]+|var\(--font-[a-z0-9-]+\)|inherit|initial|unset)\s*(!important)?\s*$")

def norm(v):
    v = v.lower()
    return "#" + "".join(c * 2 for c in v[1:]) if len(v) == 4 else v

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tokens", nargs="?", default="docs/tokens.json")
    ap.add_argument("--theme", default=".")
    a = ap.parse_args()
    t = json.load(open(a.tokens, encoding="utf-8"))
    errors, warnings = [], []

    seen = {}
    for name, v in (t.get("color", {}).get("palette") or {}).items():
        n = norm(v)
        if n in seen:
            errors.append(f"color.palette.{name} ({v}) repeats color.palette.{seen[n]}")
        seen[n] = name
    for sid, s in (t.get("color", {}).get("schemes") or {}).items():
        for rid, v in s.items():
            if rid != "name" and not (isinstance(v, str) and REF.match(v)):
                errors.append(f"color.schemes.{sid}.{rid} is a raw value ({v}); reference the palette")
    for fid, f in (t.get("color", {}).get("fixed") or {}).items():
        if not REF.match(str(f.get("value", ""))):
            errors.append(f"color.fixed.{fid} is a raw value; reference the palette")

    for family in (("space", "layout"), ("radius",), ("border",), ("icon",)):
        values = collections.defaultdict(list)
        for group in family:
            for name, v in (t.get(group) or {}).items():
                if isinstance(v, (int, float)):
                    values[v].append(f"{group}.{name}")
        for v, names in values.items():
            if len(names) > 1:
                warnings.append(f"{v} is defined as {', '.join(names)}. Keep one and reference it, e.g. \"{{{names[0]}}}\"")
    specs = collections.defaultdict(list)
    for role, spec in (t.get("type") or {}).items():
        specs[json.dumps(spec, sort_keys=True)].append(role)
    for roles in specs.values():
        if len(roles) > 1:
            warnings.append(f"type roles {', '.join(roles)} are identical. Merge them or make the difference explicit")

    theme = a.theme
    files = glob.glob(os.path.join(theme, "src", "scss", "**", "*.scss"), recursive=True)
    for folder in ("sections", "blocks", "snippets", "layout"):
        files += glob.glob(os.path.join(theme, folder, "*.liquid"))
    for path in sorted(files):
        rel = os.path.relpath(path, theme)
        text = open(path, encoding="utf-8", errors="ignore").read()
        if path.endswith(".liquid"):
            m = re.search(r"{%-?\s*schema\s*-?%}.*?{%-?\s*endschema\s*-?%}", text, re.S)
            if m:
                text = text[: m.start()] + text[m.end():]
        for i, line in enumerate(text.splitlines(), 1):
            if HEX.search(line) or FUNC.search(line) or NAMED.search(line):
                if re.search(r"url\(|&#|\{\{", line) and not FUNC.search(line):
                    continue
                errors.append(f"{rel}:{i} colour value outside tokens: {line.strip()[:100]}")
            if path.endswith(".scss") and "lib/_variables.scss" not in rel.replace(os.sep, "/"):
                m = FONT_DECL.search(line)
                if m and not FONT_OK.match(m.group(1)):
                    errors.append(f"{rel}:{i} font family outside tokens: {line.strip()[:100]}. Use $font-family-<name> from docs/tokens.json")

    for w in warnings:
        print(f"WARN  {w}")
    for e in errors:
        print(f"ERROR {e}")
    print(f"\n{len(errors)} error(s), {len(warnings)} warning(s)")
    sys.exit(1 if errors else 0)

if __name__ == "__main__":
    main()
