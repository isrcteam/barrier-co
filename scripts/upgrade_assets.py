#!/usr/bin/env python3
"""Upgrade the theme's image files in place and set alt text on every image the theme uses.

Dry run by default: reads Files and products (read only) and prints what it would change.
  python3 scripts/upgrade_assets.py                                   # dry run
  python3 scripts/upgrade_assets.py --apply                           # write
  python3 scripts/upgrade_assets.py --source-dir <dir> [--apply]      # also re-encode hi-res sources

1. Hi-res. Every photo slot in docs/assets/manifest.json with a "figma ..." source is checked against
   the native size of its original Figma image fill (FIGMA_NATIVE, read with download_assets). When the
   original is wider than the file in the store, the original (from --source-dir, named after the store
   file) is cropped to the slot's current aspect ratio, capped at 3840 wide for full-bleed slots and 1600
   for cards and tiles, encoded as JPG at quality 82, and swapped into the EXISTING MediaImage with a
   staged upload and fileUpdate(originalSource). The id and filename never change; the file is polled
   back to READY. Files reused from the live site ("existing") and product images are never replaced.
2. Alt text. Every manifest file, every seeded file in docs/data/seed-result.json and the reused
   live-site files get their alt set with fileUpdate(files: [{id, alt}]). Product media with an empty
   alt are set with productUpdateMedia. Nothing else on an existing file is changed.
3. With --apply, docs/assets/manifest.json gets each slot's width, height (and mobile_width,
   mobile_height) and final alt.

No deletes, no new files, no publishing, no theme changes.
"""
import argparse, json, os, sys, time, urllib.request, uuid

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools", "shopify"))
from shopify_client import Store, ShopifyError  # noqa: E402

MANIFEST = os.path.join(ROOT, "docs", "assets", "manifest.json")
SEED = os.path.join(ROOT, "docs", "data", "seed.json")
SEED_RESULT = os.path.join(ROOT, "docs", "data", "seed-result.json")
SCOPES = ["read_files", "write_files", "read_products", "write_products"]

FULL_BLEED = {"home_hero", "inset_banner", "video_banner_poster", "faq_background", "stats_background",
              "home_intro_video_poster", "pdp_benefit_photo"}
FULL_BLEED_MAX, CARD_MAX, QUALITY = 3840, 1600, 82
NOT_PHOTOS = ("feature_icon_", "logo_", "brand_logo_", "clinician_mark")

# Native pixel size of each photo file's original Figma image fill (file oZ00gYRP11BAdFQYwo4fxj).
FIGMA_NATIVE = {
    "home-hero-desktop.jpg": ("965:1254", 1402, 1122),
    "home-hero-mobile.jpg": ("965:3083", 1402, 1122),
    "intro-video-poster-desktop.jpg": ("965:1329", 1659, 948),
    "intro-video-poster-mobile.jpg": ("965:3147", 1659, 948),
    "routine-cleanse.jpg": ("965:1339", 728, 1092),
    "routine-protect.jpg": ("965:1339", 1254, 1254),
    "stats-background-desktop.jpg": ("978:4052", 736, 1104),
    "stats-background-mobile.jpg": ("978:4051", 736, 1104),
    "inset-banner-desktop.jpg": ("965:1579", 1672, 941),
    "inset-banner-mobile.jpg": ("965:3294", 1672, 941),
    "lifestyle-1.jpg": ("965:1587", 1505, 1045),
    "lifestyle-3.jpg": ("965:1587", 1102, 1427),
    "insta-1.jpg": ("978:4340", 1024, 1536),
    "insta-2.jpg": ("978:4340", 1122, 1402),
    "insta-3.jpg": ("978:4340", 1326, 1187),
    "insta-4.jpg": ("978:4340", 1335, 1178),
    "insta-5.jpg": ("978:4340", 1122, 1402),
    "insta-6.jpg": ("978:4340", 1326, 1187),
    "pdp-hotspot-cloth.jpg": ("965:2198", 1672, 941),
    "pdp-benefit-photo.jpg": ("965:2198", 1672, 941),
    "video-banner-poster-desktop.jpg": ("965:2346", 1672, 941),
    "video-banner-poster-mobile.jpg": ("965:3766", 1672, 941),
    "faq-background.jpg": ("978:4243", 1672, 941),
    "clinician-avatar-1.jpg": ("965:2075", 1707, 2560),
    "clinician-avatar-2.jpg": ("965:2075", 2000, 2629),
    "clinician-avatar-3.jpg": ("965:2075", 1000, 1500),
    "promo-card-image.jpg": ("965:2157", 1440, 1800),
}

