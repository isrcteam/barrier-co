#!/usr/bin/env python3
"""Read-only export of a Shopify store: data, definitions and the live theme.

Usage (from anywhere in the project repo):
  python3 tools/shopify/export.py --store source
  python3 tools/shopify/export.py --store source --only products collections     partial run, not used as "latest"
  python3 tools/shopify/export.py --store source --no-theme
  python3 tools/shopify/export.py --store source --token-only
  python3 tools/shopify/export.py --store source --reauth                        drop the saved token first

Output: docs/data/raw/<UTC timestamp>/*.json, .../theme/ (live theme files) and summary.json.
docs/data/raw/ must be gitignored.

Products, variants, collections, pages, blogs and articles come through bulk operations (one JSONL
download each), so store size doesn't matter and there is no per-query cost limit. Everything else is
small enough to page through directly. Each part is exported on its own: a failure is recorded in
summary.json and the rest carries on. The exit code is 2 when anything failed.
"""
import argparse, base64, json, os, sys, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shopify_client import READ_SCOPES, ShopifyError, Store, die, docs_path, utc_stamp

MF_BULK = "metafields { edges { node { __typename namespace key type value } } }"

BULK = {
    "products": """{ products { edges { node { id handle title status vendor productType tags templateSuffix descriptionHtml createdAt updatedAt
        seo { title description } options { name values } %s
        media { edges { node { __typename id alt mediaContentType ... on MediaImage { image { url width height } }
        ... on Video { sources { url mimeType height } } } } } } } } }""" % MF_BULK,
    "variants": """{ productVariants { edges { node { id title sku barcode price compareAtPrice position taxable inventoryPolicy
        product { id handle } selectedOptions { name value } media { edges { node { __typename ... on MediaImage { image { url altText } } } } } %s } } } }""" % MF_BULK,
    "collections": """{ collections { edges { node { id handle title descriptionHtml templateSuffix sortOrder updatedAt seo { title description }
        image { url altText } productsCount { count }
        ruleSet { appliedDisjunctively rules { column relation condition conditionObject { __typename
          ... on CollectionRuleMetafieldCondition { metafieldDefinition { id namespace key ownerType } }
          ... on CollectionRuleProductCategoryCondition { category: value { id fullName } }
          ... on CollectionRuleTextCondition { text: value } } } }
        products { edges { node { __typename handle } } } %s } } } }""" % MF_BULK,
    "pages": """{ pages { edges { node { id handle title body templateSuffix isPublished updatedAt
        seoTitle: metafield(namespace: "global", key: "title_tag") { value type }
        seoDescription: metafield(namespace: "global", key: "description_tag") { value type } %s } } } }""" % MF_BULK,
    "blogs": """{ blogs { edges { node { id handle title templateSuffix commentPolicy %s } } } }""" % MF_BULK,
    "articles": """{ articles { edges { node { id handle title body summary tags templateSuffix isPublished publishedAt author { name }
        blog { handle } image { url altText }
        seoTitle: metafield(namespace: "global", key: "title_tag") { value type }
        seoDescription: metafield(namespace: "global", key: "description_tag") { value type } %s } } } }""" % MF_BULK,
}
CHILD_KEYS = {"Metafield": "metafields", "MediaImage": "media", "Video": "media", "ExternalVideo": "media", "Model3d": "media",
              "Product": "products"}
CHILD_DEFAULTS = {"products": ("metafields", "media"), "variants": ("metafields", "media"), "collections": ("metafields", "products"),
                  "pages": ("metafields",), "blogs": ("metafields",), "articles": ("metafields",)}

