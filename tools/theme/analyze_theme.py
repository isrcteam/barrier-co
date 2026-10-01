#!/usr/bin/env python3
"""Map the live theme against the store data, and audit apps and scripts.

Usage: python3 tools/theme/analyze_theme.py [docs/data/raw/<timestamp>] [--theme <folder>] [--requests requests.json]
         [--out docs/data/theme-data-map.md]
--theme defaults to <run>/theme (downloaded by export.py). Use a `shopify theme pull --live` folder if the
export had no read_themes scope. --requests takes the network recording from record_requests.mjs.

Writes a report with a Decision and Reason column on every row. Decisions survive reruns.
Decisions: keep · restructure · retire (templates, metafields) and keep · disable · remove code · replace · ask client (apps).
"""
import argparse, collections, glob, json, os, re, sys
from urllib.parse import urlparse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "shopify"))
try:
    from shopify_client import standard_match
except ImportError:  # tools/shopify missing: no standard-definition hints
    def standard_match(owner, key):
        return None

KNOWN_APPS = {
    "klaviyo": "Klaviyo", "judge.me": "Judge.me", "judgeme": "Judge.me", "okendo": "Okendo", "yotpo": "Yotpo", "stamped": "Stamped",
    "loox": "Loox", "trustpilot": "Trustpilot", "rebuy": "Rebuy", "rechargeapps": "Recharge", "recharge": "Recharge", "skio": "Skio",
    "stay.ai": "Stay AI", "retextion": "Stay AI", "loopreturns": "Loop", "loopsubscriptions": "Loop Subscriptions", "gorgias": "Gorgias",
    "hotjar": "Hotjar", "clarity.ms": "Microsoft Clarity", "googletagmanager": "Google Tag Manager", "google-analytics": "Google Analytics",
    "connect.facebook": "Meta pixel", "facebook.net": "Meta pixel", "tiktok": "TikTok pixel", "pinimg": "Pinterest tag",
    "attentive": "Attentive", "postscript": "Postscript", "privy": "Privy", "justuno": "Justuno", "smile.io": "Smile.io",
    "pagefly": "PageFly", "gempages": "GemPages", "shogun": "Shogun", "replo": "Replo", "upcart": "Upcart", "kaching": "Kaching Bundles",
    "foxsell": "FoxSell", "boldapps": "Bold", "bold-": "Bold", "zipify": "Zipify", "intelligems": "Intelligems", "elevar": "Elevar",
    "triplewhale": "Triple Whale", "northbeam": "Northbeam", "vwo": "VWO", "optimizely": "Optimizely", "searchanise": "Searchanise",
    "boostcommerce": "Boost", "globo": "Globo", "weglot": "Weglot", "langify": "Langify", "afterpay": "Afterpay", "klarna": "Klarna",
    "affirm": "Affirm", "shopify-chat": "Shopify Inbox", "tidio": "Tidio", "zendesk": "Zendesk", "aftership": "AfterShip",
    "judgeme_": "Judge.me", "swym": "Swym Wishlist", "wishlist": "Wishlist app", "accessibe": "accessiBe", "userway": "UserWay",
}
NATIVE_HINTS = {
    "Searchanise": "Search & Discovery", "Boost": "Search & Discovery", "Globo": "Search & Discovery filters",
    "Kaching Bundles": "Shopify Bundles", "FoxSell": "Shopify Bundles or a Cart Transform function",
    "PageFly": "theme sections and templates", "GemPages": "theme sections and templates", "Shogun": "theme sections and templates",
    "Replo": "theme sections and templates", "Weglot": "Shopify Translate & Adapt", "Langify": "Shopify Translate & Adapt",
    "Upcart": "a theme cart drawer", "Privy": "Shopify Forms", "Justuno": "Shopify Forms",
}
OWNER = {"product": "PRODUCT", "variant": "PRODUCTVARIANT", "selected_variant": "PRODUCTVARIANT", "current_variant": "PRODUCTVARIANT",
         "collection": "COLLECTION", "page": "PAGE", "article": "ARTICLE", "blog": "BLOG", "shop": "SHOP", "localization": "MARKET"}
