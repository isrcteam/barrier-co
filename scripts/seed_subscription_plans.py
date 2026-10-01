#!/usr/bin/env python3
"""Create subscription_plan entries from docs/data/subscription-plans.json and link them to each product's
custom.subscription_plans metafield. Create-only for entries (existing handles are reused); the metafield is set
to the listed order.
  python3 scripts/seed_subscription_plans.py --store store            # dry run
  python3 scripts/seed_subscription_plans.py --store store --apply
"""
import argparse, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools", "shopify"))
from shopify_client import Store  # noqa: E402

FIND = """query($h: MetaobjectHandleInput!) { metaobjectByHandle(handle: $h) { id } }"""
CREATE = """mutation($m: MetaobjectCreateInput!) { metaobjectCreate(metaobject: $m) { metaobject { id handle } userErrors { field message } } }"""
PRODUCT = """query($q: String!) { products(first: 1, query: $q) { nodes { id handle } } }"""
SET = """mutation($m: [MetafieldsSetInput!]!) { metafieldsSet(metafields: $m) { metafields { key } userErrors { field message } } }"""


def field_value(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, list):
        return json.dumps(v, ensure_ascii=False)
    return str(v)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", default="store")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    spec = json.load(open(os.path.join(ROOT, "docs", "data", "subscription-plans.json"), encoding="utf-8"))
    store = Store(a.store)
    store.ensure_token(["read_metaobjects", "write_metaobjects", "read_products", "write_products"])
    for product_handle, entries in spec.items():
        ids = []
        for e in entries:
            found = store.gql(FIND, {"h": {"type": "subscription_plan", "handle": e["handle"]}})["metaobjectByHandle"]
            if found:
                print(f"  exists  subscription_plan/{e['handle']}")
                ids.append(found["id"])
                continue
            fields = [{"key": k, "value": field_value(v)} for k, v in e["fields"].items() if v not in (None, "", [])]
            print(f"  create  subscription_plan/{e['handle']} ({e['fields']['title']})")
            if a.apply:
                r = store.gql(CREATE, {"m": {"type": "subscription_plan", "handle": e["handle"], "fields": fields,
                                             "capabilities": {"publishable": {"status": "ACTIVE"}}}}, idempotent=False)["metaobjectCreate"]
                if r["userErrors"]:
                    sys.exit(f"    failed: {r['userErrors']}")
                ids.append(r["metaobject"]["id"])
        prod = store.gql(PRODUCT, {"q": f"handle:{product_handle}"})["products"]["nodes"]
        if not prod:
            sys.exit(f"product {product_handle} not found")
        print(f"  set     {product_handle}.custom.subscription_plans = {len(entries)} entries")
        if a.apply:
            r = store.gql(SET, {"m": [{"ownerId": prod[0]["id"], "namespace": "custom", "key": "subscription_plans",
                                       "type": "list.metaobject_reference", "value": json.dumps(ids)}]}, idempotent=False)["metafieldsSet"]
            if r["userErrors"]:
                sys.exit(f"    failed: {r['userErrors']}")
    if not a.apply:
        print("Dry run only. Re-run with --apply.")


if __name__ == "__main__":
    main()