Q = {
    "shop": """query Shop($after: String) { shop { id name email myshopifyDomain primaryDomain { url host } currencyCode ianaTimezone description
        metafields(first: 250, after: $after) { pageInfo { hasNextPage endCursor } nodes { namespace key type value } } }
        shopLocales { locale name primary published } }""",
    "metafield_definitions": """query MetafieldDefinitions($ownerType: MetafieldOwnerType!, $after: String) {
        metafieldDefinitions(ownerType: $ownerType, first: 100, after: $after) { pageInfo { hasNextPage endCursor } nodes {
        id name namespace key description ownerType type { name } validations { name value } pinnedPosition access { admin storefront }
        capabilities { smartCollectionCondition { enabled } adminFilterable { enabled } } } } }""",
    "metaobject_definitions": """query MetaobjectDefinitions($after: String) { metaobjectDefinitions(first: 50, after: $after) {
        pageInfo { hasNextPage endCursor } nodes { id type name description displayNameKey metaobjectsCount access { admin storefront }
        capabilities { publishable { enabled } translatable { enabled } renderable { enabled } onlineStore { enabled } }
        fieldDefinitions { key name description required type { name } validations { name value } } } } }""",
    "metaobjects": """query Metaobjects($type: String!, $after: String) { metaobjects(type: $type, first: 100, after: $after) {
        pageInfo { hasNextPage endCursor } nodes { id handle type displayName updatedAt capabilities { publishable { status } }
        fields { key type value } } } }""",
    "menus": """query Menus($after: String) { menus(first: 50, after: $after) { pageInfo { hasNextPage endCursor } nodes { id handle title
        items { title type url resourceId tags items { title type url resourceId tags items { title type url resourceId tags } } } } } }""",
    "redirects": """query Redirects($after: String) { urlRedirects(first: 250, after: $after) { pageInfo { hasNextPage endCursor } nodes { id path target } } }""",
    "files": """query Files($after: String) { files(first: 100, after: $after) { pageInfo { hasNextPage endCursor } nodes { id alt fileStatus createdAt
        ... on MediaImage { image { url width height } mimeType } ... on GenericFile { url mimeType originalFileSize }
        ... on Video { filename sources { url mimeType height } } } } }""",
    "markets": """query Markets($after: String) { markets(first: 50, after: $after) { pageInfo { hasNextPage endCursor } nodes { id name handle status type } } }""",
    "themes": """query Themes { themes(first: 20) { nodes { id name role updatedAt } } }""",
    "theme_files": """query ThemeFiles($id: ID!, $after: String) { theme(id: $id) { id name role files(first: 250, after: $after) {
        pageInfo { hasNextPage endCursor } nodes { filename size checksumMd5 body { ... on OnlineStoreThemeFileBodyText { content }
        ... on OnlineStoreThemeFileBodyBase64 { contentBase64 } ... on OnlineStoreThemeFileBodyUrl { url } } } } } }""",
    "translations": """query Translations($type: TranslatableResourceType!, $locale: String!, $after: String) {
        translatableResources(resourceType: $type, first: 100, after: $after) { pageInfo { hasNextPage endCursor } nodes {
        resourceId translations(locale: $locale) { key value locale outdated } } } }""",
}

OWNER_TYPES = ["PRODUCT", "PRODUCTVARIANT", "COLLECTION", "PAGE", "BLOG", "ARTICLE", "SHOP", "MARKET"]
TRANSLATABLE = ["PRODUCT", "PRODUCT_OPTION", "PRODUCT_OPTION_VALUE", "COLLECTION", "COLLECTION_IMAGE", "PAGE", "ARTICLE", "ARTICLE_IMAGE",
                "BLOG", "METAOBJECT", "MENU", "LINK", "SHOP", "SHOP_POLICY", "FILTER", "MEDIA_IMAGE", "ONLINE_STORE_THEME",
                "ONLINE_STORE_THEME_LOCALE_CONTENT", "ONLINE_STORE_THEME_JSON_TEMPLATE", "ONLINE_STORE_THEME_SECTION_GROUP",
                "ONLINE_STORE_THEME_SETTINGS_CATEGORY", "ONLINE_STORE_THEME_SETTINGS_DATA_SECTIONS", "ONLINE_STORE_THEME_APP_EMBED"]
SIMPLE = {"menus": ["menus"], "redirects": ["urlRedirects"], "files": ["files"], "markets": ["markets"]}
ORDER = ["shop", "products", "variants", "collections", "pages", "blogs", "articles", "metafield_definitions",
         "metaobject_definitions", "metaobjects", "menus", "redirects", "files", "markets", "translations", "theme"]


