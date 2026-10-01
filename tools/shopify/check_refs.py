#!/usr/bin/env python3
"""Confirm every shopify://shop_images/ reference in the theme exists in the store's Files.

Usage: python3 tools/shopify/check_refs.py --store <alias> [--theme .]
Reads templates/*.json, sections/*.json and config/settings_data.json. Run it after uploading an asset pack
and before pushing or previewing the theme. Exit 1 if anything is missing or still processing.
"""
import argparse, glob, os, re, sys, urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shopify_client import READ_SCOPES, ShopifyError, Store, die

Q = "query($q: String!) { files(first: 50, query: $q) { nodes { id fileStatus ... on MediaImage { image { url } } ... on GenericFile { url } } } }"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", default="source")
    ap.add_argument("--theme", default=".")
    a = ap.parse_args()
    refs = {}
    files = glob.glob(os.path.join(a.theme, "templates", "*.json")) + glob.glob(os.path.join(a.theme, "sections", "*.json")) + [os.path.join(a.theme, "config", "settings_data.json")]
    for f in files:
        if os.path.exists(f):
            for name in re.findall(r"shopify://shop_images/([^\"'\s]+)", open(f, encoding="utf-8").read()):
                refs.setdefault(urllib.parse.unquote(name), set()).add(os.path.relpath(f, a.theme))
    if not refs:
        print("No shopify://shop_images/ references found.")
        return
    try:
        store = Store(a.store)
        store.ensure_token(READ_SCOPES)
    except ShopifyError as e:
        die(str(e))
    missing, processing = [], []
    for name, where in sorted(refs.items()):
        stem = name.rsplit(".", 1)[0].replace('"', "")
        try:
            nodes = store.gql(Q, {"q": f'filename:"{stem}"'})["files"]["nodes"]
        except ShopifyError as e:
            die(f"Could not query files on {store.shop}: {e}")
        hit = [n for n in nodes if urllib.parse.unquote(os.path.basename(((n.get("image") or {}).get("url") or n.get("url") or "").split("?")[0])) == name]
        if not hit:
            missing.append((name, where))
        elif hit[0]["fileStatus"] != "READY":
            processing.append(name)
    print(f"{len(refs)} referenced files on {store.shop}: {len(refs) - len(missing) - len(processing)} ready, {len(processing)} processing, {len(missing)} missing")
    for name, where in missing:
        print(f"  MISSING {name}  (used in {', '.join(sorted(where))})")
    for name in processing:
        print(f"  PROCESSING {name}")
    if missing:
        print("A missing file usually means it wasn't uploaded, or Shopify renamed it because the name was already taken.")
    sys.exit(1 if missing or processing else 0)

if __name__ == "__main__":
    main()