# The design crop measured in the original's own pixels, where it is smaller than the ratio allows
# (the inset banner is also mirrored in the design).
NATIVE_CROP = {"intro-video-poster-mobile.jpg": (993, 840), "inset-banner-desktop.jpg": (1659, 790)}

# Larger source exists but the slot gains nothing from it.
HOLD = {
    "clinician-avatar-1.jpg": "rendered at 26px (largest request 120px); 480px already covers it",
    "clinician-avatar-2.jpg": "rendered at 26px (largest request 120px); 480px already covers it",
    "clinician-avatar-3.jpg": "rendered at 26px (largest request 120px); 480px already covers it",
}

# Crop box in the source as fractions (left, top, right, bottom); centred crop to the slot's ratio if absent.
CROPS = {}

SLOT_ALT = {
    "stats_background": "Close-up of warm brown skin across the neck, collarbone and shoulder",
    "feature_icon_1": "100% proven: deep skin hydration in 30 minutes",
    "feature_icon_2": "100% proven: helps reduce dryness",
    "feature_icon_3": "100% proven: supports smoother-looking skin",
    "feature_icon_4": "100% proven: improves skin texture",
    "lifestyle_2": "Woman pressing a soft pink towel to her face with both hands",
    "logo_equinox": "Equinox logo",
    "logo_delta_one": "Delta One logo",
    "logo_credo": "Credo logo",
    "brand_logo_light": "The Barrier Co. logo",
    "brand_logo_dark": "The Barrier Co. logo",
    "clinician_mark": "Clinicians' Choice laurel",
    "clinician_avatar_1": "Grey-haired clinician in glasses and a white coat, arms crossed",
    "clinician_avatar_2": "Smiling clinician with short silver hair in a camel turtleneck",
    "clinician_avatar_3": "Clinician with a dark bob and glasses in a white coat, looking to one side",
    "recognition_seal": "National Eczema Association Seal of Acceptance",
}
FILE_ALT = {
    "cloth-face-towel.jpg": SLOT_ALT["lifestyle_2"],
    "expert-avatar.jpg": "Marco Bellini smiling outdoors in a dark denim jacket",
    "ingredient-witch-hazel.png": "Yellow witch hazel flower on a black background",
    "ingredient-cocoa-butter.png": "Cocoa beans resting in drops of cocoa butter on a black background",
}

FILE_BY_NAME = """query($q: String!) { files(first: 25, query: $q) { nodes { id fileStatus alt
  ... on MediaImage { image { url width height } } } } }"""
FILE_NODE = """query($id: ID!) { node(id: $id) { ... on MediaImage { id fileStatus alt
  fileErrors { message } image { url width height } } } }"""
STAGED = """mutation($input: [StagedUploadInput!]!) { stagedUploadsCreate(input: $input) {
  stagedTargets { url resourceUrl parameters { name value } } userErrors { field message } } }"""
FILE_UPDATE = """mutation($files: [FileUpdateInput!]!) { fileUpdate(files: $files) {
  files { id fileStatus alt } userErrors { field message code } } }"""
PRODUCT_MEDIA = """query($id: ID!) { product(id: $id) { id handle media(first: 50) { nodes { id alt
  ... on MediaImage { image { url } } } } } }"""
PRODUCT_MEDIA_UPDATE = """mutation($pid: ID!, $media: [UpdateMediaInput!]!) { productUpdateMedia(productId: $pid, media: $media) {
  media { id alt } mediaUserErrors { field message } } }"""


def basename(url):
    return os.path.basename((url or "").split("?")[0])


def find_file(store, filename):
    stem = os.path.splitext(filename)[0]
    for n in store.gql(FILE_BY_NAME, {"q": f"filename:{stem}"})["files"]["nodes"]:
        if basename((n.get("image") or {}).get("url")) == filename:
            return n
    return None


def wait_ready(store, fid):
    n = {}
    for _ in range(120):
        n = store.gql(FILE_NODE, {"id": fid})["node"] or {}
        if n.get("fileStatus") == "READY":
            return n
        if n.get("fileStatus") == "FAILED":
            raise ShopifyError(f"{fid} failed processing: {n.get('fileErrors')}")
        time.sleep(2)
    raise ShopifyError(f"{fid} not READY after polling (status {n.get('fileStatus')})")


