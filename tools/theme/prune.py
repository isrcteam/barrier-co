#!/usr/bin/env python3
"""Find theme files, locale keys and settings nothing uses, and remove them once approved.

Usage: python3 tools/theme/prune.py [--theme .] [--keep docs/prune-keep.txt]          writes docs/prune-report.md
       python3 tools/theme/prune.py --apply                needs an "Approved: prune" row in the plan's approval log
Starts from every template, section group, layout and settings_data.json and follows sections, theme blocks,
snippets, content_for blocks, schema block types, presets and assets. Anything not reached is a candidate.
Always kept: layout, config, templates, section groups, the apps section, the basic sections in
prune-keep.default.txt (next to this script) and anything in docs/prune-keep.txt. Only web assets are candidates.
Can't prove unused (listed for a decision, never auto-deleted): dynamic renders, and theme blocks when a
section accepts "@theme" (the merchant can add any block).
--apply deletes candidates (and their src/scss and src/ts entrypoints), prunes unused locale keys, and
appends everything removed to docs/pruned-files.txt so Horizon updates can re-apply it.
"""
import argparse, glob, gzip, json, os, re, sys

# No "{%" anchor: Horizon renders inside {% liquid %} tags, one statement per line.
RENDER = re.compile(r"\b(?:render|include)\s+['\"]([^'\"]+)['\"]")
DYN_RENDER = re.compile(r"\b(?:render|include)\s+(?!['\"])([a-z_][\w.]*)")
SECTION = re.compile(r"\bsection\s+['\"]([^'\"]+)['\"]")
SECTIONS = re.compile(r"\bsections\s+['\"]([^'\"]+)['\"]")
JS_IMPORT = re.compile(r"(?:from\s*|import\s*\(?\s*)['\"](?:@theme/|\./)([\w.\-]+?)(?:\.js)?['\"]")
DYN_ASSET = re.compile(r"(?<!['\"])\b[a-z_][\w.]*\s*\|\s*(?:append:[^|}]+\|\s*)*(?:asset_url|inline_asset_content)")
CONTENT_FOR = re.compile(r"content_for\s+['\"]block['\"]\s*,\s*type:\s*['\"]([^'\"]+)['\"]")
ASSET = re.compile(r"['\"]([\w.\-]+\.(?:js|css|svg|png|jpg|jpeg|gif|webp|woff2?|json))['\"]\s*\|\s*(?:asset_url|asset_img_url|inline_asset_content)")
SCHEMA = re.compile(r"{%-?\s*schema\s*-?%}(.*?){%-?\s*endschema\s*-?%}", re.S)
T_KEY = re.compile(r"['\"]([a-z0-9_]+(?:\.[a-z0-9_]+)+)['\"]\s*\|\s*t\b")
T_SCHEMA = re.compile(r"\"t:([a-z0-9_.]+)\"")
WEB_ASSET = re.compile(r"\.(js|css|svg|png|jpe?g|gif|webp|avif|woff2?|ttf|otf|mp4|webm)$")
SETTING = re.compile(r"\bsettings\.([a-z0-9_]+)")



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

DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")


def approval(phrase, plan_path):
    """The Approval log section of docs/plan.md must hold a table row whose first cell is the phrase, with a date and an approver."""
    if not os.path.exists(plan_path):
        return False, f"{plan_path} doesn't exist"
    text = open(plan_path, encoding="utf-8").read()
    m = re.search(r"^#+\s*Approval log\s*$(.*?)(?=^#+\s|\Z)", text, re.S | re.M | re.I)
    if not m:
        return False, "docs/plan.md has no 'Approval log' section"
    want = re.sub(r"\s+", " ", phrase.strip().lower())
    bare = want[len("approved: "):]
    incomplete = None
    for line in m.group(1).splitlines():
        line = line.strip()
        if line.startswith("|"):
            cells = [c.strip().strip("`").strip() for c in line.strip("|").split("|")]
            if len(cells) < 3 or set(cells[0]) <= set("-: "):
                continue
            if re.sub(r"\s+", " ", cells[0].lower()) in (want, bare):
                date = next((c for c in cells[1:] if DATE.search(c)), "")
                who = next((c for c in cells[1:] if c and not DATE.search(c)), "")
                if date and who:
                    return True, f"{who}, {DATE.search(date).group(0)}"
                incomplete = f"'{cells[0]}' is in the approval log but needs a date and an approver"
        elif re.sub(r"\s+", " ", line.lstrip("-* ").lower()).startswith(want) and DATE.search(line):
            return True, DATE.search(line).group(0)
    return False, incomplete or f"'{phrase}' isn't in the Approval log of {plan_path}"


