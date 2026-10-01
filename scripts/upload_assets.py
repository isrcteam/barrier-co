#!/usr/bin/env python3
"""Upload the theme image pack in docs/assets/dist/ to the store's Files, as listed in docs/assets/manifest.json.

Dry run by default: looks every filename up in Files (read only) and lists what it would upload.
  python3 scripts/upload_assets.py                  # dry run
  python3 scripts/upload_assets.py --apply          # upload what's missing

Upload only (stagedUploadsCreate + fileCreate). A filename that already exists in Files is skipped and
never changed, so the script is safe to run again. Slots marked "existing" in the manifest are only
checked for presence. Each new upload is polled until it reaches READY.
"""
import argparse, json, mimetypes, os, sys, time, urllib.request, uuid

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools", "shopify"))
from shopify_client import Store, ShopifyError  # noqa: E402

MANIFEST = os.path.join(ROOT, "docs", "assets", "manifest.json")
DIST = os.path.join(ROOT, "docs", "assets", "dist")
SCOPES = ["read_files", "write_files"]
MIME = {".svg": "image/svg+xml", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}

FILE_BY_NAME = """query($q: String!) { files(first: 25, query: $q) { nodes { id fileStatus
  ... on MediaImage { image { url } } ... on GenericFile { url } } } }"""
FILE_STATUS = """query($id: ID!) { node(id: $id) { ... on MediaImage { id fileStatus fileErrors { message } }
  ... on GenericFile { id fileStatus fileErrors { message } } } }"""
STAGED = """mutation($input: [StagedUploadInput!]!) { stagedUploadsCreate(input: $input) {
  stagedTargets { url resourceUrl parameters { name value } } userErrors { field message } } }"""
FILE_CREATE = """mutation($files: [FileCreateInput!]!) { fileCreate(files: $files) {
  files { id fileStatus } userErrors { field message code } } }"""


def wanted(manifest):
    """Yield (filename, alt, existing) for every file the manifest references."""
    for slot, entry in manifest.items():
        existing = entry.get("source") == "existing"
        for key in ("desktop", "mobile"):
            if entry.get(key):
                yield slot, entry[key], entry["alt"], existing


def find_file(store, filename):
    stem = os.path.splitext(filename)[0]
    for n in store.gql(FILE_BY_NAME, {"q": f"filename:{stem}"})["files"]["nodes"]:
        url = ((n.get("image") or {}).get("url") or n.get("url") or "").split("?")[0]
        if os.path.basename(url) == filename:
            return n
    return None


def upload(store, path, alt):
    filename = os.path.basename(path)
    mime = MIME.get(os.path.splitext(filename)[1].lower()) or mimetypes.guess_type(filename)[0]
    size = os.path.getsize(path)
    r = store.gql(STAGED, {"input": [{"resource": "IMAGE", "filename": filename, "mimeType": mime,
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
    r = store.gql(FILE_CREATE, {"files": [{"originalSource": t["resourceUrl"], "contentType": "IMAGE",
                                           "alt": alt, "filename": filename,
                                           "duplicateResolutionMode": "RAISE_ERROR"}]}, idempotent=False)["fileCreate"]
    if r["userErrors"]:
        raise ShopifyError(f"fileCreate {filename}: {r['userErrors']}")
    fid = r["files"][0]["id"]
    for _ in range(90):
        n = store.gql(FILE_STATUS, {"id": fid})["node"] or {}
        if n.get("fileStatus") == "READY":
            return fid, "READY"
        if n.get("fileStatus") == "FAILED":
            raise ShopifyError(f"{filename} failed processing: {n.get('fileErrors')}")
        time.sleep(2)
    return fid, n.get("fileStatus") or "UNKNOWN"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", default="store")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    manifest = json.load(open(MANIFEST, encoding="utf-8"))
    store = Store(a.store)
    store.ensure_token(SCOPES)
    store.ensure_scopes(SCOPES)
    print(f"{store.shop}: {'APPLY' if a.apply else 'dry run (nothing is written)'}\n")

    problems, uploaded, skipped = [], [], []
    for slot, filename, alt, existing in wanted(manifest):
        found = find_file(store, filename)
        if existing:
            if found:
                print(f"  ok        {filename}  (existing, {slot})")
            else:
                print(f"  MISSING   {filename}  (marked existing for {slot} but not in Files)")
                problems.append(filename)
            continue
        if found:
            print(f"  skip      {filename}  (already in Files, {found['fileStatus']})")
            skipped.append(filename)
            continue
        path = os.path.join(DIST, filename)
        if not os.path.exists(path):
            print(f"  MISSING   {filename}  (not in docs/assets/dist)")
            problems.append(filename)
            continue
        if not a.apply:
            print(f"  upload    {filename}  ({os.path.getsize(path) // 1024} KB)  alt: {alt}")
            continue
        fid, status = upload(store, path, alt)
        print(f"  uploaded  {filename}  {status}  {fid}")
        uploaded.append((filename, status))
        if status != "READY":
            problems.append(filename)

    print(f"\n{len(uploaded)} uploaded, {len(skipped)} skipped, {len(problems)} problem(s)")
    if problems:
        print("Problems: " + ", ".join(problems))
        sys.exit(1)


if __name__ == "__main__":
    main()
