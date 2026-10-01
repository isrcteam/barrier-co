#!/usr/bin/env python3
"""Build docs/data/existing-inventory.md from an export in docs/data/raw/<timestamp>/.

Usage: python3 tools/shopify/inventory.py [docs/data/raw/<timestamp>] [--out docs/data/existing-inventory.md]
Keeps the Decision and Reason columns from an existing inventory file, so re-running after a new
export doesn't wipe decisions already made.
"""
import argparse, collections, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shopify_client import ShopifyError, die, docs_path, latest_run, standard_match

METAFIELD_SECTIONS = ("Metafields", "Values with no definition")

def load(run, name, default=None):
    p = os.path.join(run, f"{name}.json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else default

def esc(v):
    return str(v).replace("|", "\\|")

def split_row(line):
    return [c.strip() for c in re.split(r"(?<!\\)\|", line.strip().strip("|"))]

def existing_decisions(path):
    """Decisions keyed by the row's key cell, plus the owner cell in the metafield sections so the same
    key on Product and Variant keep separate decisions."""
    keep, section = {}, ""
    if not os.path.exists(path):
        return keep
    for line in open(path, encoding="utf-8"):
        if line.startswith("#"):
            section = line.strip("# \n")
            continue
        if not line.startswith("| `"):
            continue
        cells = split_row(line)
        if len(cells) < 3:
            continue
        key = (cells[0], cells[1]) if section in METAFIELD_SECTIONS else cells[0]
        keep[key] = (cells[-2], cells[-1])
    return keep

def row(key, cells, decisions, owner=None):
    d, r = decisions.get((key, esc(owner)) if owner is not None else key, ("", ""))
    return "| " + " | ".join([key] + [esc(c) for c in cells] + [d, r]) + " |"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run", nargs="?")
    ap.add_argument("--out", default=docs_path("data", "existing-inventory.md"))
    a = ap.parse_args()
    try:
        run = a.run or latest_run()
    except ShopifyError as e:
        die(str(e))
    summary = load(run, "summary", {})
    decisions = existing_decisions(a.out)

    products = load(run, "products", [])
    variants = load(run, "variants", [])
    collections_ = load(run, "collections", [])
    pages = load(run, "pages", [])
    articles = load(run, "articles", [])
    mf_defs = load(run, "metafield_definitions", [])
    mo_defs = load(run, "metaobject_definitions", [])
    menus = load(run, "menus", [])
    redirects = load(run, "redirects", [])
    files = load(run, "files", [])

    owners = {"PRODUCT": products, "PRODUCTVARIANT": variants, "COLLECTION": collections_, "PAGE": pages, "ARTICLE": articles}
    usage = collections.Counter()
    totals = {k: len(v) for k, v in owners.items()}
    seen_keys = set()
    for owner, items in owners.items():
        for it in items:
            mfs = it.get("metafields") or {}
            nodes = mfs.get("nodes", mfs) if isinstance(mfs, dict) else mfs
            for m in nodes or []:
                if m.get("value") not in (None, "", "[]"):
                    usage[(owner, f"{m['namespace']}.{m['key']}")] += 1
                    seen_keys.add((owner, f"{m['namespace']}.{m['key']}", m.get("type")))

    L = [f"# Existing store inventory", "",
         f"Source: `{run}` from {summary.get('shop','?')}, exported {summary.get('exported_at','?')}. Rebuilt by `inventory.py`; Decision and Reason columns are kept between runs.", "",
         "Decisions: reuse as is · reuse and rename · retire · replace with new", "", "## Counts", "",
         "| Entity | Count |", "| --- | --- |"]
    for k, v in (summary.get("counts") or {}).items():
        L.append(f"| {k} | {v} |")

    def templates(items, label):
        c = collections.Counter(i.get("templateSuffix") or "default" for i in items)
        out = [f"### {label}", "", "| Template | Records | Decision | Reason |", "| --- | --- | --- | --- |"]
        for t, n in c.most_common():
            out.append(row(f"`{label.lower()}.{t}`", [n], decisions))
        return out + [""]
    L += ["", "## Templates in use", ""]
    L += templates(products, "Product") + templates(collections_, "Collection") + templates(pages, "Page") + templates(articles, "Article")

    L += ["## Metafields", "", "Standard: a Shopify standard definition or category metafield that probably means the same thing as this custom key. Reuse it unless the plan says why not.", "",
          "| Key | Owner | Type | Name | Filled | Standard | Decision | Reason |", "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    defined = set()
    std_hits = 0
    for d in sorted(mf_defs, key=lambda d: (d["ownerType"], d["namespace"], d["key"])):
        key = f"{d['namespace']}.{d['key']}"
        defined.add((d["ownerType"], key))
        n = usage.get((d["ownerType"], key), 0)
        total = totals.get(d["ownerType"])
        filled = f"{n}/{total}" if total else str(n)
        std = standard_match(d["ownerType"], key) or ""
        std_hits += bool(std)
        L.append(row(f"`{key}`", [d["ownerType"].lower(), d["type"]["name"], d["name"], filled, std], decisions, owner=d["ownerType"].lower()))
    undefined = sorted(k for k in seen_keys if (k[0], k[1]) not in defined)
    if undefined:
        L += ["", "### Values with no definition", "", "Metafields holding values but with no definition (often app-created or legacy).", "",
              "| Key | Owner | Type | Filled | Standard | Decision | Reason |", "| --- | --- | --- | --- | --- | --- | --- |"]
        for owner, key, typ in undefined:
            std = standard_match(owner, key) or ""
            std_hits += bool(std)
            L.append(row(f"`{key}`", [owner.lower(), typ, f"{usage[(owner, key)]}/{totals.get(owner, '?')}", std], decisions, owner=owner.lower()))

    L += ["", "## Metaobjects", "", "| Type | Name | Fields | Entries | Decision | Reason |", "| --- | --- | --- | --- | --- | --- |"]
    for d in sorted(mo_defs, key=lambda d: -d.get("metaobjectsCount", 0)):
        fields = ", ".join(f["key"] for f in d.get("fieldDefinitions", []))
        L.append(row(f"`{d['type']}`", [d["name"], fields, d.get("metaobjectsCount", 0)], decisions))

    L += ["", "## Menus", "", "| Menu | Title | Top-level items | Decision | Reason |", "| --- | --- | --- | --- | --- |"]
    for m in menus:
        L.append(row(f"`{m['handle']}`", [m["title"], len(m.get("items", []))], decisions))

    L += ["", "## Redirects and files", "", f"- Redirects in place: {len(redirects)}",
          f"- Files: {len(files)} ({sum(1 for f in files if f.get('image'))} images)", ""]
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    open(a.out, "w", encoding="utf-8").write("\n".join(L) + "\n")
    print(f"Wrote {a.out} from {run}" + (f". {std_hits} custom key(s) match a Shopify standard definition: see the Standard column." if std_hits else ""))

if __name__ == "__main__":
    main()
