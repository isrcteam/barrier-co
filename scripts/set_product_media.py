#!/usr/bin/env python3
"""Add the Figma-framed product images to a product and move them to the front of its gallery.

Existing media is kept (moved after the new images), never deleted. A file already on the product
(same filename) is not uploaded twice.
  python3 scripts/set_product_media.py --store store --product the-30-the-everyday \
      --image path.jpg "Alt text" --image path2.jpg "Alt text"            # dry run
  ... --apply
"""
import argparse, os, sys, time, urllib.request, uuid

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools", "shopify"))
from shopify_client import Store  # noqa: E402

PRODUCT = """query($q: String!) { products(first: 1, query: $q) { nodes { id handle media(first: 50) { nodes { id ... on MediaImage { image { url } } } } } } }"""
STAGED = """mutation($input: [StagedUploadInput!]!) { stagedUploadsCreate(input: $input) {
  stagedTargets { url resourceUrl parameters { name value } } userErrors { message } } }"""
ADD = """mutation($id: ID!, $media: [CreateMediaInput!]!) { productUpdate(product: {id: $id}, media: $media) {
  product { media(first: 50) { nodes { id status ... on MediaImage { image { url } } } } } userErrors { field message } } }"""
STATUS = """query($id: ID!) { product(id: $id) { media(first: 50) { nodes { id status ... on MediaImage { image { url } } } } } }"""
REORDER = """mutation($id: ID!, $moves: [MoveInput!]!) { productReorderMedia(id: $id, moves: $moves) { job { id } mediaUserErrors { message } } }"""


def stage(store, path):
    name = os.path.basename(path)
    size = os.path.getsize(path)
    r = store.gql(STAGED, {"input": [{"filename": name, "mimeType": "image/jpeg", "resource": "PRODUCT_IMAGE",
                                      "httpMethod": "POST", "fileSize": str(size)}]}, idempotent=False)["stagedUploadsCreate"]
    if r["userErrors"]:
        sys.exit(f"stage {name}: {r['userErrors']}")
    t = r["stagedTargets"][0]
    boundary = uuid.uuid4().hex
    body = b""
    for p in t["parameters"]:
        body += f'--{boundary}\r\nContent-Disposition: form-data; name="{p["name"]}"\r\n\r\n{p["value"]}\r\n'.encode()
    body += f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{name}"\r\nContent-Type: image/jpeg\r\n\r\n'.encode()
    body += open(path, "rb").read() + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(t["url"], data=body, headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    urllib.request.urlopen(req, timeout=120).read()
    return t["resourceUrl"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", default="store")
    ap.add_argument("--product", required=True)
    ap.add_argument("--image", nargs=2, action="append", metavar=("PATH", "ALT"), required=True)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    store = Store(a.store)
    store.ensure_token(["read_products", "write_products"])
    prod = store.gql(PRODUCT, {"q": f"handle:{a.product}"})["products"]["nodes"][0]
    existing = {(m.get("image") or {}).get("url", "").split("/")[-1].split("?")[0]: m["id"] for m in prod["media"]["nodes"]}
    print(f"{prod['handle']}: {len(existing)} existing media kept")
    wanted, to_add = [], []
    for path, alt in a.image:
        name = os.path.basename(path)
        match = next((mid for fname, mid in existing.items() if fname.startswith(os.path.splitext(name)[0])), None)
        if match:
            print(f"  exists  {name}")
            wanted.append(match)
        else:
            print(f"  add     {name}  ({alt})")
            to_add.append((path, alt))
            wanted.append(name)
    print("  order   " + " > ".join(os.path.basename(p) for p, _ in a.image) + " > existing media")
    if not a.apply:
        print("Dry run only. Re-run with --apply.")
        return
    if to_add:
        media = [{"originalSource": stage(store, p), "mediaContentType": "IMAGE", "alt": alt} for p, alt in to_add]
        r = store.gql(ADD, {"id": prod["id"], "media": media}, idempotent=False)["productUpdate"]
        if r["userErrors"]:
            sys.exit(f"add: {r['userErrors']}")
    for _ in range(30):
        nodes = store.gql(STATUS, {"id": prod["id"]})["product"]["media"]["nodes"]
        if all(n["status"] == "READY" for n in nodes):
            break
        time.sleep(2)
    by_name = {(n.get("image") or {}).get("url", "").split("/")[-1].split("?")[0]: n["id"] for n in nodes}
    ids = []
    for w in wanted:
        if w.startswith("gid://"):
            ids.append(w)
        else:
            stem = os.path.splitext(w)[0]
            ids.append(next(mid for fname, mid in by_name.items() if fname.startswith(stem)))
    moves = [{"id": mid, "newPosition": str(i)} for i, mid in enumerate(ids)]
    r = store.gql(REORDER, {"id": prod["id"], "moves": moves}, idempotent=False)["productReorderMedia"]
    if r["mediaUserErrors"]:
        sys.exit(f"reorder: {r['mediaUserErrors']}")
    time.sleep(3)
    final = store.gql(STATUS, {"id": prod["id"]})["product"]["media"]["nodes"]
    for i, n in enumerate(final):
        print(f"  {i}: {(n.get('image') or {}).get('url', '').split('/')[-1].split('?')[0]}  {n['status']}")


if __name__ == "__main__":
    main()
