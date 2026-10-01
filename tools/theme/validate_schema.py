#!/usr/bin/env python3
"""Validate {% schema %} blocks in sections/ and blocks/ against iSourceit schema rules.

Usage: validate_schema.py <theme-root>
Errors (exit 1): invalid JSON, literal strings where t: keys belong, t: keys missing from
locales/en.default.schema.json, range defaults off the step, sections with no presets that no template or
section group places.
Warnings: *_mobile settings without a "same at mobile" checkbox and visible_if.
"""
import glob, json, os, re, sys

TEXT_KEYS = ("name", "label", "info", "content", "placeholder")


def strip_jsonc(raw):
    """Remove // and /* */ comments and trailing commas outside strings, so Shopify's theme JSON parses."""
    out, i, n, in_str = [], 0, len(raw), False
    while i < n:
        c = raw[i]
        if in_str:
            out.append(c)
            if c == "\\" and i + 1 < n:
                out.append(raw[i + 1])
                i += 2
                continue
            if c == '"':
                in_str = False
            i += 1
            continue
        if c == '"':
            in_str = True
            out.append(c)
            i += 1
        elif raw.startswith("//", i):
            j = raw.find("\n", i)
            i = n if j < 0 else j
        elif raw.startswith("/*", i):
            j = raw.find("*/", i + 2)
            i = n if j < 0 else j + 2
        elif c == ",":
            j = i + 1
            while j < n and raw[j] in " \t\r\n":
                j += 1
            if j < n and raw[j] in "}]":
                i += 1
            elif raw.startswith("//", j) or raw.startswith("/*", j):
                # a comment follows; decide after it
                k = j
                while True:
                    while k < n and raw[k] in " \t\r\n":
                        k += 1
                    if raw.startswith("//", k):
                        e = raw.find("\n", k)
                        k = n if e < 0 else e
                    elif raw.startswith("/*", k):
                        e = raw.find("*/", k + 2)
                        k = n if e < 0 else e + 2
                    else:
                        break
                if k < n and raw[k] in "}]":
                    i += 1
                else:
                    out.append(c)
                    i += 1
            else:
                out.append(c)
                i += 1
        else:
            out.append(c)
            i += 1
    return "".join(out)

def load_locale(root):
    path = os.path.join(root, "locales", "en.default.schema.json")
    if not os.path.exists(path):
        return None
    return json.loads(strip_jsonc(open(path, encoding="utf-8").read()))

def has_key(locale, key):
    node = locale
    for part in key.split("."):
        if not isinstance(node, dict) or part not in node:
            return False
        node = node[part]
    return True

def walk_strings(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            here = f"{path}.{k}" if path else k
            if k in TEXT_KEYS and isinstance(v, str):
                yield here, v
            elif k == "options" and isinstance(v, list):
                for i, opt in enumerate(v):
                    if isinstance(opt, dict) and isinstance(opt.get("label"), str):
                        yield f"{here}[{i}].label", opt["label"]
            else:
                yield from walk_strings(v, here)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk_strings(v, f"{path}[{i}]")

def all_settings(schema):
    yield from schema.get("settings", [])
    for block in schema.get("blocks", []):
        yield from block.get("settings", []) if isinstance(block, dict) else []

def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    locale = load_locale(root)
    errors = warnings = 0
    files = glob.glob(os.path.join(root, "sections", "*.liquid")) + glob.glob(os.path.join(root, "blocks", "*.liquid"))
    placed = set()
    for j in glob.glob(os.path.join(root, "templates", "**", "*.json"), recursive=True) + glob.glob(os.path.join(root, "sections", "*.json")):
        try:
            data = json.loads(strip_jsonc(open(j, encoding="utf-8").read()))
        except ValueError:
            continue
        placed |= {v.get("type") for v in (data.get("sections") or {}).values() if isinstance(v, dict)}
    for path in sorted(files):
        rel = os.path.relpath(path, root)
        text = open(path, encoding="utf-8", errors="ignore").read()
        m = re.search(r"{%-?\s*schema\s*-?%}(.*?){%-?\s*endschema\s*-?%}", text, re.S)
        if not m:
            continue
        try:
            schema = json.loads(strip_jsonc(m.group(1)))
        except json.JSONDecodeError as e:
            print(f"ERROR {rel}: invalid schema JSON ({e})")
            errors += 1
            continue
        for where, value in walk_strings(schema):
            if not value.startswith("t:"):
                print(f"ERROR {rel}: literal string at {where}: {value[:60]!r}")
                errors += 1
            elif locale is not None and not has_key(locale, value[2:]):
                print(f"ERROR {rel}: missing locale key {value}")
                errors += 1
        settings = list(all_settings(schema))
        ids = {s.get("id") for s in settings if isinstance(s, dict)}
        for s in settings:
            if not isinstance(s, dict):
                continue
            if s.get("type") == "range" and "default" in s:
                step = s.get("step", 1)
                lo = s.get("min", 0)
                if step and round((s["default"] - lo) / step, 6) % 1:
                    print(f"ERROR {rel}: range '{s.get('id')}' default {s['default']} not on step {step}")
                    errors += 1
            sid = s.get("id") or ""
            if sid.endswith("_mobile"):
                has_toggle = any(i and "same" in i and "mobile" in i for i in ids)
                if not has_toggle or "visible_if" not in s:
                    print(f"WARN  {rel}: '{sid}' has no 'Same at mobile' toggle with visible_if")
                    warnings += 1
        name = os.path.basename(path)[:-7]
        if rel.startswith("sections") and not schema.get("presets") and name not in placed:
            print(f"ERROR {rel}: no presets and not placed in any template or section group, so it can't be used")
            errors += 1
    if locale is None:
        print("NOTE locales/en.default.schema.json not found, locale keys not checked")
    print(f"\n{len(files)} files checked, {errors} error(s), {warnings} warning(s)")
    sys.exit(1 if errors else 0)

if __name__ == "__main__":
    main()