def lenient(path):
    raw = open(path, encoding="utf-8", errors="ignore").read()
    raw = re.sub(r"^\s*/\*.*?\*/", "", raw, flags=re.S)
    try:
        return json.loads(strip_jsonc(raw))
    except ValueError:
        return {}


def json_types(obj, out):
    if isinstance(obj, dict):
        t = obj.get("type")
        if isinstance(t, str):
            out.add(t)
        for v in obj.values():
            json_types(v, out)
    elif isinstance(obj, list):
        for v in obj:
            json_types(v, out)


def flatten(d, prefix=""):
    for k, v in d.items():
        key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            yield from flatten(v, key)
        else:
            yield key


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--theme", default=".")
    ap.add_argument("--keep", default="docs/prune-keep.txt")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    T = a.theme
    rel = lambda p: os.path.relpath(p, T)
    exists = lambda r: os.path.exists(os.path.join(T, r))
    keep = set()
    default_keep = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prune-keep.default.txt")
    for kf in (default_keep, os.path.join(T, a.keep) if not os.path.isabs(a.keep) else a.keep):
        if os.path.exists(kf):
            keep |= {l.strip() for l in open(kf) if l.strip() and not l.startswith("#")}

    roots = set()
    for pat in ("layout/*.liquid", "templates/*.json", "templates/*.liquid", "templates/customers/*", "sections/*.json", "config/settings_data.json"):
        roots |= {rel(p) for p in glob.glob(os.path.join(T, pat))}
    if exists("sections/apps.liquid"):
        roots.add("sections/apps.liquid")
    roots |= {k for k in keep if exists(k)}

    dynamic, open_blocks, dynamic_assets = [], [], []

    def walk(queue, reached):
        while queue:
            f = queue.pop()
            if f in reached or not exists(f):
                continue
            reached.add(f)
            path = os.path.join(T, f)
            found = []
            if f.endswith(".json"):
                types = set()
                json_types(lenient(path), types)
                for t in types:
                    if t.startswith(("shopify://", "@")):
                        continue
                    found += [f"sections/{t}.liquid", f"blocks/{t}.liquid"]
            elif f.endswith(".liquid"):
                text = open(path, encoding="utf-8", errors="ignore").read()
                found += [f"snippets/{n}.liquid" for n in RENDER.findall(text)]
                found += [f"sections/{n}.liquid" for n in SECTION.findall(text)]
                found += [f"sections/{n}.json" for n in SECTIONS.findall(text)]
                found += [f"blocks/{n}.liquid" for n in CONTENT_FOR.findall(text)]
                found += [f"assets/{n}" for n in ASSET.findall(text)] + [f"src/assets/{n}" for n in ASSET.findall(text)]
                for d in DYN_RENDER.findall(text):
                    dynamic.append(f"{f}: renders `{d}` by variable")
                if DYN_ASSET.search(text):
                    dynamic_assets.append(f)
                m = SCHEMA.search(text)
                if m:
                    try:
                        schema = json.loads(strip_jsonc(m.group(1)))
                    except ValueError:
                        schema = {}
                    types = set()
                    json_types({"blocks": schema.get("blocks", []), "presets": schema.get("presets", []), "default": schema.get("default", {})}, types)
                    if "@theme" in types:
                        open_blocks.append(f)
                    found += [f"blocks/{t}.liquid" for t in types if not t.startswith(("@", "shopify://"))]
            elif f.endswith(".js"):
                text = open(path, encoding="utf-8", errors="ignore").read()
                found += [f"{os.path.dirname(f)}/{n}.js" for n in JS_IMPORT.findall(text)]
            queue += [x for x in found if exists(x)]
        return reached

    reached = walk(list(roots), set())

    candidates = []
    for folder in ("sections", "blocks", "snippets"):
        for p in glob.glob(os.path.join(T, folder, "*.liquid")):
            r = rel(p)
            if r not in reached and r not in keep:
                candidates.append(r)
    asset_dir = "src/assets" if os.path.isdir(os.path.join(T, "src", "assets")) else "assets"
    compiled = re.compile(r"^(theme|block-|section-|snippet-|template-|chunk-)")
    for p in glob.glob(os.path.join(T, asset_dir, "*")):
        r = rel(p)
        if not WEB_ASSET.search(r):
            continue
        if r not in reached and r not in keep and not (asset_dir == "assets" and compiled.match(os.path.basename(p))):
            candidates.append(r)
    # A file whose name still appears in a kept file may be used in a way the graph can't follow.
    kept_text = "\n".join(open(os.path.join(T, r), encoding="utf-8", errors="ignore").read() for r in reached
                          if r.endswith((".liquid", ".json", ".js")))
    def mentioned(c):
        stem = os.path.splitext(os.path.basename(c))[0]
        return re.search(r"['\"/]" + re.escape(stem) + r"(?:\.\w+)?['\"]", kept_text) is not None
    unprovable = [c for c in candidates if (c.startswith("blocks/") and open_blocks) or mentioned(c)
                  or (c.startswith(("assets/", "src/assets/")) and dynamic_assets)]
    first_pass = set(unprovable)
    # Anything an undecided file uses has to wait for that decision too.
    held = walk(list(unprovable), set())
    unprovable += [c for c in candidates if c in held and c not in unprovable]
    certain = [c for c in candidates if c not in unprovable]

    used_keys, used_schema_keys, used_settings = set(), set(), set()
    for p in glob.glob(os.path.join(T, "**", "*.liquid"), recursive=True) + glob.glob(os.path.join(T, "**", "*.json"), recursive=True):
        if "/locales/" in p or "node_modules" in p or rel(p) in certain:
            continue
        text = open(p, encoding="utf-8", errors="ignore").read()
        used_keys |= set(T_KEY.findall(text))
        used_schema_keys |= set(T_SCHEMA.findall(text))
        used_settings |= set(SETTING.findall(text))
    gone_keys, gone_schema_keys = set(), set()
    for c in certain:
        if c.endswith((".liquid", ".json")):
            text = open(os.path.join(T, c), encoding="utf-8", errors="ignore").read()
            gone_keys |= set(T_KEY.findall(text))
            gone_schema_keys |= set(T_SCHEMA.findall(text))
    loc_unused, loc_advisory = {}, {}
    for loc in glob.glob(os.path.join(T, "locales", "*.json")):
        schema = loc.endswith(".schema.json")
        keys = set(flatten(lenient(loc)))
        used = used_schema_keys if schema else used_keys
        gone = gone_schema_keys if schema else gone_keys
        unused = sorted(k for k in keys if k not in used and not any(k.startswith(u + ".") for u in used))
        # Only keys the removed files used, and nothing kept uses, are pruned. The rest may be read
        # through dynamic keys or JS, so they're listed for a manual look and never deleted.
        safe = [k for k in unused if k in gone]
        if safe:
            loc_unused[rel(loc)] = safe
        rest = [k for k in unused if k not in gone]
        if rest:
            loc_advisory[rel(loc)] = rest
    settings_unused = []
    ss = os.path.join(T, "config", "settings_schema.json")
    if os.path.exists(ss):
        for g in lenient(ss) if isinstance(lenient(ss), list) else []:
            for s in g.get("settings", []):
                sid = s.get("id")
                if sid and s.get("type") not in ("header", "paragraph", "color_scheme_group") and sid not in used_settings:
                    settings_unused.append(sid)

    size = lambda files: sum(os.path.getsize(os.path.join(T, f)) for f in files if exists(f))
    all_files = [rel(p) for p in glob.glob(os.path.join(T, "*", "*")) if rel(p).split("/")[0] in ("sections", "blocks", "snippets", "assets", "templates", "layout", "config", "locales")]
    L = ["# Prune report", "", f"{len(certain)} files can go, {len(unprovable)} need a decision. Theme files now: {len(all_files)}, {size(all_files)//1024} KB. After: {len(all_files)-len(certain)}, {(size(all_files)-size(certain))//1024} KB.", "",
         "Nothing is deleted until `Approved: prune` is in the plan. To keep something, add its path to `docs/prune-keep.txt` (the merchant toolkit belongs there).", "",
         "## Unused, safe to remove", "", "| File | KB |", "| --- | --- |"] + [f"| `{c}` | {size([c])//1024 or '<1'} |" for c in sorted(certain)]
    L += ["", "## Can't prove unused", "", "Theme blocks when a section accepts `@theme`, files whose name still appears in kept code, assets when a file loads assets by variable, and dynamic renders. Decide each one; add keepers to the keep file.", ""]
    if unprovable:
        def why(c):
            if mentioned(c):
                return "name appears in kept code"
            if c in held and c not in first_pass:
                return "used by another file on this list"
            if c.startswith("blocks/"):
                return "sections accept any theme block: " + ", ".join(open_blocks[:3]) + ("…" if len(open_blocks) > 3 else "")
            return "assets loaded by variable in " + ", ".join(dynamic_assets[:3]) + ("…" if len(dynamic_assets) > 3 else "")
        L += [f"- [ ] `{c}` ({why(c)})" for c in sorted(unprovable)]
    L += [f"- [ ] {d}" for d in dynamic]
    L += ["", "## Locale keys removed with the files", "", "Only used by the files above. Pruned on apply.", ""] + [f"- `{f}`: {len(k)} keys, e.g. {', '.join(k[:5])}" for f, k in loc_unused.items()]
    L += ["", "## Locale keys with no static reference (advisory)", "",
          "Could be read through dynamic keys or JavaScript. Never deleted by the script. Leave them unless you've checked.", ""]
    L += [f"- `{f}`: {len(k)} keys" for f, k in loc_advisory.items()]
    L += ["", "## Theme settings nothing reads", ""] + [f"- `{s}`" for s in settings_unused]
    os.makedirs(os.path.join(T, "docs"), exist_ok=True)
    open(os.path.join(T, "docs", "prune-report.md"), "w").write("\n".join(L) + "\n")
    print(f"Wrote docs/prune-report.md: {len(certain)} removable, {len(unprovable) + len(dynamic)} to decide, "
          f"{sum(len(v) for v in loc_unused.values())} locale keys to prune, {len(settings_unused)} unused settings.")
    if not a.apply:
        return
    ok, detail = approval("Approved: prune", os.path.join(T, "docs", "plan.md"))
    if not ok:
        sys.exit(f"Refusing: {detail}. Add a row to the approval log: | Approved: prune | YYYY-MM-DD | Jeet | |")
    print(f"Approval found: Approved: prune ({detail})")
    removed = []
    for c in certain:
        os.remove(os.path.join(T, c))
        removed.append(c)
        folder, name = c.split("/")[0], os.path.splitext(os.path.basename(c))[0]
        for ext_dir, ext in (("scss", "scss"), ("ts", "ts")):
            src = os.path.join(T, "src", ext_dir, "entrypoints", folder, f"{name}.{ext}")
            if os.path.exists(src):
                os.remove(src)
                removed.append(rel(src))
    for f, keys in loc_unused.items():
        data = lenient(os.path.join(T, f))
        if not data:
            print(f"Skipped {f}: couldn't parse it, left as is.")
            continue
        for k in keys:
            parts, node = k.split("."), data
            for p in parts[:-1]:
                node = node.get(p, {})
            node.pop(parts[-1], None)
        def clean(d):
            for k in list(d):
                if isinstance(d[k], dict):
                    clean(d[k])
                    if not d[k]:
                        del d[k]
        clean(data)
        raw = open(os.path.join(T, f), encoding="utf-8").read()
        banner = re.match(r"\s*/\*.*?\*/\s*", raw, re.S)
        open(os.path.join(T, f), "w").write((banner.group(0) if banner else "") + json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    with open(os.path.join(T, "docs", "pruned-files.txt"), "a") as out:
        out.write("\n".join(removed) + "\n")
    print(f"Removed {len(removed)} files and the unused locale keys. Listed in docs/pruned-files.txt. Run the checks, visual diff and QA next.")


if __name__ == "__main__":
    main()