MF_RE = re.compile(r"(\w+)\.metafields\.([a-z0-9_\-]+)\.([a-z0-9_\-]+)", re.I)
MF_BRACKET = re.compile(r"(\w+)\.metafields\[['\"]([^'\"]+)['\"]\]\[['\"]([^'\"]+)['\"]\]")
MO_RE = re.compile(r"shop\.metaobjects\.([a-z0-9_\-]+)", re.I)
SCRIPT_SRC = re.compile(r"<script[^>]+src=['\"]([^'\"]+)['\"]", re.I)
RENDER = re.compile(r"{%-?\s*(?:render|include|section)\s+['\"]([^'\"]+)['\"]")



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

def latest_run(root="docs/data/raw"):
    runs = sorted(d for d in glob.glob(os.path.join(root, "*")) if os.path.isdir(d))
    usable = []
    for r in runs:
        p = os.path.join(r, "summary.json")
        try:
            summary = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None
        except ValueError:
            summary = None
        if summary and summary.get("complete", True) and not summary.get("partial"):
            usable.append(r)
    if not usable:
        raise SystemExit(f"No complete export in {root}. Run export.py (a --only run doesn't count), or pass the run folder.")
    return usable[-1]


def load(run, name, default=None):
    p = os.path.join(run, f"{name}.json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else default


def lenient(path):
    raw = open(path, encoding="utf-8", errors="ignore").read()
    raw = re.sub(r"^\s*/\*.*?\*/", "", raw, flags=re.S)
    try:
        return json.loads(strip_jsonc(raw))
    except ValueError:
        return {}


def app_name(text):
    low = text.lower()
    for key, name in KNOWN_APPS.items():
        if key in low:
            return name
    return None


def prior(path):
    keep = {}
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            if line.startswith("| `"):
                c = [x.strip() for x in line.strip().strip("|").split("|")]
                keep[c[0]] = (c[-2], c[-1])
    return keep


def row(key, cells, dec):
    d, r = dec.get(key, ("", ""))
    return "| " + " | ".join([key] + [str(x) for x in cells] + [d, r]) + " |"


def write_app_plan(path, embeds, app_blocks, scripts, dec):
    """Launch checklist for apps, from the decisions in the theme data map. Ticks survive reruns."""
    done = set()
    if os.path.exists(path):
        done = {l.strip()[6:] for l in open(path, encoding="utf-8") if l.strip().startswith("- [x] ")}
    groups = {"Before publish": [], "After publish": [], "Clean-up": [], "Decide first": []}
    def add(group, text):
        groups[group].append(f"- [{'x' if text in done else ' '}] {text}")
    for app, block, on in sorted(embeds):
        d = dec.get(f"`{app}`", ("", ""))[0].lower()
        if not d:
            add("Decide first", f"{app} embed ({'on' if on else 'off'} on the live theme): keep, disable or replace?")
        elif d.startswith("keep"):
            add("Before publish", f"Switch on the {app} embed in the new theme (Customize › App embeds) and check it on the preview")
        elif d.startswith(("disable", "remove")):
            add("Clean-up", f"Leave the {app} embed off. If the app is unused, ask the client to uninstall it")
        else:
            add("Before publish", f"{app} embed: {d}")
    for app, where in sorted(app_blocks.items()):
        d = dec.get(f"`{app}`", ("", ""))[0].lower()
        if not d:
            add("Decide first", f"{app} app blocks in {'; '.join(sorted(where))[:200]}: keep, replace or remove?")
        elif d.startswith("keep"):
            add("Before publish", f"Re-place the {app} block in the new templates: {'; '.join(sorted(where))[:200]}")
        else:
            add("Before publish", f"{app} blocks: {d}")
    for host, files in sorted(scripts.items()):
        name = app_name(host) or host
        d, r = dec.get(f"`{host}`", ("", ""))
        d = d.lower()
        if not d:
            add("Decide first", f"{name} script from {host} in {', '.join(sorted(files))[:150]}: keep, move or remove?")
        elif d.startswith("keep"):
            add("Before publish", f"Carry the {name} script into the new theme ({', '.join(sorted(files))[:150]}), with a reasoning entry")
        elif d.startswith("replace"):
            hint = r or NATIVE_HINTS.get(app_name(host) or "", "move it to Customer events or GTM")
            add("Before publish", f"Replace the hard-coded {name} script ({hint}). Check events fire on the preview")
        elif d.startswith(("remove", "disable")):
            add("Clean-up", f"Don't carry the {name} script across. Confirm with the client that nothing depends on it")
        else:
            add("Before publish", f"{name}: {d}")
    add("Before publish", "Apps that install code into the theme on setup (not embeds): ask each one to install on the new unpublished theme")
    add("After publish", "Check every kept app on the live theme: widget shows, events arrive in the app's dashboard")
    add("After publish", "Record requests on the live site again and compare with docs/data/third-party-requests.json")
    L = ["# App migration plan", "", "Generated from the Decision column in docs/data/theme-data-map.md. Rerun analyze_theme.py after changing a decision; ticks are kept.", ""]
    for g, items in groups.items():
        if items:
            L += [f"## {g}", ""] + items + [""]
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf-8").write("\n".join(L))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run", nargs="?")
    ap.add_argument("--theme")
    ap.add_argument("--requests")
    ap.add_argument("--out", default="docs/data/theme-data-map.md")
    ap.add_argument("--app-plan", default="docs/launch/app-migration.md")
    a = ap.parse_args()
    run = a.run or latest_run()
    theme = a.theme or os.path.join(run, "theme")
    if not os.path.isdir(theme):
        raise SystemExit(f"No theme files at {theme}. Run the export with read_themes, or `shopify theme pull --live` and pass --theme.")
    dec = prior(a.out)

    liquid = {os.path.relpath(p, theme): open(p, encoding="utf-8", errors="ignore").read()
              for p in glob.glob(os.path.join(theme, "**", "*.liquid"), recursive=True)}
    jsons = {os.path.relpath(p, theme): lenient(p) for p in glob.glob(os.path.join(theme, "**", "*.json"), recursive=True)
             if not os.path.relpath(p, theme).startswith("locales")}

    used_mf = collections.defaultdict(set)
    used_mo = collections.defaultdict(set)
    for f, text in liquid.items():
        for m in list(MF_RE.finditer(text)) + list(MF_BRACKET.finditer(text)):
            owner = OWNER.get(m.group(1).lower(), m.group(1).lower())
            used_mf[(owner, f"{m.group(2)}.{m.group(3)}")].add(f)
        for m in MO_RE.finditer(text):
            used_mo[m.group(1)].add(f)
    for f, data in jsons.items():
        blob = json.dumps(data)
        for m in re.finditer(r"(product|collection|page|article|shop|variant)\.metafields\.([a-z0-9_\-]+)\.([a-z0-9_\-]+)", blob, re.I):
            used_mf[(OWNER[m.group(1).lower()], f"{m.group(2)}.{m.group(3)}")].add(f)

    defs = load(run, "metafield_definitions", [])
    mo_defs = load(run, "metaobject_definitions", [])
    owners_data = {"PRODUCT": load(run, "products", []), "PRODUCTVARIANT": load(run, "variants", []),
                   "COLLECTION": load(run, "collections", []), "PAGE": load(run, "pages", []), "ARTICLE": load(run, "articles", [])}
    fill = collections.Counter()
    for owner, items in owners_data.items():
        for it in items:
            mfs = it.get("metafields") or {}
            for m in (mfs.get("nodes", []) if isinstance(mfs, dict) else mfs):
                if m.get("value") not in (None, "", "[]"):
                    fill[(owner, f"{m['namespace']}.{m['key']}")] += 1
    defined = {(d["ownerType"], f"{d['namespace']}.{d['key']}"): d for d in defs}

    L = ["# Theme and data map", "", f"Theme: `{theme}` · Data: `{run}`. Rebuilt by `analyze_theme.py`; Decision and Reason columns are kept between runs.", "",
         "Rule: reuse by default. Restructure only when it clearly pays off, and give the reason. Restructures are approved with the plan.", ""]

    L += ["## Metafields: definitions vs theme vs data", "", "| Key | Owner | Defined | Rendered in theme | Filled | Signal | Decision | Reason |", "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    keys = sorted(set(defined) | set(used_mf) | set(fill), key=lambda k: (k[0], k[1]))
    for owner, key in keys:
        if key.startswith(("app--", "shopify--")):
            continue
        is_def = (owner, key) in defined
        files = used_mf.get((owner, key), set())
        n = fill.get((owner, key), 0)
        total = len(owners_data.get(owner, [])) or ""
        if not files and n == 0:
            signal = "unused: retire candidate"
        elif not files and not is_def:
            signal = "data only: no definition, not rendered"
        elif not files:
            signal = "has data, not rendered"
        elif files and not is_def:
            signal = "rendered, no definition"
        elif files and n == 0:
            signal = "rendered, never filled"
        else:
            signal = "in use"
        std = standard_match(owner, key)
        if std:
            signal += f"; standard definition exists: {std}"
        L.append(row(f"`{key}`", [owner.lower(), "yes" if is_def else "no", f"{len(files)} file(s)" if files else "no",
                                  f"{n}/{total}" if total else str(n), signal], dec))

    groups = collections.defaultdict(list)
    for (owner, key), d in defined.items():
        if owner == "PRODUCT":
            stem = re.split(r"[_\-]", key.split(".", 1)[1])[0]
            groups[stem].append(key)
    cands = {s: k for s, k in groups.items() if len(k) >= 3}
    if cands:
        L += ["", "### Metaobject candidates", "", "Groups of product metafields sharing a stem often describe one thing and could be a single metaobject.", "",
              "| Stem | Metafields | Decision | Reason |", "| --- | --- | --- | --- |"]
        for stem, ks in sorted(cands.items()):
            L.append(row(f"`{stem}_*`", [", ".join(sorted(ks))], dec))

    L += ["", "## Metaobjects", "", "| Type | Entries | Rendered directly | Decision | Reason |", "| --- | --- | --- | --- | --- |"]
    for d in mo_defs:
        files = used_mo.get(d["type"], set())
        L.append(row(f"`{d['type']}`", [d.get("metaobjectsCount", 0), f"{len(files)} file(s)" if files else "via references only or unused"], dec))

    L += ["", "## Templates", "", "| Template | Records using it | Sections | Signal | Decision | Reason |", "| --- | --- | --- | --- | --- | --- |"]
    suffix_counts = collections.Counter()
    for kind, items in (("product", owners_data["PRODUCT"]), ("collection", owners_data["COLLECTION"]), ("page", owners_data["PAGE"]), ("article", owners_data["ARTICLE"])):
        for it in items:
            suffix_counts[f"{kind}.{it.get('templateSuffix')}" if it.get("templateSuffix") else kind] += 1
    hardcoded = {}
    for f, data in sorted(jsons.items()):
        if not f.startswith("templates/"):
            continue
        name = os.path.basename(f)[:-5]
        kind = name.split(".")[0]
        sections = data.get("sections", {}) if isinstance(data, dict) else {}
        texts = 0
        for s in sections.values():
            for v in list((s.get("settings") or {}).values()) + [bv for b in (s.get("blocks") or {}).values() for bv in (b.get("settings") or {}).values()]:
                if isinstance(v, str) and len(v) > 40 and not v.startswith(("shopify://", "http", "#")):
                    texts += 1
        hardcoded[name] = texts
        records = suffix_counts.get(name, 0) if kind in ("product", "collection", "page", "article") else "n/a"
        signal = ""
        if records == 0:
            signal = "no records use it"
        elif texts > 5 and kind in ("product", "collection", "page"):
            signal = f"{texts} hard-coded text settings: content may belong in data"
        L.append(row(f"`{name}`", [records, len(sections), signal or "in use"], dec))

    embeds = []
    sd = jsons.get("config/settings_data.json", {})
    for bid, b in ((sd.get("current") or {}).get("blocks") or {}).items():
        if isinstance(b, dict) and str(b.get("type", "")).startswith("shopify://apps/"):
            parts = b["type"].split("/")
            embeds.append((parts[3] if len(parts) > 3 else b["type"], parts[5] if len(parts) > 5 else "", not b.get("disabled", False)))
    app_blocks = collections.defaultdict(set)
    for f, data in jsons.items():
        for m in re.finditer(r"shopify://apps/([^/\"]+)/blocks/([^/\"]+)", json.dumps(data)):
            if f != "config/settings_data.json":
                app_blocks[m.group(1)].add(f"{f} ({m.group(2)})")
    scripts = collections.defaultdict(set)
    for f, text in liquid.items():
        for src in SCRIPT_SRC.findall(text):
            if "asset_url" in src or src.startswith("{{"):
                continue
            host = urlparse(src if src.startswith("http") else "https:" + src if src.startswith("//") else "https://x/" + src).netloc
            scripts[host].add(f)
    referenced = set()
    for text in liquid.values():
        referenced |= set(RENDER.findall(text))
    for data in jsons.values():
        blob = json.dumps(data)
        referenced |= set(re.findall(r'"type":\s*"([a-z0-9_\-]+)"', blob))
    orphans = sorted(f for f in liquid if f.startswith(("snippets/", "sections/")) and os.path.basename(f)[:-7] not in referenced)
    app_orphans = [f for f in orphans if app_name(f) or app_name(liquid[f][:2000])]

    L += ["", "## Apps and scripts", "", "Installed apps can't be listed through the API. Cross-check this against the client's Settings → Apps screenshot.", "",
          "### App embeds (per theme: each kept one must be switched on in the new theme)", "",
          "| App | Embed | Enabled | Decision | Reason |", "| --- | --- | --- | --- | --- |"]
    for app, block, on in sorted(embeds):
        L.append(row(f"`{app}`", [block, "yes" if on else "no, switched off"], dec))
    L += ["", "### App blocks placed in templates and sections", "", "| App | Where | Decision | Reason |", "| --- | --- | --- | --- |"]
    for app, where in sorted(app_blocks.items()):
        L.append(row(f"`{app}`", ["; ".join(sorted(where))[:300]], dec))
    L += ["", "### Hard-coded scripts", "", "| Domain | App | Files | Native alternative | Decision | Reason |", "| --- | --- | --- | --- | --- | --- |"]
    for host, files in sorted(scripts.items()):
        name = app_name(host) or ""
        L.append(row(f"`{host}`", [name, ", ".join(sorted(files))[:200], NATIVE_HINTS.get(name, "")], dec))
    if a.requests and os.path.exists(a.requests):
        reqs = json.load(open(a.requests))
        L += ["", "### What actually loads (recorded)", "", "| Domain | App | Requests | KB | Pages | Decision | Reason |", "| --- | --- | --- | --- | --- | --- | --- |"]
        for host, info in sorted(reqs.items(), key=lambda kv: -kv[1]["bytes"]):
            name = app_name(host) or ""
            L.append(row(f"`{host}`", [name, info["count"], round(info["bytes"] / 1024), ", ".join(info["pages"])], dec))
    L += ["", "### Likely leftover code", "", "Snippets and sections nothing renders. Ones that name an app are usually left behind after it was uninstalled.", "",
          "| File | Looks like | Decision | Reason |", "| --- | --- | --- | --- |"]
    for f in orphans:
        L.append(row(f"`{f}`", [app_name(f) or app_name(liquid[f][:2000]) or ""], dec))

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    open(a.out, "w", encoding="utf-8").write("\n".join(L) + "\n")
    write_app_plan(a.app_plan, embeds, app_blocks, scripts, dec)
    print(f"Wrote {a.out}: {len(keys)} metafield keys, {len(hardcoded)} templates, {len(embeds)} app embeds, "
          f"{len(app_blocks)} apps with blocks, {len(scripts)} script domains, {len(orphans)} unreferenced files ({len(app_orphans)} app-related)")


if __name__ == "__main__":
    main()
