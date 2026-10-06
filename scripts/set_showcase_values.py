#!/usr/bin/env python3
"""Fill the product metafields in docs/data/showcase-values.json (subtitle, cloth count, best for,
comparison points) that the comparison tables read.

Dry run by default: reads each product's current values (read only) and lists what would change.
  python3 scripts/set_showcase_values.py --store store            # dry run
  python3 scripts/set_showcase_values.py --store store --apply    # fill the empty ones

Only empty metafields are filled. A value that differs from the file is reported and left alone
unless --overwrite is passed. Before any write, the current values of every listed metafield are
saved to docs/data/backups/showcase-values-<time>.json.
"""
import argparse, datetime, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools", "shopify"))
from shopify_client import Store  # noqa: E402

VALUES = os.path.join(ROOT, "docs", "data", "showcase-values.json")
BACKUPS = os.path.join(ROOT, "docs", "data", "backups")
SCOPES = ["read_products", "write_products"]

PRODUCT = """query($handle: String!) { productByHandle(handle: $handle) { id handle
  metafields(first: 100) { nodes { namespace key type value } } } }"""
SET = """mutation($m: [MetafieldsSetInput!]!) { metafieldsSet(metafields: $m) {
  metafields { namespace key } userErrors { field message code } } }"""


def same(kind, a, b):
    if kind.startswith("list."):
        try:
            return json.loads(a) == json.loads(b)
        except (TypeError, ValueError):
            return False
    return (a or "").strip() == (b or "").strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", default="store")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--overwrite", action="store_true", help="replace values that differ from the file")
    a = ap.parse_args()

    store = Store(a.store)
    store.ensure_token(SCOPES)
    store.ensure_scopes(SCOPES)
    print(f"{store.shop}: {'APPLY' if a.apply else 'dry run (nothing is written)'}\n")

    spec = json.load(open(VALUES, encoding="utf-8"))
    backup, writes = {}, []
    for handle, fields in spec.items():
        product = store.gql(PRODUCT, {"handle": handle})["productByHandle"]
        if not product:
            print(f"  missing   product {handle}")
            continue
        current = {f"{m['namespace']}.{m['key']}": m for m in product["metafields"]["nodes"]}
        backup[handle] = {"id": product["id"], "metafields": {k: current.get(k) for k in fields}}
        for full_key, (kind, value) in fields.items():
            namespace, key = full_key.split(".", 1)
            have = current.get(full_key)
            if have and same(kind, have["value"], value):
                print(f"  same      {handle} {full_key}")
                continue
            if have and not a.overwrite:
                print(f"  differs   {handle} {full_key}: store has {have['value']!r}; left alone (use --overwrite)")
                continue
            print(f"  {'replace' if have else 'set':<9} {handle} {full_key} = {value}")
            writes.append({"ownerId": product["id"], "namespace": namespace, "key": key, "type": kind, "value": value})

    if not writes:
        print("\nNothing to write.")
        return
    if not a.apply:
        print(f"\nDry run only: {len(writes)} metafield(s) would be written. Re-run with --apply.")
        return

    os.makedirs(BACKUPS, exist_ok=True)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = os.path.join(BACKUPS, f"showcase-values-{stamp}.json")
    json.dump(backup, open(path, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"\nBackup: {os.path.relpath(path, ROOT)}")

    result = store.gql(SET, {"m": writes}, idempotent=False)["metafieldsSet"]
    if result["userErrors"]:
        for e in result["userErrors"]:
            print(f"  error     {e['field']}: {e['message']}")
        sys.exit(1)
    print(f"Wrote {len(result['metafields'])} metafield(s).")


if __name__ == "__main__":
    main()
