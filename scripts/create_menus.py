#!/usr/bin/env python3
"""Create the theme's navigation menus from docs/data/menus.json. Create-only: an existing handle is skipped.
  python3 scripts/create_menus.py --store store            # dry run
  python3 scripts/create_menus.py --store store --apply
"""
import argparse, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools", "shopify"))
from shopify_client import Store  # noqa: E402

EXISTING = """{ menus(first: 50) { nodes { handle } } }"""
CREATE = """mutation($title: String!, $handle: String!, $items: [MenuItemCreateInput!]!) {
  menuCreate(title: $title, handle: $handle, items: $items) { menu { id handle } userErrors { field message } } }"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", default="store")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    spec = json.load(open(os.path.join(ROOT, "docs", "data", "menus.json"), encoding="utf-8"))
    store = Store(a.store)
    store.ensure_token(["read_online_store_navigation", "write_online_store_navigation"])
    have = {n["handle"] for n in store.gql(EXISTING)["menus"]["nodes"]}
    for m in spec:
        if m["handle"] in have:
            print(f"  exists  {m['handle']}")
            continue
        items = [{"title": i["title"], "type": "HTTP", "url": i["url"]} for i in m["items"]]
        print(f"  create  {m['handle']}: " + ", ".join(i["title"] for i in m["items"]))
        if a.apply:
            r = store.gql(CREATE, {"title": m["title"], "handle": m["handle"], "items": items}, idempotent=False)["menuCreate"]
            if r["userErrors"]:
                sys.exit(f"    failed: {r['userErrors']}")
    if not a.apply:
        print("Dry run only. Re-run with --apply.")


if __name__ == "__main__":
    main()
