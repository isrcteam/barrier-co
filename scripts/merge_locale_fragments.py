#!/usr/bin/env python3
"""Merge docs/locale-fragments/*.json into the Horizon locale files without reformatting them.

<name>.json goes into locales/en.default.schema.json, <name>.storefront.json into locales/en.default.json.
Only missing keys are added, as new lines directly under their parent object, so Horizon's comments
and layout survive and upstream merges stay small. A key that exists with different text is reported,
never overwritten.
  python3 scripts/merge_locale_fragments.py           # dry run
  python3 scripts/merge_locale_fragments.py --apply
"""
import glob, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRAGMENTS = os.path.join(ROOT, "docs", "locale-fragments")
TARGETS = {False: os.path.join(ROOT, "locales", "en.default.schema.json"),
           True: os.path.join(ROOT, "locales", "en.default.json")}


def strip_jsonc(raw):
    out, i, n, in_str = [], 0, len(raw), False
    while i < n:
        c = raw[i]
        if in_str:
            out.append(c)
            if c == "\\" and i + 1 < n:
                out.append(raw[i + 1]); i += 2; continue
            if c == '"':
                in_str = False
            i += 1; continue
        if c == '"':
            in_str = True; out.append(c); i += 1
        elif raw.startswith("//", i):
            j = raw.find("\n", i); i = n if j < 0 else j
        elif raw.startswith("/*", i):
            j = raw.find("*/", i); i = n if j < 0 else j + 2
        else:
            out.append(c); i += 1
    return re.sub(r",(\s*[}\]])", r"\1", "".join(out))


def find_object_line(lines, path):
    """Line index of the opening brace for the object at path, matched by indentation."""
    start, end = 0, len(lines)
    for depth, key in enumerate(path, start=1):
        pat = re.compile(r'^' + " " * (2 * depth) + re.escape(json.dumps(key)) + r':\s*\{\s*$')
        for i in range(start, end):
            if pat.match(lines[i]):
                start = i
                close = re.compile(r'^' + " " * (2 * depth) + r'\}')
                end = next(j for j in range(i + 1, len(lines)) if close.match(lines[j]))
                break
        else:
            return None
    return start


def render(key, value, depth):
    pad = " " * (2 * depth)
    if isinstance(value, dict):
        inner = [render(k, v, depth + 1) for k, v in value.items()]
        body = ",\n".join(inner)
        return f'{pad}{json.dumps(key)}: {{\n{body}\n{pad}}}'
    return f'{pad}{json.dumps(key)}: {json.dumps(value, ensure_ascii=False)}'


def merge(target, fragment, apply):
    raw = open(target, encoding="utf-8").read()
    data = json.loads(strip_jsonc(raw))
    lines = raw.split("\n")
    added, conflicts = [], []

    def walk(frag, existing, path):
        for key, value in frag.items():
            here = path + [key]
            if key in existing:
                if isinstance(value, dict) and isinstance(existing[key], dict):
                    walk(value, existing[key], here)
                elif existing[key] != value:
                    conflicts.append((".".join(here), existing[key], value))
                continue
            parent = find_object_line(lines, path) if path else None
            if path and parent is None:
                conflicts.append((".".join(here), "<parent not found>", value)); continue
            insert_at = parent + 1 if path else 1 + next(i for i, l in enumerate(lines) if l.strip() == "{")
            lines.insert(insert_at, render(key, value, len(path) + 1) + ",")
            existing[key] = value
            added.append(".".join(here))

    walk(fragment, data, [])
    if apply and added:
        open(target, "w", encoding="utf-8").write("\n".join(lines))
        json.loads(strip_jsonc("\n".join(lines)))
    return added, conflicts


def main():
    apply = "--apply" in sys.argv
    files = sorted(glob.glob(os.path.join(FRAGMENTS, "*.json")))
    total = 0
    for path in files:
        storefront = path.endswith(".storefront.json")
        added, conflicts = merge(TARGETS[storefront], json.load(open(path, encoding="utf-8")), apply)
        total += len(added)
        name = os.path.basename(path)
        print(f"{name}: {len(added)} added" + (f", {len(conflicts)} conflicts" if conflicts else ""))
        for key, old, new in conflicts:
            print(f"  conflict {key}: existing {old!r}, fragment {new!r}")
    print(("Applied" if apply else "Dry run") + f": {total} keys")


if __name__ == "__main__":
    main()
