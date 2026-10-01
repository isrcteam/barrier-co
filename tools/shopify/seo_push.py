#!/usr/bin/env python3
"""Push approved SEO titles, descriptions and alt text to the store, with a backup for rollback.

Usage:
  python3 tools/shopify/seo_push.py --store source                         dry run from docs/seo/seo-review.csv
  python3 tools/shopify/seo_push.py --store source --apply                 needs the approval row the dry run prints
  python3 tools/shopify/seo_push.py --store source --rollback docs/data/backups/seo-<time>.json [--apply]
Only rows with Approve = Y and a Recommended value are written. Current values (and metafield types) are
read from the live store, not the export, and saved to the backup file before anything changes.
The approval names a hash of the approved rows, so an edited sheet needs a new approval.
"""
import argparse, csv, hashlib, io, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shopify_client import READ_SCOPES, SEO_WRITE_SCOPES, ShopifyError, Store, die, docs_path, require_approval, utc_stamp

BACKUP_Q = """query($ids: [ID!]!) { nodes(ids: $ids) { id ... on Product { seo { title description } } ... on Collection { seo { title description } }
  ... on Page { t: metafield(namespace: "global", key: "title_tag") { value type } d: metafield(namespace: "global", key: "description_tag") { value type } }
  ... on Article { t: metafield(namespace: "global", key: "title_tag") { value type } d: metafield(namespace: "global", key: "description_tag") { value type } }
  ... on MediaImage { alt } } }"""
PRODUCT = "mutation($p: ProductUpdateInput!) { productUpdate(product: $p) { product { id } userErrors { field message } } }"
COLLECTION = "mutation($c: CollectionInput!) { collectionUpdate(input: $c) { collection { id } userErrors { field message } } }"
MF_SET = "mutation($m: [MetafieldsSetInput!]!) { metafieldsSet(metafields: $m) { metafields { id } userErrors { field message } } }"
MF_DELETE = "mutation($m: [MetafieldIdentifierInput!]!) { metafieldsDelete(metafields: $m) { deletedMetafields { ownerId namespace key } userErrors { field message } } }"
FILES = "mutation($f: [FileUpdateInput!]!) { fileUpdate(files: $f) { files { id } userErrors { field message } } }"
DEFAULT_TYPES = {"title": "single_line_text_field", "description": "multi_line_text_field"}
COLUMNS = ["Type", "Handle", "ID", "Field", "Current", "Issue", "Recommended", "Reason", "Approve"]


def check(node, key):
    errs = node[key]["userErrors"]
    if errs:
        raise ShopifyError("; ".join(e["message"] for e in errs))


def current(store, ids):
    """Live values and, for pages and articles, the existing metafield types."""
    values, types = {}, {}
    for i in range(0, len(ids), 100):
        for n in store.gql(BACKUP_Q, {"ids": ids[i:i + 100]})["nodes"]:
            if not n:
                continue
            if "seo" in n:
                values[n["id"]] = {"title": n["seo"]["title"], "description": n["seo"]["description"]}
            elif "t" in n:
                values[n["id"]] = {"title": (n.get("t") or {}).get("value"), "description": (n.get("d") or {}).get("value")}
                types[n["id"]] = {"title": (n.get("t") or {}).get("type"), "description": (n.get("d") or {}).get("type")}
            elif "alt" in n:
                values[n["id"]] = {"alt": n["alt"]}
    return values, types


def write(store, changes, types):
    grouped = {}
    for gid, field, value in changes:
        grouped.setdefault(gid, {})[field] = value
    sets, deletes, files, done, failed = [], [], [], 0, []
    for gid, fields in grouped.items():
        kind = re.search(r"gid://shopify/(\w+)/", gid).group(1)
        try:
            if kind == "Product":
                check(store.gql(PRODUCT, {"p": {"id": gid, "seo": {k: v or "" for k, v in fields.items() if k in ("title", "description")}}}), "productUpdate")
                done += 1
            elif kind == "Collection":
                check(store.gql(COLLECTION, {"c": {"id": gid, "seo": {k: v or "" for k, v in fields.items() if k in ("title", "description")}}}), "collectionUpdate")
                done += 1
            elif kind in ("Page", "Article"):
                for f, key in (("title", "title_tag"), ("description", "description_tag")):
                    if f not in fields:
                        continue
                    if fields[f] in (None, ""):
                        deletes.append({"ownerId": gid, "namespace": "global", "key": key})
                    else:
                        mtype = (types.get(gid) or {}).get(f) or DEFAULT_TYPES[f]
                        sets.append({"ownerId": gid, "namespace": "global", "key": key, "type": mtype, "value": fields[f]})
            elif "alt" in fields:
                files.append({"id": gid, "alt": fields["alt"] or ""})
        except ShopifyError as e:
            failed.append(f"{gid}: {e}")
    for i in range(0, len(sets), 25):
        batch = sets[i:i + 25]
        try:
            check(store.gql(MF_SET, {"m": batch}), "metafieldsSet")
            done += len(batch)
        except ShopifyError as e:
            failed.append(f"page/article batch {i // 25 + 1}: {e}")
    for i in range(0, len(deletes), 25):
        batch = deletes[i:i + 25]
        try:
            check(store.gql(MF_DELETE, {"m": batch}), "metafieldsDelete")
            done += len(batch)
        except ShopifyError as e:
            failed.append(f"page/article clear batch {i // 25 + 1}: {e}")
    for i in range(0, len(files), 50):
        batch = files[i:i + 50]
        try:
            check(store.gql(FILES, {"f": batch}), "fileUpdate")
            done += len(batch)
        except ShopifyError as e:
            failed.append(f"alt text batch {i // 50 + 1}: {e}")
    return done, failed


