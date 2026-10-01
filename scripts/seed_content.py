#!/usr/bin/env python3
"""Seed the store with the products, files and metaobject entries in docs/data/seed.json.

Dry run by default: looks everything up (read only) and prints each mutation it would send.
  python3 scripts/seed_content.py --store store            # dry run
  python3 scripts/seed_content.py --store store --apply    # create what's missing

Create only. Files are looked up by filename, metaobjects by type and handle, products by handle;
anything that exists is skipped and never changed. The one exception is a product this script
created on an earlier run (listed in docs/data/seed-result.json): its missing media and empty
metafields are filled in, nothing is overwritten.

Products are created ACTIVE with no publications. After each product the script checks every
sales channel; if a product turns out to be published anywhere it is unpublished at once and
reported. Created IDs are written to docs/data/seed-result.json.
"""
import argparse, json, mimetypes, os, sys, time, urllib.request, uuid

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools", "shopify"))
from shopify_client import Store, ShopifyError  # noqa: E402

SEED = os.path.join(ROOT, "docs", "data", "seed.json")
RESULT = os.path.join(ROOT, "docs", "data", "seed-result.json")
SCOPES = ["read_products", "write_products", "read_files", "write_files", "read_metaobjects",
          "write_metaobjects", "read_publications"]

FILE_BY_NAME = """query($q: String!) { files(first: 5, query: $q) { nodes { id fileStatus alt
  ... on MediaImage { image { url } } } } }"""
FILE_STATUS = """query($id: ID!) { node(id: $id) { ... on MediaImage { id fileStatus fileErrors { message } } } }"""
STAGED = """mutation($input: [StagedUploadInput!]!) { stagedUploadsCreate(input: $input) {
  stagedTargets { url resourceUrl parameters { name value } } userErrors { field message } } }"""
FILE_CREATE = """mutation($files: [FileCreateInput!]!) { fileCreate(files: $files) {
  files { id fileStatus } userErrors { field message code } } }"""
FILE_ATTACH = """mutation($files: [FileUpdateInput!]!) { fileUpdate(files: $files) {
  files { id } userErrors { field message code } } }"""
MO_BY_HANDLE = """query($h: MetaobjectHandleInput!) { metaobjectByHandle(handle: $h) { id handle
  capabilities { publishable { status } } } }"""
MO_CREATE = """mutation($m: MetaobjectCreateInput!) { metaobjectCreate(metaobject: $m) {
  metaobject { id handle capabilities { publishable { status } } } userErrors { field message code } } }"""
PRODUCT_BY_HANDLE = """query($h: String!) { productByIdentifier(identifier: { handle: $h }) { id handle status
  media(first: 50) { nodes { id } } variants(first: 1) { nodes { id price } }
  metafields(first: 50, namespace: "custom") { nodes { key } } } }"""
PRODUCT_CREATE = """mutation($p: ProductCreateInput!) { productCreate(product: $p) {
  product { id handle status variants(first: 1) { nodes { id price } } } userErrors { field message } } }"""
VARIANT_UPDATE = """mutation($pid: ID!, $v: [ProductVariantsBulkInput!]!) { productVariantsBulkUpdate(productId: $pid, variants: $v) {
  productVariants { id price } userErrors { field message } } }"""
METAFIELDS_SET = """mutation($m: [MetafieldsSetInput!]!) { metafieldsSet(metafields: $m) {
  metafields { key } userErrors { field message code } } }"""
PUBLICATIONS = """{ publications(first: 50) { nodes { id name } } }"""
PUB_CHECK = """query($id: ID!) { product(id: $id) { id status resourcePublicationsCount { count }
  resourcePublicationsV2(first: 50, onlyPublished: true) { nodes { isPublished publication { id name } } } } }"""
PUB_ON = """query($id: ID!, $pub: ID!) { product(id: $id) { publishedOnPublication(publicationId: $pub) } }"""
UNPUBLISH = """mutation($id: ID!, $input: [PublicationInput!]!) { publishableUnpublish(id: $id, input: $input) {
  userErrors { field message } } }"""


def load_result():
    if os.path.exists(RESULT):
        return json.load(open(RESULT, encoding="utf-8"))
    return {"files": {}, "metaobjects": {}, "products": {}, "publication_checks": {}}


