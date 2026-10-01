#!/usr/bin/env python3
"""Check theme file and schema names, and catch clashes with Horizon files.

Usage:
  python3 tools/theme/check_names.py [--theme .]                       naming rules on every custom file
  python3 tools/theme/check_names.py --new blocks/hero-banner.liquid   before creating a file: clash with Horizon?
  python3 tools/theme/check_names.py --update-from <old-commit> --update-to upstream/main
                                                                       before merging a Horizon update: new upstream
                                                                       files that clash with files we added
Rules: lowercase kebab-case; named for what the merchant sees or what the file does; no agency or client
names or initials; no versions or -new/-copy/-old/-final; no Figma layer names; schema "name" in sentence
case, as a t: key. Client names to ban go in docs/banned-names.txt, one per line.
"""
import argparse, glob, json, os, re, subprocess, sys

BAD_WORDS = re.compile(r"(^|[-_])(v\d+|copy|old|final|temp|untitled|isrc|isourceit|(frame|group|layer|rectangle|section|block)[-_]?\d+)([-_]|$)")



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

def upstream_files(ref):
    out = subprocess.run(["git", "ls-tree", "-r", "--name-only", ref], capture_output=True, text=True)
    if out.returncode:
        sys.exit(f"git ls-tree {ref} failed. Run bash tools/theme/horizon_version.sh . first so the upstream remote exists.")
    return set(out.stdout.split())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--theme", default=".")
    ap.add_argument("--new")
    ap.add_argument("--update-from")
    ap.add_argument("--update-to", default="upstream/main")
    a = ap.parse_args()
    banned = []
    bf = os.path.join(a.theme, "docs", "banned-names.txt")
    if os.path.exists(bf):
        banned = [l.strip().lower() for l in open(bf) if l.strip()]

    if a.new:
        up = upstream_files(a.update_to)
        if a.new in up:
            sys.exit(f"CLASH {a.new} exists in Horizon ({a.update_to}). Pick another name.")
        print(f"ok  {a.new} is free in Horizon {a.update_to}")
        return
    if a.update_from:
        before, after = upstream_files(a.update_from), upstream_files(a.update_to)
        added = after - before
        ours = {os.path.relpath(p, a.theme) for p in glob.glob(os.path.join(a.theme, "*", "*"))}
        clashes = sorted(added & ours)
        for c in clashes:
            print(f"CLASH {c}: Horizon adds this file in the update and we already have our own. Rename ours before merging.")
        print(f"{len(added)} new upstream files, {len(clashes)} clash(es)")
        sys.exit(1 if clashes else 0)

    errors = []
    for folder in ("sections", "blocks", "snippets", "templates"):
        for p in glob.glob(os.path.join(a.theme, folder, "*")):
            name = os.path.basename(p).split(".")[0]
            full = os.path.basename(p)
            if folder == "templates":
                name = full.rsplit(".", 1)[0].split(".", 1)[-1] if full.count(".") > 1 else ""
            if not name:
                continue
            if not re.fullmatch(r"_?[a-z0-9]+(-[a-z0-9]+)*", name):
                errors.append(f"{folder}/{full}: use lowercase kebab-case")
            if BAD_WORDS.search(name):
                errors.append(f"{folder}/{full}: no versions, copies, layer names or agency names in file names")
            for b in banned:
                if b and re.search(rf"(^|-){re.escape(b)}(-|$)", name):
                    errors.append(f"{folder}/{full}: contains '{b}' from banned-names.txt")
            if p.endswith(".liquid") and folder in ("sections", "blocks"):
                m = re.search(r"{%-?\s*schema\s*-?%}(.*?){%-?\s*endschema\s*-?%}", open(p, encoding="utf-8", errors="ignore").read(), re.S)
                if m:
                    try:
                        sname = json.loads(strip_jsonc(m.group(1))).get("name", "")
                    except ValueError:
                        sname = ""
                    if sname and not sname.startswith("t:"):
                        errors.append(f"{folder}/{full}: schema name '{sname}' should be a t: key")
    ts = os.path.join(a.theme, "config", "settings_schema.json")
    if os.path.exists(ts):
        text = open(ts, encoding="utf-8").read()
        if re.search(r'"theme_(author|documentation_url|support_url)"\s*:\s*"[^"]*(isrc|isourceit)', text, re.I):
            errors.append("config/settings_schema.json: theme_info names the agency")
    for e in errors:
        print(f"NAME {e}")
    print(f"{len(errors)} naming issue(s)")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