def encode(src, out, aspect, max_w, crop=None):
    from PIL import Image
    im = Image.open(src).convert("RGB")
    w, h = im.size
    if crop:
        box = (crop[0] * w, crop[1] * h, crop[2] * w, crop[3] * h)
    else:
        cw, ch = (w, w / aspect) if w / h <= aspect else (h * aspect, h)
        box = ((w - cw) / 2, (h - ch) / 2, (w + cw) / 2, (h + ch) / 2)
    im = im.crop(tuple(round(v) for v in box))
    if im.width > max_w:
        im = im.resize((max_w, round(max_w * im.height / im.width)), Image.LANCZOS)
    im.save(out, "JPEG", quality=QUALITY, optimize=True, progressive=True)
    return im.size


def staged_upload(store, path, filename):
    size = os.path.getsize(path)
    r = store.gql(STAGED, {"input": [{"resource": "IMAGE", "filename": filename, "mimeType": "image/jpeg",
                                      "httpMethod": "POST", "fileSize": str(size)}]}, idempotent=False)["stagedUploadsCreate"]
    if r["userErrors"]:
        raise ShopifyError(f"stagedUploadsCreate {filename}: {r['userErrors']}")
    t = r["stagedTargets"][0]
    boundary = uuid.uuid4().hex
    body = b""
    for p in t["parameters"]:
        body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"{p['name']}\"\r\n\r\n{p['value']}\r\n".encode()
    body += (f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{filename}\"\r\n"
             f"Content-Type: image/jpeg\r\n\r\n").encode() + open(path, "rb").read() + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(t["url"], data=body, method="POST",
                                 headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(req, timeout=300) as resp:
        if resp.status not in (200, 201, 204):
            raise ShopifyError(f"upload of {filename} failed: HTTP {resp.status}")
    return t["resourceUrl"]


def replace_image(store, node, filename, path):
    resource = staged_upload(store, path, filename)
    r = store.gql(FILE_UPDATE, {"files": [{"id": node["id"], "originalSource": resource}]},
                  idempotent=False)["fileUpdate"]
    if r["userErrors"]:
        raise ShopifyError(f"fileUpdate {filename}: {r['userErrors']}")
    time.sleep(3)
    after = wait_ready(store, node["id"])
    if basename(after["image"]["url"]) != filename:
        raise ShopifyError(f"{filename}: filename changed to {basename(after['image']['url'])}")
    return after


def manifest_files(manifest):
    for slot, e in manifest.items():
        for key in ("desktop", "mobile"):
            if e.get(key):
                yield slot, key, e[key], e


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", default="store")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--source-dir", help="folder of original Figma fills, each named after its store file")
    a = ap.parse_args()
    manifest = json.load(open(MANIFEST, encoding="utf-8"))
    seed = json.load(open(SEED, encoding="utf-8"))
    seed_result = json.load(open(SEED_RESULT, encoding="utf-8"))
    store = Store(a.store)
    store.ensure_token(SCOPES)
    store.ensure_scopes(SCOPES)
    print(f"{store.shop}: {'APPLY' if a.apply else 'dry run (nothing is written)'}\n")

    alt_for, nodes, problems = {}, {}, []
    for slot, _, filename, e in manifest_files(manifest):
        alt_for[filename] = SLOT_ALT.get(slot, e["alt"])
    seed_alt = {os.path.basename(f["path"]): f["alt"] for f in seed["files"]}
    for f in seed_result["files"].values():
        alt_for.setdefault(f["filename"], seed_alt.get(f["filename"]))
    for filename, alt in FILE_ALT.items():
        alt_for[filename] = alt
    for filename, alt in alt_for.items():
        if not alt or len(alt) >= 125 or alt.lower().startswith(("image of", "picture of", "photo of")):
            problems.append(f"{filename}: alt needs work ({alt!r})")
    for filename in alt_for:
        n = find_file(store, filename)
        if not n:
            problems.append(f"{filename}: not in Files")
        nodes[filename] = n

    print("Hi-res check")
    upgraded, too_small = [], []
    for slot, key, filename, e in manifest_files(manifest):
        if not e["source"].startswith("figma") or slot.startswith(NOT_PHOTOS) or not nodes.get(filename):
            continue
        n = nodes[filename]
        cur_w, cur_h = n["image"]["width"], n["image"]["height"]
        node_id, nat_w, nat_h = FIGMA_NATIVE[filename]
        max_w = FULL_BLEED_MAX if slot in FULL_BLEED else CARD_MAX
        aspect = cur_w / cur_h
        crop_w = min(nat_w, nat_h * aspect, max_w, NATIVE_CROP.get(filename, (nat_w,))[0])
        if crop_w <= cur_w:
            print(f"  too small {filename:34} {cur_w}x{cur_h}  Figma {node_id} original {nat_w}x{nat_h}")
            too_small.append(filename)
            continue
        if filename in HOLD:
            print(f"  hold      {filename:34} {cur_w}x{cur_h}  original {nat_w}x{nat_h}: {HOLD[filename]}")
            continue
        src = a.source_dir and next((os.path.join(a.source_dir, x) for x in os.listdir(a.source_dir)
                                     if os.path.splitext(x)[0] == os.path.splitext(filename)[0]), None)
        if not src:
            print(f"  upgrade   {filename:34} {cur_w}x{cur_h} -> ~{int(crop_w)}w  (needs --source-dir)")
            continue
        out = os.path.join(a.source_dir, "_encoded_" + filename)
        new_w, new_h = encode(src, out, aspect, max_w, CROPS.get(filename))
        if not a.apply:
            print(f"  upgrade   {filename:34} {cur_w}x{cur_h} -> {new_w}x{new_h}  ({os.path.getsize(out) // 1024} KB)")
            continue
        after = replace_image(store, n, filename, out)
        same = after["id"] == n["id"]
        print(f"  upgraded  {filename:34} {cur_w}x{cur_h} -> {after['image']['width']}x{after['image']['height']}"
              f"  {after['fileStatus']}  id {'unchanged' if same else 'CHANGED'}")
        nodes[filename] = after
        upgraded.append(filename)
        if not same:
            problems.append(f"{filename}: id changed")

    print("\nAlt text")
    changes = [{"id": nodes[f]["id"], "alt": alt} for f, alt in alt_for.items()
               if nodes.get(f) and (nodes[f].get("alt") or "") != alt]
    for f, alt in alt_for.items():
        if nodes.get(f):
            same = (nodes[f].get("alt") or "") == alt
            print(f"  {'ok  ' if same else 'set '} {f:34} {alt}")
    if a.apply:
        for i in range(0, len(changes), 10):
            r = store.gql(FILE_UPDATE, {"files": changes[i:i + 10]}, idempotent=True)["fileUpdate"]
            if r["userErrors"]:
                problems.append(f"fileUpdate alt: {r['userErrors']}")
        for f in alt_for:
            if nodes.get(f):
                after = store.gql(FILE_NODE, {"id": nodes[f]["id"]})["node"]
                if after["alt"] != alt_for[f] or basename(after["image"]["url"]) != f or after["fileStatus"] != "READY":
                    problems.append(f"{f}: after alt update alt={after['alt']!r} status={after['fileStatus']}")
                nodes[f] = after

    print("\nProduct media")
    media_set = 0
    for handle, p in seed_result["products"].items():
        prod = store.gql(PRODUCT_MEDIA, {"id": p["id"]})["product"]
        empty = []
        for m in prod["media"]["nodes"]:
            fname = basename((m.get("image") or {}).get("url"))
            alt = alt_for.get(fname)
            status = "ok  " if m["alt"] else "set "
            print(f"  {status} {handle:32} {fname:24} {m['alt'] or alt!r}")
            if not m["alt"]:
                if alt:
                    empty.append({"id": m["id"], "alt": alt})
                else:
                    problems.append(f"{handle}: {fname} has no alt and none is known")
        if empty and a.apply:
            r = store.gql(PRODUCT_MEDIA_UPDATE, {"pid": p["id"], "media": empty}, idempotent=True)["productUpdateMedia"]
            if r["mediaUserErrors"]:
                problems.append(f"productUpdateMedia {handle}: {r['mediaUserErrors']}")
            media_set += len(empty)

    if a.apply:
        for slot, key, filename, e in manifest_files(manifest):
            n = nodes.get(filename)
            if not n:
                continue
            prefix = "" if key == "desktop" else "mobile_"
            e[prefix + "width"], e[prefix + "height"] = n["image"]["width"], n["image"]["height"]
            e["alt"] = alt_for[filename]
        with open(MANIFEST, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print("\nUpdated docs/assets/manifest.json")

    print(f"\n{len(upgraded)} upgraded, {len(too_small)} source too small, {len(changes)} file alt change(s)"
          f"{'' if a.apply else ' pending'}, {media_set} product media alt set, {len(problems)} problem(s)")
    if problems:
        print("Problems:\n  " + "\n  ".join(problems))
        sys.exit(1)


if __name__ == "__main__":
    main()