def assemble(jsonl_path, part):
    """Turn Shopify's bulk JSONL (parents, then children with __parentId) back into nested records."""
    parents, order = {}, []
    orphans = 0
    with open(jsonl_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            pid = obj.pop("__parentId", None)
            typename = obj.pop("__typename", None)
            if pid is None:
                for key in CHILD_DEFAULTS.get(part, ()):
                    obj[key] = {"pageInfo": {"hasNextPage": False}, "nodes": []}
                parents[obj["id"]] = obj
                order.append(obj["id"])
                continue
            parent = parents.get(pid)
            key = CHILD_KEYS.get(typename)
            if parent is None or key is None:
                orphans += 1
                continue
            parent.setdefault(key, {"pageInfo": {"hasNextPage": False}, "nodes": []})["nodes"].append(obj)
    return [parents[i] for i in order], orphans


def export_bulk(store, part, out, summary):
    jsonl = os.path.join(out, f"{part}.jsonl")
    count = store.bulk_query(BULK[part], jsonl, on_status=lambda s, n: print(f"    {s.lower()}, {n or 0} objects so far", flush=True))
    data, orphans = assemble(jsonl, part)
    if orphans:
        summary["truncated"].append(f"{part}: {orphans} nested records could not be attached to a parent")
    os.remove(jsonl)
    return data


def export_theme(store, out, summary):
    themes = store.gql(Q["themes"])["themes"]["nodes"]
    write_json(os.path.join(out, "themes.json"), themes)
    live = next((t for t in themes if t["role"] == "MAIN"), None)
    if not live:
        raise ShopifyError("No live (MAIN) theme found")
    dest = os.path.join(out, "theme")
    count, failed = 0, []
    for f in store.paginate(Q["theme_files"], ["theme", "files"], {"id": live["id"]}):
        path = os.path.join(dest, f["filename"])
        os.makedirs(os.path.dirname(path), exist_ok=True)
        body = f.get("body") or {}
        try:
            if "content" in body:
                with open(path, "w", encoding="utf-8", newline="") as fh:
                    fh.write(body["content"])
            elif "contentBase64" in body:
                open(path, "wb").write(base64.b64decode(body["contentBase64"]))
            elif "url" in body:
                with urllib.request.urlopen(body["url"], timeout=120) as r:
                    open(path + ".part", "wb").write(r.read())
                os.replace(path + ".part", path)
            count += 1
        except (OSError, urllib.error.URLError, ValueError) as e:
            failed.append(f"{f['filename']}: {e}")
    summary["counts"]["theme_files"] = count
    summary["live_theme"] = {"id": live["id"], "name": live["name"], "updated": live["updatedAt"]}
    if failed:
        summary["failures"]["theme_files"] = failed[:50]
        print(f"    {len(failed)} theme file(s) could not be saved; see summary.json")


def write_json(path, data):
    with open(path + ".part", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(path + ".part", path)


def read_json(path, default):
    return json.load(open(path, encoding="utf-8")) if os.path.exists(path) else default


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--store", default="source")
    ap.add_argument("--only", nargs="*", choices=ORDER, metavar="PART", help="parts to export: " + ", ".join(ORDER))
    ap.add_argument("--no-theme", action="store_true")
    ap.add_argument("--token-only", action="store_true")
    ap.add_argument("--reauth", action="store_true", help="ignore the saved token and get a new one")
    ap.add_argument("--out", default=docs_path("data", "raw"))
    a = ap.parse_args()

    try:
        store = Store(a.store)
        store.ensure_token(READ_SCOPES, reauth=a.reauth)
        granted = store.granted_scopes()
    except ShopifyError as e:
        die(str(e))
    writes = [s for s in granted if s.startswith("write_")]
    print(f"Connected to {store.shop} (API {store.api_version}). Scopes: {', '.join(granted)}")
    if writes:
        print(f"Note: this app also has write scopes ({', '.join(writes)}). The export never writes.")
    missing = [s for s in READ_SCOPES if s not in granted and s.replace("read_", "write_") not in granted]
    if missing:
        print(f"Missing scopes, their parts will fail: {', '.join(missing)}")
    if a.token_only:
        return

    stamp = utc_stamp()
    out = os.path.join(a.out, stamp)
    n = 2
    while os.path.exists(out):
        out = os.path.join(a.out, f"{stamp}-{n}")
        n += 1
    os.makedirs(out)
    wanted = a.only or [p for p in ORDER if not (p == "theme" and a.no_theme)]
    summary = {"shop": store.shop, "api_version": store.api_version, "exported_at": stamp, "scopes": granted,
               "parts": wanted, "partial": bool(a.only), "complete": False, "counts": {}, "failures": {}, "truncated": []}
    summary_path = os.path.join(out, "summary.json")

    try:
        for part in ORDER:
            if part not in wanted:
                continue
            print(f"  {part}...", flush=True)
            try:
                if part == "shop":
                    data = store.gql(Q["shop"], {"after": None})
                    mfs = data["shop"].get("metafields") or {}
                    if (mfs.get("pageInfo") or {}).get("hasNextPage"):
                        summary["truncated"].append("shop: more than 250 shop metafields, only the first page exported")
                elif part in BULK:
                    data = export_bulk(store, part, out, summary)
                elif part in SIMPLE:
                    data = list(store.paginate(Q[part], SIMPLE[part]))
                elif part == "metafield_definitions":
                    data = []
                    for owner in OWNER_TYPES:
                        try:
                            data += list(store.paginate(Q[part], ["metafieldDefinitions"], {"ownerType": owner}))
                        except ShopifyError as e:
                            summary["failures"][f"metafield_definitions:{owner}"] = str(e)[:300]
                elif part == "metaobject_definitions":
                    data = list(store.paginate(Q[part], ["metaobjectDefinitions"]))
                elif part == "metaobjects":
                    defs = read_json(os.path.join(out, "metaobject_definitions.json"), None)
                    if defs is None:
                        defs = list(store.paginate(Q["metaobject_definitions"], ["metaobjectDefinitions"]))
                    data = []
                    for d in defs:
                        try:
                            data += list(store.paginate(Q[part], ["metaobjects"], {"type": d["type"]}))
                        except ShopifyError as e:
                            summary["failures"][f"metaobjects:{d['type']}"] = str(e)[:300]
                elif part == "translations":
                    shop = read_json(os.path.join(out, "shop.json"), None) or store.gql(Q["shop"], {"after": None})
                    locales = [l["locale"] for l in shop["shopLocales"] if not l["primary"]]
                    data = {}
                    for loc in locales:
                        data[loc] = {}
                        for t in TRANSLATABLE:
                            try:
                                rows = [r for r in store.paginate(Q[part], ["translatableResources"], {"type": t, "locale": loc}) if r["translations"]]
                            except ShopifyError as e:
                                summary["failures"][f"translations:{loc}:{t}"] = str(e)[:300]
                                continue
                            if rows:
                                data[loc][t] = rows
                elif part == "theme":
                    export_theme(store, out, summary)
                    continue
                write_json(os.path.join(out, f"{part}.json"), data)
                if part == "translations":
                    summary["counts"][part] = sum(len(rows) for loc in data.values() for rows in loc.values())
                else:
                    summary["counts"][part] = len(data) if isinstance(data, list) else 1
            except ShopifyError as e:
                summary["failures"][part] = str(e)[:500]
                print(f"    failed: {str(e)[:200]}")
            except Exception as e:  # noqa: BLE001 - one part must never take the run down
                summary["failures"][part] = f"{type(e).__name__}: {str(e)[:400]}"
                print(f"    failed: {type(e).__name__}: {str(e)[:200]}")
        summary["complete"] = not summary["failures"]
    finally:
        write_json(summary_path, summary)

    print(f"\nDone: {out}" + (" (partial run, not used as the latest export)" if a.only else ""))
    for k, v in summary["counts"].items():
        print(f"  {k:24} {v}")
    if summary["truncated"]:
        print(f"  {len(summary['truncated'])} note(s) about nested data; see summary.json")
    if summary["failures"]:
        print("Failures:", ", ".join(summary["failures"]))
        sys.exit(2)


if __name__ == "__main__":
    main()
