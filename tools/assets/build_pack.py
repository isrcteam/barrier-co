#!/usr/bin/env python3
"""Build a named, mapped asset pack from docs/assets/manifest.json.

Usage: python3 build_pack.py --purpose theme [--manifest docs/assets/manifest.json] [--files docs/data/raw/<ts>/files.json]
                             [--theme .] [--no-map]
For every asset in the manifest (or only those whose dest matches --purpose, unless --purpose all):
  - names it <name>[-<variant>].<ext> (lowercase kebab-case, no versions, layer names, agency or client names)
  - resizes: mobile variants to 1080 px wide max, others to max_width if set (default 3840)
  - flags a clash with a file already in the store's Files (from the export's files.json)
  - writes shopify://shop_images/<filename> into every template or settings file listed under "maps"
  - copies it into the pack folder for its destination
Then zips docs/assets/dist/<project>-assets-<purpose>-v<n>.zip with a README checklist, and rewrites docs/assets.md.

Manifest entry:
  {"source": "docs/assets/source/home/hero-desktop.jpg", "name": "home-hero", "variant": "desktop",
   "dest": "theme", "alt": "Folded towels on a bench", "from": "Figma 12:345",
   "maps": [{"file": "templates/index.json", "path": "sections.hero.settings.image_desktop"}]}
dest is one of: theme, checkout, brand, email, social.
"""
import argparse, datetime, json, os, re, shutil, sys, zipfile
from PIL import Image

DESTS = ["theme", "checkout", "brand", "email", "social"]
BANNED = re.compile(r"(^|-)(v\d+|new|copy|final|old|untitled|isrc|isourceit|img|image-\d+|(frame|group|layer|rectangle)-?\d*)(-|$)")
STEPS = {
    "theme": "Upload everything in theme/ to Content › Files with the names unchanged, then run check_refs.py before pushing or previewing the theme.",
    "checkout": "Settings › Checkout › Customise: upload the logo from checkout/ and enter the values in checkout-settings.md.",
    "brand": "Settings › Brand: upload the logo, square logo and cover image from brand/, and set the colours from checkout-settings.md.",
    "email": "Settings › Notifications › Customise email templates: upload the email logo from email/.",
    "social": "Online Store › Preferences: set the social sharing image from social/. The theme also uses it as its default share image.",
}



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

def lenient(path):
    raw = open(path, encoding="utf-8").read()
    banner = re.match(r"\s*/\*.*?\*/\s*", raw, re.S)
    body = raw[banner.end():] if banner else raw
    return (banner.group(0) if banner else ""), json.loads(strip_jsonc(body))


