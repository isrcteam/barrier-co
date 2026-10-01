#!/usr/bin/env python3
"""Create the metaobject and metafield definitions in docs/data/definitions.json.

Dry run by default: prints what would be created and what already exists. Only creates, never
updates or deletes, so an existing definition is left exactly as it is.
  python3 scripts/create_definitions.py --store store            # dry run
  python3 scripts/create_definitions.py --store store --apply    # create the missing ones
"""
import argparse, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools", "shopify"))
from shopify_client import Store  # noqa: E402

SPEC = os.path.join(ROOT, "docs", "data", "definitions.json")
SCOPES = ["read_metaobject_definitions", "write_metaobject_definitions", "read_products", "write_products"]

EXISTING_TYPES = """{ metaobjectDefinitions(first: 100) { nodes { id type } } }"""
EXISTING_FIELDS = """query($owner: MetafieldOwnerType!) {
  metafieldDefinitions(first: 250, ownerType: $owner) { nodes { id namespace key } } }"""
CREATE_TYPE = """mutation($d: MetaobjectDefinitionCreateInput!) {
  metaobjectDefinitionCreate(definition: $d) { metaobjectDefinition { id type } userErrors { field message code } } }"""
CREATE_FIELD = """mutation($d: MetafieldDefinitionInput!) {
  metafieldDefinitionCreate(definition: $d) { createdDefinition { id namespace key } userErrors { field message code } } }"""


def validations(f, type_ids):
    v = []
    if f.get("file_types"):
        v.append({"name": "file_type_options", "value": json.dumps(f["file_types"])})
    if f.get("scale"):
        v += [{"name": "scale_min", "value": f"{f['scale'][0]}.0"}, {"name": "scale_max", "value": f"{f['scale'][1]}.0"}]
    if f.get("metaobject"):
        v.append({"name": "metaobject_definition_id", "value": type_ids[f["metaobject"]]})
    return v


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", default="store")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    spec = json.load(open(SPEC, encoding="utf-8"))
    store = Store(a.store)
    store.ensure_token(SCOPES)
    store.ensure_scopes(SCOPES)

    type_ids = {n["type"]: n["id"] for n in store.gql(EXISTING_TYPES)["metaobjectDefinitions"]["nodes"]}
    print(f"{store.shop}: {'APPLY' if a.apply else 'dry run'}")
    for mo in spec["metaobjects"]:
        if mo["type"] in type_ids:
            print(f"  exists  metaobject {mo['type']}")
            continue
        refs = [f["metaobject"] for f in mo["fields"] if f.get("metaobject")]
        missing = [r for r in refs if r not in type_ids]
        if missing and a.apply:
            sys.exit(f"metaobject {mo['type']} references {missing}, which must be created first (order them earlier in the spec)")
        d = {"type": mo["type"], "name": mo["name"], "displayNameKey": mo["display"],
             "access": {"storefront": "PUBLIC_READ"}, "capabilities": {"publishable": {"enabled": True}},
             "fieldDefinitions": [{"key": f["key"], "name": f["name"], "type": f["type"], "required": bool(f.get("required")),
                                   "validations": validations(f, {**type_ids, **{r: "<new>" for r in missing}})} for f in mo["fields"]]}
        print(f"  create  metaobject {mo['type']} ({len(d['fieldDefinitions'])} fields)")
        if a.apply:
            r = store.gql(CREATE_TYPE, {"d": d}, idempotent=False)["metaobjectDefinitionCreate"]
            if r["userErrors"]:
                sys.exit(f"    failed: {r['userErrors']}")
            type_ids[mo["type"]] = r["metaobjectDefinition"]["id"]
        else:
            type_ids[mo["type"]] = "<new>"

    owners = {f["owner"] for f in spec["metafields"]}
    existing = set()
    for o in owners:
        for n in store.gql(EXISTING_FIELDS, {"owner": o})["metafieldDefinitions"]["nodes"]:
            existing.add((o, n["namespace"], n["key"]))
    for f in spec["metafields"]:
        ident = (f["owner"], f["namespace"], f["key"])
        if ident in existing:
            print(f"  exists  metafield {f['owner'].lower()}.{f['namespace']}.{f['key']}")
            continue
        d = {"ownerType": f["owner"], "namespace": f["namespace"], "key": f["key"], "name": f["name"], "type": f["type"],
             "description": f["description"], "pin": True, "access": {"storefront": "PUBLIC_READ"},
             "validations": validations(f, type_ids)}
        print(f"  create  metafield {f['owner'].lower()}.{f['namespace']}.{f['key']} ({f['type']})")
        if a.apply:
            r = store.gql(CREATE_FIELD, {"d": d}, idempotent=False)["metafieldDefinitionCreate"]
            if r["userErrors"]:
                sys.exit(f"    failed: {r['userErrors']}")
    if not a.apply:
        print("Dry run only. Re-run with --apply to create the missing definitions.")


if __name__ == "__main__":
    main()