def read_sheet(path):
    raw = open(path, "rb").read()
    text = raw.decode("utf-8-sig") if raw[:3] == b"\xef\xbb\xbf" else raw.decode("utf-8", errors="replace")
    try:
        dialect = csv.Sniffer().sniff(text[:4096], delimiters=",;\t")
    except csv.Error:
        dialect = csv.excel
    rows = list(csv.DictReader(io.StringIO(text), dialect=dialect))
    header = list(rows[0].keys()) if rows else []
    missing = [c for c in COLUMNS if c not in header]
    if missing:
        die(f"{path} is missing the column(s) {', '.join(missing)}. Expected: {', '.join(COLUMNS)}. Was it re-saved with different headers?")
    return rows


def approval_hash(changes):
    body = "\n".join(f"{g}\t{f}\t{v}" for g, f, v in sorted(changes))
    return hashlib.sha256(body.encode("utf-8")).hexdigest()[:8]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--store", default="source")
    ap.add_argument("--sheet", default=docs_path("seo", "seo-review.csv"))
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--rollback", help="a backup file written by an earlier push")
    ap.add_argument("--reauth", action="store_true", help="ignore the saved token and get a new one")
    a = ap.parse_args()
    try:
        store = Store(a.store)
    except ShopifyError as e:
        die(str(e))

    if a.rollback:
        backup = json.load(open(a.rollback, encoding="utf-8"))
        if backup.get("shop") != store.shop:
            die(f"Refusing: {a.rollback} was taken from {backup.get('shop')}, not {store.shop}.")
        changes = [(gid, f, v) for gid, vals in backup["values"].items() for f, v in vals.items()]
        backup_types = backup.get("types") or {}
        print(f"Rolling back {len(backup['values'])} record(s) on {store.shop} to the values in {a.rollback}")
        if not a.apply:
            print("Dry run. Add --apply to restore.")
            return
        phrase = None
    else:
        rows = [r for r in read_sheet(a.sheet) if (r.get("Approve") or "").strip().upper() == "Y" and (r.get("Recommended") or "").strip()]
        changes = [(r["ID"].strip(), r["Field"].strip(), r["Recommended"].strip()) for r in rows]
        backup_types = {}
        by_type = {}
        for r in rows:
            k = f"{r['Type']} {r['Field']}"
            by_type[k] = by_type.get(k, 0) + 1
        print(f"{len(changes)} approved change(s) for {store.shop}: " + ", ".join(f"{v} {k}" for k, v in sorted(by_type.items())))
        for r in rows[:5]:
            print(f"  {r['Type']} {r['Handle']} {r['Field']}: {(r.get('Current') or '')[:50]!r} -> {r['Recommended'].strip()[:70]!r}")
        if not changes:
            print("Nothing to push.")
            return
        phrase = f"Approved: seo push {approval_hash(changes)}"
        if not a.apply:
            print("Dry run. Nothing written. To push, add this row to the approval log in docs/plan.md, then rerun with --apply:")
            print(f"  | {phrase} | YYYY-MM-DD | Jeet | |")
            print("The code is a hash of the approved rows: editing the sheet changes it and needs a new approval.")
            return
        require_approval(phrase)

    try:
        store.ensure_token(READ_SCOPES + SEO_WRITE_SCOPES, reauth=a.reauth)
        store.ensure_scopes(SEO_WRITE_SCOPES, READ_SCOPES + SEO_WRITE_SCOPES)
    except ShopifyError as e:
        die(str(e))
    ids = sorted({c[0] for c in changes})
    stamp = utc_stamp()
    prefix = "seo-before-rollback" if a.rollback else "seo"
    backups = docs_path("data", "backups")
    backup_path = os.path.join(backups, f"{prefix}-{stamp}.json")
    n = 1
    while os.path.exists(backup_path):
        backup_path = os.path.join(backups, f"{prefix}-{stamp}-{n}.json")
        n += 1
    os.makedirs(backups, exist_ok=True)
    before, live_types = current(store, ids)
    touched = {}
    for gid, field, _ in changes:
        touched.setdefault(gid, set()).add(field)
    before = {gid: {f: v for f, v in vals.items() if f in touched.get(gid, ())} for gid, vals in before.items()}
    types = {**backup_types, **live_types}
    with open(backup_path, "w", encoding="utf-8") as f:
        json.dump({"shop": store.shop, "taken": stamp, "approval": phrase, "values": before, "types": live_types}, f, indent=1)
    print(f"Backup of current values: {backup_path}")
    done, failed = write(store, changes, types)
    print(f"Updated {done} value(s).")
    if failed:
        print(f"{len(failed)} failed:")
        for f in failed[:20]:
            print(f"  {f}")
        sys.exit(2)
    print("Remove the write scopes from the app now (release a read-only version).")


if __name__ == "__main__":
    main()