def set_path(data, path, value):
    keys = path.split(".")
    node = data
    for k in keys[:-1]:
        if k not in node:
            raise KeyError(f"'{k}' not found")
        node = node[k]
    node[keys[-1]] = value


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--purpose", required=True, choices=DESTS + ["all"])
    ap.add_argument("--manifest", default="docs/assets/manifest.json")
    ap.add_argument("--files")
    ap.add_argument("--theme", default=".")
    ap.add_argument("--no-map", action="store_true")
    a = ap.parse_args()
    man = json.load(open(a.manifest))
    project = man["project"]
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", project):
        sys.exit(f"project '{project}' must be lowercase kebab-case")
    existing = set()
    if a.files and os.path.exists(a.files):
        for f in json.load(open(a.files)):
            url = (f.get("image") or {}).get("url") or f.get("url") or ""
            if url:
                existing.add(os.path.basename(url.split("?")[0]).lower())
    assets = [x for x in man["assets"] if a.purpose == "all" or x["dest"] == a.purpose]
    if not assets:
        sys.exit(f"No assets with dest '{a.purpose}' in the manifest")
    dist = os.path.join("docs", "assets", "dist")
    os.makedirs(dist, exist_ok=True)
    n = 1
    while os.path.exists(os.path.join(dist, f"{project}-assets-{a.purpose}-v{n}.zip")):
        n += 1
    zip_name = f"{project}-assets-{a.purpose}-v{n}.zip"
    stage = os.path.join(dist, f"_{project}-{a.purpose}-v{n}")
    shutil.rmtree(stage, ignore_errors=True)
    errors, warnings, rows, mapped = [], [], [], 0
    json_cache = {}
    names = set()
    extra_banned = []
    if os.path.exists("docs/banned-names.txt"):
        extra_banned = [l.strip().lower() for l in open("docs/banned-names.txt") if l.strip() and not l.startswith("#")]
    for x in assets:
        if x["dest"] not in DESTS:
            errors.append(f"{x['name']}: dest must be one of {', '.join(DESTS)}")
            continue
        if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", x["name"]) or BANNED.search(x["name"]) or \
                project in x["name"].split("-") or any(w in x["name"] for w in extra_banned):
            errors.append(f"{x['name']}: use a plain kebab-case name for what it is, with no versions, layer names, agency or client names")
            continue
        ext = os.path.splitext(x["source"])[1].lower().replace(".jpeg", ".jpg")
        filename = x["name"] + (f"-{x['variant']}" if x.get("variant") else "") + ext
        if filename in names:
            errors.append(f"{filename}: two assets would get the same name")
            continue
        names.add(filename)
        if filename.lower() in existing:
            warnings.append(f"{filename} already exists in the store's Files. Uploading it again saves a renamed copy and breaks the reference. Rename or reuse it.")
        if not os.path.exists(x["source"]):
            errors.append(f"{x['source']}: missing")
            continue
        out_dir = os.path.join(stage, x["dest"])
        os.makedirs(out_dir, exist_ok=True)
        out = os.path.join(out_dir, filename)
        if ext in (".jpg", ".png", ".webp"):
            im = Image.open(x["source"])
            cap = 1080 if x.get("variant") == "mobile" else x.get("max_width", 3840)
            if im.width > cap:
                im = im.resize((cap, round(im.height * cap / im.width)), Image.LANCZOS)
            if ext == ".jpg":
                im.convert("RGB").save(out, quality=85, optimize=True, progressive=True)
            else:
                im.save(out, optimize=True)
            size = f"{im.width}×{im.height}"
        else:
            shutil.copy(x["source"], out)
            size = ""
        ref = f"shopify://shop_images/{filename}"
        targets = []
        if not a.no_map:
            for m in x.get("maps", []):
                path = os.path.join(a.theme, m["file"])
                if path not in json_cache:
                    if not os.path.exists(path):
                        errors.append(f"{filename}: {m['file']} not found")
                        continue
                    json_cache[path] = lenient(path)
                try:
                    set_path(json_cache[path][1], m["path"], ref)
                    targets.append(f"{m['file']} › {m['path']}")
                    mapped += 1
                except KeyError as e:
                    errors.append(f"{filename}: {m['file']} {m['path']}: {e}")
        rows.append((filename, x["dest"], x.get("variant", ""), size, x.get("alt", ""), x.get("from", ""), "; ".join(targets)))
    if errors:
        shutil.rmtree(stage, ignore_errors=True)
        print("Not built:")
        for e in errors:
            print(f"  {e}")
        sys.exit(1)
    for path, (banner, data) in json_cache.items():
        open(path, "w", encoding="utf-8").write(banner + json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    dests = sorted({r[1] for r in rows})
    readme = [f"# {project} assets: {a.purpose} v{n}", "", f"Built {datetime.date.today()}. File names are final: don't rename them, the theme already points at them.", "", "## Steps, in order", ""]
    readme += [f"{i}. **{d}/**: {STEPS[d]}" for i, d in enumerate(dests, 1)]
    readme += ["", "## Files", "", "| File | Where | Variant | Size | Alt text |", "| --- | --- | --- | --- | --- |"]
    readme += [f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} |" for r in rows]
    if os.path.exists("docs/assets/checkout-settings.md") and ("checkout" in dests or "brand" in dests):
        shutil.copy("docs/assets/checkout-settings.md", os.path.join(stage, "checkout-settings.md"))
    open(os.path.join(stage, "README.md"), "w").write("\n".join(readme) + "\n")
    with zipfile.ZipFile(os.path.join(dist, zip_name), "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(stage):
            for f in files:
                full = os.path.join(root, f)
                z.write(full, os.path.relpath(full, stage))
    shutil.rmtree(stage)
    reg = "docs/assets.md"
    lines = open(reg).read().splitlines() if os.path.exists(reg) else ["# Assets", "", "| File | Destination | Variant | Size | Source | Mapped to | Pack | Uploaded |", "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    lines = [l for l in lines if not any(l.startswith(f"| {r[0]} |") for r in rows)]
    lines += [f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[5]} | {r[6]} | {zip_name} | |" for r in rows]
    open(reg, "w").write("\n".join(lines) + "\n")
    print(f"Built docs/assets/dist/{zip_name}: {len(rows)} files, {mapped} reference(s) written into theme JSON.")
    for w in warnings:
        print(f"WARN {w}")


if __name__ == "__main__":
    main()