def save_result(res):
    res["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with open(RESULT, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2, ensure_ascii=False)
        f.write("\n")


def rich_text(paragraphs):
    return json.dumps({"type": "root", "children": [
        {"type": "paragraph", "children": [{"type": "text", "value": p}]} for p in paragraphs]}, ensure_ascii=False)


def show(label, query, variables):
    name = query.split("{", 2)[1].split("(")[0].strip()
    print(f"    would run {name}  {label}")
    print("      " + json.dumps(variables, ensure_ascii=False)[:1500])


class Seeder:
    def __init__(self, store, spec, apply):
        self.s, self.spec, self.apply = store, spec, apply
        self.res = load_result()
        self.file_ids = {}
        self.mo_ids = {}

    # --- files ---------------------------------------------------------------------------------
    def find_file(self, filename):
        stem = os.path.splitext(filename)[0]
        for n in self.s.gql(FILE_BY_NAME, {"q": f"filename:{stem}"})["files"]["nodes"]:
            url = ((n.get("image") or {}).get("url") or "").split("?")[0]
            if os.path.basename(url) == filename:
                return n["id"]
        return None

    def upload(self, f):
        path = os.path.join(ROOT, f["path"])
        filename = os.path.basename(path)
        mime = mimetypes.guess_type(filename)[0] or "image/jpeg"
        size = os.path.getsize(path)
        r = self.s.gql(STAGED, {"input": [{"resource": "IMAGE", "filename": filename, "mimeType": mime,
                                           "httpMethod": "POST", "fileSize": str(size)}]}, idempotent=False)["stagedUploadsCreate"]
        if r["userErrors"]:
            raise ShopifyError(f"stagedUploadsCreate {filename}: {r['userErrors']}")
        t = r["stagedTargets"][0]
        boundary = uuid.uuid4().hex
        body = b""
        for p in t["parameters"]:
            body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"{p['name']}\"\r\n\r\n{p['value']}\r\n".encode()
        body += (f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{filename}\"\r\n"
                 f"Content-Type: {mime}\r\n\r\n").encode() + open(path, "rb").read() + f"\r\n--{boundary}--\r\n".encode()
        req = urllib.request.Request(t["url"], data=body, method="POST",
                                     headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
        with urllib.request.urlopen(req, timeout=300) as resp:
            if resp.status not in (200, 201, 204):
                raise ShopifyError(f"upload of {filename} failed: HTTP {resp.status}")
        r = self.s.gql(FILE_CREATE, {"files": [{"originalSource": t["resourceUrl"], "contentType": "IMAGE",
                                                "alt": f["alt"], "filename": filename,
                                                "duplicateResolutionMode": "RAISE_ERROR"}]}, idempotent=False)["fileCreate"]
        if r["userErrors"]:
            raise ShopifyError(f"fileCreate {filename}: {r['userErrors']}")
        fid = r["files"][0]["id"]
        for _ in range(60):
            n = self.s.gql(FILE_STATUS, {"id": fid})["node"] or {}
            if n.get("fileStatus") == "READY":
                break
            if n.get("fileStatus") == "FAILED":
                raise ShopifyError(f"{filename} failed processing: {n.get('fileErrors')}")
            time.sleep(2)
        return fid

    def files(self):
        print("\nFiles")
        for key, ex in self.spec.get("existing_files", {}).items():
            n = self.s.gql(FILE_STATUS, {"id": ex["id"]})["node"]
            if not n:
                sys.exit(f"  existing file {key} ({ex['id']}) isn't in the store")
            self.file_ids[key] = ex["id"]
            print(f"  reuse   {key} -> {ex['id']}")
        for f in self.spec["files"]:
            filename = os.path.basename(f["path"])
            known = self.res["files"].get(f["key"], {}).get("id")
            fid = known or self.find_file(filename)
            if fid:
                self.file_ids[f["key"]] = fid
                print(f"  exists  {filename} -> {fid}")
                continue
            print(f"  create  {filename}  (alt: {f['alt']})")
            if not self.apply:
                show(filename, STAGED, {"input": [{"resource": "IMAGE", "filename": filename, "httpMethod": "POST"}]})
                show(filename, FILE_CREATE, {"files": [{"originalSource": "<staged resourceUrl>", "contentType": "IMAGE",
                                                        "alt": f["alt"], "filename": filename}]})
                self.file_ids[f["key"]] = f"<new file {filename}>"
                continue
            fid = self.upload(f)
            self.file_ids[f["key"]] = fid
            self.res["files"][f["key"]] = {"id": fid, "filename": filename}
            save_result(self.res)
            print(f"    created {fid}")

    # --- metaobjects ---------------------------------------------------------------------------
    def field_value(self, v):
        if isinstance(v, str):
            return v
        if isinstance(v, (int, float)):
            return str(v)
        if isinstance(v, list):
            return json.dumps(v, ensure_ascii=False)
        if "rich_text" in v:
            return rich_text(v["rich_text"])
        if "file" in v:
            return self.file_ids[v["file"]]
        if "existing_file" in v:
            return self.file_ids[v["existing_file"]]
        if "metaobject" in v:
            return self.mo_ids[v["metaobject"]]
        if "metaobjects" in v:
            return json.dumps([self.mo_ids[k] for k in v["metaobjects"]])
        if "rating" in v:
            return json.dumps({"value": str(v["rating"]), "scale_min": f"{v['scale_min']}.0", "scale_max": f"{v['scale_max']}.0"})
        raise ValueError(f"Unknown value shape: {v}")

    def metaobjects(self):
        print("\nMetaobjects")
        for m in self.spec["metaobjects"]:
            ref = f"{m['type']}/{m['handle']}"
            found = self.s.gql(MO_BY_HANDLE, {"h": {"type": m["type"], "handle": m["handle"]}})["metaobjectByHandle"]
            if found:
                self.mo_ids[ref] = found["id"]
                print(f"  exists  {ref} -> {found['id']} ({found['capabilities']['publishable']['status']})")
                continue
            data = {"type": m["type"], "handle": m["handle"],
                    "capabilities": {"publishable": {"status": m["status"]}},
                    "fields": [{"key": k, "value": self.field_value(v)} for k, v in m["fields"].items()]}
            print(f"  create  {ref} [{m['status']}] source={m['source']}")
            if not self.apply:
                show(ref, MO_CREATE, {"m": data})
                self.mo_ids[ref] = f"<new {ref}>"
                continue
            r = self.s.gql(MO_CREATE, {"m": data}, idempotent=False)["metaobjectCreate"]
            if r["userErrors"]:
                sys.exit(f"    failed: {r['userErrors']}")
            mo = r["metaobject"]
            self.mo_ids[ref] = mo["id"]
            self.res["metaobjects"][ref] = {"id": mo["id"], "status": mo["capabilities"]["publishable"]["status"], "source": m["source"]}
            save_result(self.res)
            print(f"    created {mo['id']} ({mo['capabilities']['publishable']['status']})")

    # --- products ------------------------------------------------------------------------------
    def metafield_inputs(self, p, skip=()):
        defs = {d["key"]: d["type"] for d in json.load(open(os.path.join(ROOT, "docs", "data", "definitions.json")))["metafields"]}
        out = []
        for k, v in p["metafields"].items():
            if k in skip:
                continue
            t = defs[k]
            if t.startswith("list.metaobject_reference"):
                t = "list.metaobject_reference"
            out.append({"namespace": "custom", "key": k, "type": t, "value": self.field_value(v)})
        return out

    def check_channels(self, pid, handle):
        pubs = self.s.gql(PUBLICATIONS)["publications"]["nodes"]
        d = self.s.gql(PUB_CHECK, {"id": pid})["product"]
        published = {n["publication"]["id"]: n["publication"]["name"] for n in d["resourcePublicationsV2"]["nodes"] if n["isPublished"]}
        for pub in pubs:
            if self.s.gql(PUB_ON, {"id": pid, "pub": pub["id"]})["product"]["publishedOnPublication"]:
                published[pub["id"]] = pub["name"]
        count = d["resourcePublicationsCount"]["count"]
        check = {"checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "status": d["status"],
                 "channels_checked": [p["name"] for p in pubs], "published_on": sorted(published.values()),
                 "resourcePublicationsCount": count}
        if published or count:
            print(f"  WARNING {handle} is published on {sorted(published.values()) or count}; unpublishing now")
            r = self.s.gql(UNPUBLISH, {"id": pid, "input": [{"publicationId": i} for i in published]}, idempotent=False)
            check["unpublished"] = sorted(published.values())
            check["unpublish_errors"] = r["publishableUnpublish"]["userErrors"]
            d = self.s.gql(PUB_CHECK, {"id": pid})["product"]
            check["after_unpublish_count"] = d["resourcePublicationsCount"]["count"]
        print(f"  channels {handle}: published on {len(published)} of {len(pubs)} ({', '.join(p['name'] for p in pubs)}); "
              f"resourcePublicationsCount={count}")
        self.res["publication_checks"][handle] = check
        save_result(self.res)

    def attach_media(self, pid, keys, existing_count):
        for key in keys[existing_count:]:
            fid = self.file_ids[key]
            r = self.s.gql(FILE_ATTACH, {"files": [{"id": fid, "referencesToAdd": [pid]}]}, idempotent=False)["fileUpdate"]
            if r["userErrors"]:
                sys.exit(f"    attaching {key} failed: {r['userErrors']}")
            print(f"    attached {key}")

    def products(self):
        print("\nProducts")
        for p in self.spec["products"]:
            h = p["handle"]
            found = self.s.gql(PRODUCT_BY_HANDLE, {"h": h})["productByIdentifier"]
            ours = h in self.res["products"]
            if found and not ours:
                print(f"  exists  {h} -> {found['id']} (not created by this script, left alone)")
                continue
            if found and ours:
                pid = found["id"]
                print(f"  exists  {h} -> {pid} (created by this script; filling gaps only)")
                have = {n["key"] for n in found["metafields"]["nodes"]}
                missing = self.metafield_inputs(p, skip=have)
                n_media = len(found["media"]["nodes"])
                if not self.apply:
                    if missing:
                        show(h, METAFIELDS_SET, {"m": [dict(m, ownerId=pid) for m in missing]})
                    for k in p["media"][n_media:]:
                        show(k, FILE_ATTACH, {"files": [{"id": self.file_ids[k], "referencesToAdd": [pid]}]})
                    continue
                v = found["variants"]["nodes"][0]
                if float(v["price"]) == 0:
                    r = self.s.gql(VARIANT_UPDATE, {"pid": pid, "v": [{"id": v["id"], "price": p["price"],
                                                                        "inventoryItem": {"tracked": False}}]}, idempotent=False)["productVariantsBulkUpdate"]
                    if r["userErrors"]:
                        sys.exit(f"    price update failed: {r['userErrors']}")
                if missing:
                    r = self.s.gql(METAFIELDS_SET, {"m": [dict(m, ownerId=pid) for m in missing]}, idempotent=False)["metafieldsSet"]
                    if r["userErrors"]:
                        sys.exit(f"    metafieldsSet failed: {r['userErrors']}")
                self.attach_media(pid, p["media"], n_media)
                self.check_channels(pid, h)
                continue

            data = {"title": p["title"], "handle": h, "descriptionHtml": p["description_html"], "vendor": p["vendor"],
                    "productType": p["product_type"], "status": p["status"], "metafields": self.metafield_inputs(p)}
            print(f"  create  {h} [{p['status']}, no publications] price {p['price']}, {len(p['media'])} images, "
                  f"{len(data['metafields'])} metafields")
            if not self.apply:
                show(h, PRODUCT_CREATE, {"p": data})
                show(h, VARIANT_UPDATE, {"pid": "<new product>", "v": [{"id": "<default variant>", "price": p["price"],
                                                                         "inventoryItem": {"tracked": False}}]})
                for k in p["media"]:
                    show(k, FILE_ATTACH, {"files": [{"id": self.file_ids[k], "referencesToAdd": ["<new product>"]}]})
                print(f"    then check {h} is on 0 sales channels")
                continue
            r = self.s.gql(PRODUCT_CREATE, {"p": data}, idempotent=False)["productCreate"]
            if r["userErrors"]:
                sys.exit(f"    productCreate failed: {r['userErrors']}")
            prod = r["product"]
            pid = prod["id"]
            self.res["products"][h] = {"id": pid, "status": prod["status"]}
            save_result(self.res)
            print(f"    created {pid} ({prod['status']})")
            vid = prod["variants"]["nodes"][0]["id"]
            r = self.s.gql(VARIANT_UPDATE, {"pid": pid, "v": [{"id": vid, "price": p["price"],
                                                                "inventoryItem": {"tracked": False}}]}, idempotent=False)["productVariantsBulkUpdate"]
            if r["userErrors"]:
                sys.exit(f"    price update failed: {r['userErrors']}")
            self.res["products"][h].update({"variant_id": vid, "price": r["productVariants"][0]["price"]})
            save_result(self.res)
            print(f"    price {r['productVariants'][0]['price']}")
            self.attach_media(pid, p["media"], 0)
            self.check_channels(pid, h)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", default="store")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    spec = json.load(open(SEED, encoding="utf-8"))
    store = Store(a.store)
    store.ensure_token(SCOPES)
    store.ensure_scopes(SCOPES)
    print(f"{store.shop}: {'APPLY' if a.apply else 'dry run (nothing is written)'}")
    seeder = Seeder(store, spec, a.apply)
    seeder.files()
    seeder.metaobjects()
    seeder.products()
    for s in spec.get("skipped", []):
        print(f"\nSkipped {s['type']}: {s['reason']}")
    if a.apply:
        save_result(seeder.res)
        print(f"\nIDs written to {os.path.relpath(RESULT, ROOT)}")


if __name__ == "__main__":
    main()
