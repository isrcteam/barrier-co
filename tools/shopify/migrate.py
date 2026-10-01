#!/usr/bin/env python3
"""Copy an export into a dev or staging store, with definitions and remapped references.

Usage:
  python3 tools/shopify/migrate.py --to dev                      dry run: shows what would happen, no token needed
  python3 tools/shopify/migrate.py --to dev --apply              runs it; needs the approval row the dry run prints
  python3 tools/shopify/migrate.py --to dev --apply --only products metafields
  python3 tools/shopify/migrate.py --to dev --apply --limit 20   seed 20 products (and 20 files) for a quick dev store
  python3 tools/shopify/migrate.py --to dev --apply --redo       run every phase again, even ones already done

Order: metaobject definitions, metafield definitions, files, products, collections, pages, blogs,
articles, metaobjects, metafields (all owners, references remapped), menus, redirects.
Refuses any target whose role in stores.json isn't dev or staging.
Progress and the old-to-new ID map are saved in docs/data/migrate/<alias>.json and bound to the target
shop and the export it came from. A rerun skips finished phases and products already copied; --only runs
the named phases again, --redo runs everything again.
Inventory, customers, orders and discounts are never copied.
"""
import argparse, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shopify_client import MIGRATE_SCOPES, READ_SCOPES, ShopifyError, Store, die, docs_path, latest_run, require_approval

PHASES = ["metaobject_definitions", "metafield_definitions", "files", "products", "collections", "pages", "blogs",
          "articles", "metaobjects", "metafields", "menus", "redirects"]
GID = re.compile(r"gid://shopify/([A-Za-z]+)/(\d+)")
# Namespaces that belong to apps or to Shopify itself (category metafields), plus the reviews app.
# "global" is kept: page and article SEO titles and descriptions live there.
NON_IDEMPOTENT = {"mo_def", "mf_def", "file", "coll_create", "page", "blog", "article", "menu_create", "redirect"}


# Shopify's standard definitions: enabled from Shopify's template, never created as custom definitions
STANDARD_NAMESPACES = ("descriptors", "reviews", "mm-google-shopping", "shopify--discovery--product_recommendation", "shopify--discovery--product_search_boost")


def skip_namespace(ns):
    if ns in STANDARD_NAMESPACES:
        return False
    return ns.startswith("app--") or ns.startswith("shopify--") or ns == "shopify"

M = {
    "mo_def": "mutation($d: MetaobjectDefinitionCreateInput!) { metaobjectDefinitionCreate(definition: $d) { metaobjectDefinition { id type } userErrors { field message code } } }",
    "mf_def": "mutation($d: MetafieldDefinitionInput!) { metafieldDefinitionCreate(definition: $d) { createdDefinition { id } userErrors { field message code } } }",
    "mf_def_std": "mutation($ns: String!, $k: String!, $o: MetafieldOwnerType!, $pin: Boolean) { standardMetafieldDefinitionEnable(namespace: $ns, key: $k, ownerType: $o, pin: $pin, access: { storefront: PUBLIC_READ }) { createdDefinition { id } userErrors { field message code } } }",
    "file": "mutation($f: [FileCreateInput!]!) { fileCreate(files: $f) { files { id fileStatus } userErrors { field message code } } }",
    "file_status": "query($ids: [ID!]!) { nodes(ids: $ids) { ... on File { id fileStatus } } }",
    "product": "mutation($i: ProductSetInput!, $h: ProductSetIdentifiers) { productSet(input: $i, identifier: $h, synchronous: true) { product { id handle variants(first: 250) { nodes { id title } } } userErrors { field message code } } }",
    "coll_find": "query($h: String!) { collectionByIdentifier(identifier: { handle: $h }) { id } }",
    "coll_create": "mutation($i: CollectionInput!) { collectionCreate(input: $i) { collection { id } userErrors { field message } } }",
    "coll_update": "mutation($i: CollectionInput!) { collectionUpdate(input: $i) { collection { id } userErrors { field message } } }",
    "coll_add": "mutation($id: ID!, $p: [ID!]!) { collectionAddProductsV2(id: $id, productIds: $p) { job { id } userErrors { field message } } }",
    "find": "query($q: String!) { pages(first: 1, query: $q) { nodes { id handle } } blogs(first: 1, query: $q) { nodes { id handle } } articles(first: 1, query: $q) { nodes { id handle } } }",
    "page": "mutation($p: PageCreateInput!) { pageCreate(page: $p) { page { id } userErrors { field message code } } }",
    "blog": "mutation($b: BlogCreateInput!) { blogCreate(blog: $b) { blog { id } userErrors { field message code } } }",
    "article": "mutation($a: ArticleCreateInput!) { articleCreate(article: $a) { article { id } userErrors { field message code } } }",
    "mo_upsert": "mutation($h: MetaobjectHandleInput!, $m: MetaobjectUpsertInput!) { metaobjectUpsert(handle: $h, metaobject: $m) { metaobject { id } userErrors { field message code } } }",
    "mf_set": "mutation($m: [MetafieldsSetInput!]!) { metafieldsSet(metafields: $m) { metafields { id } userErrors { field message code } } }",
    "menus": "query { menus(first: 250) { nodes { id handle } } }",
    "menu_create": "mutation($t: String!, $h: String!, $i: [MenuItemCreateInput!]!) { menuCreate(title: $t, handle: $h, items: $i) { menu { id } userErrors { field message code } } }",
    "menu_update": "mutation($id: ID!, $t: String!, $h: String, $i: [MenuItemUpdateInput!]!) { menuUpdate(id: $id, title: $t, handle: $h, items: $i) { menu { id } userErrors { field message code } } }",
    "redirect": "mutation($r: UrlRedirectInput!) { urlRedirectCreate(urlRedirect: $r) { urlRedirect { id } userErrors { field message code } } }",
    "existing": "query($o: MetafieldOwnerType!) { metafieldDefinitions(ownerType: $o, first: 250) { nodes { id namespace key } } metaobjectDefinitions(first: 250) { nodes { id type } } shop { id } }",
}


class Migration:
    def __init__(self, target, run, apply, limit, source_shop):
        self.t, self.run, self.apply, self.limit = target, run, apply, limit
        self.state_path = docs_path("data", "migrate", f"{target.alias}.json")
        fresh = {"target": target.shop, "source": source_shop, "map": {}, "done": [], "runs": []}
        self.state = json.load(open(self.state_path, encoding="utf-8")) if os.path.exists(self.state_path) else fresh
        if self.state.get("target") and self.state["target"] != target.shop:
            die(f"Refusing: {self.state_path} holds IDs for {self.state['target']}, not {target.shop}. Rename or delete it first.")
        if self.state.get("source") and self.state["source"] != source_shop:
            die(f"Refusing: {self.state_path} was built from an export of {self.state['source']}, this export is from {source_shop}. Rename or delete it first.")
        self.state.setdefault("target", target.shop)
        self.state.setdefault("source", source_shop)
        self.state.setdefault("runs", [])
        if os.path.basename(run) not in self.state["runs"]:
            self.state["runs"].append(os.path.basename(run))
        self.log = []
        self.redo = False

    def load(self, name):
        p = os.path.join(self.run, f"{name}.json")
        return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else []

    def save(self):
        if self.apply:
            os.makedirs(os.path.dirname(self.state_path), exist_ok=True)
            with open(self.state_path + ".tmp", "w", encoding="utf-8") as f:
                json.dump(self.state, f, indent=1)
            os.replace(self.state_path + ".tmp", self.state_path)

    def remember(self, old, new):
        m = GID.match(old or "")
        if m and new:
            self.state["map"].setdefault(m.group(1), {})[m.group(2)] = new

    def lookup(self, old):
        m = GID.match(old or "")
        return self.state["map"].get(m.group(1), {}).get(m.group(2)) if m else None

    def call(self, name, variables, result_key):
        data = self.t.gql(M[name], variables, idempotent=name not in NON_IDEMPOTENT)
        node = data[result_key]
        errs = (node or {}).get("userErrors") or []
        if errs:
            raise ShopifyError("; ".join(f"{'.'.join(e.get('field') or [])} {e['message']}" for e in errs))
        return node

    def note(self, msg):
        self.log.append(msg)
        print(f"    {msg}")

    def remap_value(self, typ, value):
        if value is None or "reference" not in (typ or ""):
            return value
        if typ.startswith("list."):
            try:
                items = json.loads(value)
            except ValueError:
                return value
            mapped = [self.lookup(v) for v in items]
            missing = [v for v, n in zip(items, mapped) if not n]
            if missing:
                self.note(f"dropped {len(missing)} unmapped reference(s) in a {typ}")
            mapped = [n for n in mapped if n]
            return json.dumps(mapped) if mapped else None
        new = self.lookup(value)
        if not new:
            self.note(f"dropped unmapped reference {value}")
        return new

    # --- phases ---
    def metaobject_definitions(self):
        defs = self.load("metaobject_definitions")
        existing = {d["type"]: d["id"] for d in self.t.gql(M["existing"], {"o": "PRODUCT"})["metaobjectDefinitions"]["nodes"]} if self.apply else {}
        by_id = {d["id"]: d for d in defs}
        order, seen = [], set()
        def visit(d, stack=()):
            if d["id"] in seen:
                return
            if d["id"] in stack:
                self.note(f"reference cycle through {d['type']}; its self-references are created without validation")
                return
            for f in d["fieldDefinitions"]:
                for v in f.get("validations", []):
                    if v["name"] == "metaobject_definition_id" and v["value"] in by_id:
                        visit(by_id[v["value"]], stack + (d["id"],))
            seen.add(d["id"])
            order.append(d)
        for d in defs:
            visit(d)
        print(f"  {len(order)} metaobject definitions")
        for d in order:
            if not self.apply:
                continue
            if d["type"] in existing:
                self.remember(d["id"], existing[d["type"]])
                continue
            fields = []
            for f in d["fieldDefinitions"]:
                vals = []
                for v in f.get("validations", []):
                    if v["name"] == "metaobject_definition_id":
                        new = self.lookup(v["value"])
                        if not new:
                            continue
                        v = {"name": v["name"], "value": new}
                    vals.append({"name": v["name"], "value": v["value"]})
                fields.append({"key": f["key"], "name": f["name"], "description": f.get("description") or "",
                               "required": f.get("required", False), "type": f["type"]["name"], "validations": vals})
            caps = d.get("capabilities") or {}
            body = {"type": d["type"], "name": d["name"], "description": d.get("description") or "", "fieldDefinitions": fields,
                    "access": {"storefront": ((d.get("access") or {}).get("storefront")) or "PUBLIC_READ"},
                    "capabilities": {k: {"enabled": bool((caps.get(k) or {}).get("enabled"))} for k in ("publishable", "translatable")}}
            if d.get("displayNameKey"):
                body["displayNameKey"] = d["displayNameKey"]
            try:
                node = self.call("mo_def", {"d": body}, "metaobjectDefinitionCreate")
                self.remember(d["id"], node["metaobjectDefinition"]["id"])
            except ShopifyError as e:
                self.note(f"metaobject definition {d['type']}: {e}")

    def metafield_definitions(self):
        defs = [d for d in self.load("metafield_definitions") if not skip_namespace(d["namespace"])]
        std = sum(d["namespace"] in STANDARD_NAMESPACES for d in defs)
        print(f"  {len(defs)} metafield definitions, {std} of them Shopify standard definitions enabled from the template (app-owned and category namespaces skipped)")
        if not self.apply:
            return
        existing = {}
        for owner in {d["ownerType"] for d in defs}:
            for n in self.t.gql(M["existing"], {"o": owner})["metafieldDefinitions"]["nodes"]:
                existing[(owner, n["namespace"], n["key"])] = n["id"]
        for d in defs:
            key = (d["ownerType"], d["namespace"], d["key"])
            if key in existing:
                self.remember(d["id"], existing[key])
                continue
            if d["namespace"] in STANDARD_NAMESPACES:
                try:
                    node = self.call("mf_def_std", {"ns": d["namespace"], "k": d["key"], "o": d["ownerType"], "pin": d.get("pinnedPosition") is not None}, "standardMetafieldDefinitionEnable")
                    self.remember(d["id"], (node.get("createdDefinition") or {}).get("id"))
                except ShopifyError as e:
                    self.note(f"standard definition {d['ownerType'].lower()} {d['namespace']}.{d['key']}: {e}")
                continue
            vals = []
            for v in d.get("validations", []):
                if v["name"] == "metaobject_definition_id":
                    new = self.lookup(v["value"])
                    if not new:
                        self.note(f"{d['namespace']}.{d['key']}: its metaobject definition wasn't migrated")
                        continue
                    v = {"name": v["name"], "value": new}
                vals.append({"name": v["name"], "value": v["value"]})
            caps = d.get("capabilities") or {}
            body = {"namespace": d["namespace"], "key": d["key"], "name": d["name"], "description": d.get("description") or "",
                    "ownerType": d["ownerType"], "type": d["type"]["name"], "validations": vals,
                    "pin": d.get("pinnedPosition") is not None,
                    "access": {"storefront": ((d.get("access") or {}).get("storefront")) or "PUBLIC_READ"},
                    "capabilities": {k: {"enabled": bool((caps.get(k) or {}).get("enabled"))} for k in ("smartCollectionCondition", "adminFilterable")}}
            try:
                node = self.call("mf_def", {"d": body}, "metafieldDefinitionCreate")
                self.remember(d["id"], (node.get("createdDefinition") or {}).get("id"))
            except ShopifyError as e:
                self.note(f"metafield definition {d['ownerType'].lower()} {d['namespace']}.{d['key']}: {e}")

    def _product_media_urls(self):
        urls = set()
        for p in self.load("products"):
            for m in ((p.get("media") or {}).get("nodes") or []):
                if m.get("image"):
                    urls.add(m["image"]["url"].split("?")[0])
        return urls

    def files(self):
        product_media = self._product_media_urls()
        files = [f for f in self.load("files") if not self.lookup(f["id"])]
        images = [f for f in files if (f.get("image") or f.get("url"))
                  and ((f.get("image") or {}).get("url") or f.get("url") or "").split("?")[0] not in product_media]
        videos = len([f for f in files if not (f.get("image") or f.get("url"))])
        product_images = len(files) - len(images) - videos
        if self.limit:
            images = images[: self.limit]
        print(f"  {len(images)} files to copy" + (f", {product_images} product images left to the products phase" if product_images else "")
              + (f", {videos} videos skipped (need staged uploads, upload by hand)" if videos else ""))
        if not self.apply:
            return
        for i in range(0, len(images), 25):
            batch = images[i:i + 25]
            inputs = [{"originalSource": (f.get("image") or {}).get("url") or f.get("url"), "alt": f.get("alt") or "",
                       "contentType": "IMAGE" if f.get("image") else "FILE"} for f in batch]
            try:
                node = self.call("file", {"f": inputs}, "fileCreate")
            except ShopifyError as e:
                self.note(f"files {i}-{i + len(batch)}: {e}")
                continue
            for old, new in zip(batch, node["files"]):
                self.remember(old["id"], new["id"])
            self.save()
        print("    files are processing in the background; references to them are set in the metafields phase")

    def products(self):
        products = self.load("products")
        variants = self.load("variants")
        if self.limit:
            products = products[: self.limit]
        by_product = {}
        for v in variants:
            by_product.setdefault(v["product"]["handle"], []).append(v)
        print(f"  {len(products)} products, {sum(len(by_product.get(p['handle'], [])) for p in products)} variants")
        if not self.apply:
            return
        skipped = 0
        for n, p in enumerate(products, 1):
            if self.lookup(p["id"]) and not self.redo:
                skipped += 1
                continue
            vs = sorted(by_product.get(p["handle"], []), key=lambda v: v.get("position") or 0)
            media = [m for m in ((p.get("media") or {}).get("nodes") or []) if m.get("image")]
            files = [{"originalSource": m["image"]["url"], "alt": m.get("alt") or "", "contentType": "IMAGE"} for m in media]
            known = {f["originalSource"] for f in files}

            def variant_file(v):
                nodes = ((v.get("media") or {}).get("nodes") or []) if isinstance(v.get("media"), dict) else []
                url = next((m["image"]["url"] for m in nodes if m.get("image")), None) or (v.get("image") or {}).get("url")
                if not url:
                    return None
                if url not in known:
                    files.append({"originalSource": url, "contentType": "IMAGE"})
                    known.add(url)
                return {"originalSource": url, "contentType": "IMAGE"}

            variants = []
            for v in vs:
                entry = {"optionValues": [{"optionName": s["name"], "name": s["value"]} for s in v["selectedOptions"]],
                         "price": v["price"], "compareAtPrice": v.get("compareAtPrice"), "sku": v.get("sku") or "",
                         "barcode": v.get("barcode") or "", "inventoryPolicy": v.get("inventoryPolicy") or "DENY",
                         "taxable": v.get("taxable", True)}
                vf = variant_file(v)
                if vf:
                    entry["file"] = vf
                variants.append(entry)
            body = {"handle": p["handle"], "title": p["title"], "descriptionHtml": p.get("descriptionHtml") or "",
                    "vendor": p.get("vendor") or "", "productType": p.get("productType") or "", "tags": p.get("tags") or [],
                    "status": p["status"], "seo": p.get("seo") or {},
                    "productOptions": [{"name": o["name"], "values": [{"name": x} for x in o["values"]]} for o in p.get("options") or []],
                    "files": files, "variants": variants}
            if p.get("templateSuffix"):
                body["templateSuffix"] = p["templateSuffix"]
            if not body["variants"]:
                body.pop("variants")
                body.pop("productOptions")
            try:
                node = self.call("product", {"i": body, "h": {"handle": p["handle"]}}, "productSet")
            except ShopifyError as e:
                self.note(f"product {p['handle']}: {e}")
                continue
            self.remember(p["id"], node["product"]["id"])
            new_by_title = {v["title"]: v["id"] for v in node["product"]["variants"]["nodes"]}
            for v in vs:
                self.remember(v["id"], new_by_title.get(v["title"]))
            if n % 20 == 0:
                print(f"    {n}/{len(products)}")
                self.save()
        if skipped:
            print(f"    {skipped} product(s) already copied, skipped (use --redo to copy again)")

    def collections(self):
        cols = self.load("collections")
        print(f"  {len(cols)} collections")
        if not self.apply:
            return
        for c in cols:
            body = {"handle": c["handle"], "title": c["title"], "descriptionHtml": c.get("descriptionHtml") or "",
                    "seo": c.get("seo") or {}, "sortOrder": c.get("sortOrder") or "BEST_SELLING"}
            if c.get("templateSuffix"):
                body["templateSuffix"] = c["templateSuffix"]
            if c.get("image"):
                body["image"] = {"src": c["image"]["url"], "altText": c["image"].get("altText") or ""}
            if c.get("ruleSet"):
                rules, dropped = [], []
                for r in c["ruleSet"].get("rules") or []:
                    rule = {"column": r["column"], "relation": r["relation"], "condition": r["condition"]}
                    if r["column"] in ("PRODUCT_METAFIELD_DEFINITION", "VARIANT_METAFIELD_DEFINITION"):
                        old_def = ((r.get("conditionObject") or {}).get("metafieldDefinition") or {}).get("id")
                        new_def = self.lookup(old_def) if old_def else None
                        if not new_def:
                            dropped.append(r["condition"])
                            continue
                        rule["conditionObjectId"] = new_def
                    rules.append(rule)
                if dropped:
                    self.note(f"collection {c['handle']}: {len(dropped)} metafield rule(s) dropped, their definition wasn't migrated")
                if not rules:
                    self.note(f"collection {c['handle']}: skipped, none of its rules could be carried across")
                    continue
                body["ruleSet"] = {"appliedDisjunctively": bool(c["ruleSet"].get("appliedDisjunctively")), "rules": rules}
            try:
                found = self.t.gql(M["coll_find"], {"h": c["handle"]})["collectionByIdentifier"]
                if found:
                    body["id"] = found["id"]
                    node = self.call("coll_update", {"i": body}, "collectionUpdate")
                else:
                    node = self.call("coll_create", {"i": body}, "collectionCreate")
                cid = node["collection"]["id"]
                self.remember(c["id"], cid)
                if not c.get("ruleSet"):
                    handles = [x["handle"] for x in (c.get("products") or {}).get("nodes", [])]
                    pids = [self.state["map"].get("Product", {}).get(pid) for pid in self._product_ids_for(handles)]
                    pids = [x for x in pids if x]
                    for i in range(0, len(pids), 250):
                        self.call("coll_add", {"id": cid, "p": pids[i:i + 250]}, "collectionAddProductsV2")
            except ShopifyError as e:
                self.note(f"collection {c['handle']}: {e}")

    def _product_ids_for(self, handles):
        if not hasattr(self, "_handle_index"):
            self._handle_index = {p["handle"]: GID.match(p["id"]).group(2) for p in self.load("products")}
        return [self._handle_index[h] for h in handles if h in self._handle_index]

    def _find(self, kind, handle):
        return (self.t.gql(M["find"], {"q": f"handle:{handle}"})[kind]["nodes"] or [None])[0]

    def pages(self):
        pages = self.load("pages")
        print(f"  {len(pages)} pages")
        if not self.apply:
            return
        for p in pages:
            try:
                found = self._find("pages", p["handle"])
                if found and found["handle"] == p["handle"]:
                    self.remember(p["id"], found["id"])
                    continue
                body = {"handle": p["handle"], "title": p["title"], "body": p.get("body") or "", "isPublished": p.get("isPublished", True)}
                if p.get("templateSuffix"):
                    body["templateSuffix"] = p["templateSuffix"]
                self.remember(p["id"], self.call("page", {"p": body}, "pageCreate")["page"]["id"])
            except ShopifyError as e:
                self.note(f"page {p['handle']}: {e}")

    def blogs(self):
        blogs = self.load("blogs")
        print(f"  {len(blogs)} blogs")
        if not self.apply:
            return
        for b in blogs:
            try:
                found = self._find("blogs", b["handle"])
                if found and found["handle"] == b["handle"]:
                    self.remember(b["id"], found["id"])
                    continue
                body = {"handle": b["handle"], "title": b["title"], "commentPolicy": b.get("commentPolicy") or "MODERATED"}
                if b.get("templateSuffix"):
                    body["templateSuffix"] = b["templateSuffix"]
                self.remember(b["id"], self.call("blog", {"b": body}, "blogCreate")["blog"]["id"])
            except ShopifyError as e:
                self.note(f"blog {b['handle']}: {e}")

    def articles(self):
        arts = self.load("articles")
        blog_ids = {b["handle"]: self.lookup(b["id"]) for b in self.load("blogs")}
        print(f"  {len(arts)} articles")
        if not self.apply:
            return
        for a in arts:
            blog = blog_ids.get((a.get("blog") or {}).get("handle"))
            if not blog:
                self.note(f"article {a['handle']}: its blog wasn't migrated")
                continue
            try:
                found = self._find("articles", a["handle"])
                if found and found["handle"] == a["handle"]:
                    self.remember(a["id"], found["id"])
                    continue
                body = {"blogId": blog, "handle": a["handle"], "title": a["title"], "body": a.get("body") or "",
                        "summary": a.get("summary") or "", "tags": a.get("tags") or [], "isPublished": a.get("isPublished", True),
                        "author": {"name": (a.get("author") or {}).get("name") or "Staff"}}
                if a.get("publishedAt"):
                    body["publishDate"] = a["publishedAt"]
                if a.get("image"):
                    body["image"] = {"url": a["image"]["url"], "altText": a["image"].get("altText") or ""}
                if a.get("templateSuffix"):
                    body["templateSuffix"] = a["templateSuffix"]
                self.remember(a["id"], self.call("article", {"a": body}, "articleCreate")["article"]["id"])
            except ShopifyError as e:
                self.note(f"article {a['handle']}: {e}")

    def metaobjects(self):
        mos = self.load("metaobjects")
        print(f"  {len(mos)} metaobject entries (two passes: values, then references)")
        if not self.apply:
            return
        for second in (False, True):
            for m in mos:
                fields = []
                for f in m["fields"]:
                    is_ref = "reference" in (f.get("type") or "")
                    if is_ref and not second:
                        continue
                    value = self.remap_value(f["type"], f["value"]) if is_ref else f["value"]
                    if value is not None:
                        fields.append({"key": f["key"], "value": value})
                if second and not any("reference" in (f.get("type") or "") for f in m["fields"]):
                    continue
                status = ((m.get("capabilities") or {}).get("publishable") or {}).get("status")
                body = {"fields": fields}
                if status:
                    body["capabilities"] = {"publishable": {"status": status}}
                try:
                    node = self.call("mo_upsert", {"h": {"type": m["type"], "handle": m["handle"]}, "m": body}, "metaobjectUpsert")
                    self.remember(m["id"], node["metaobject"]["id"])
                except ShopifyError as e:
                    self.note(f"metaobject {m['type']}/{m['handle']}: {e}")
            self.save()

    def metafields(self):
        owners = [("products", None), ("variants", None), ("collections", None), ("pages", None), ("blogs", None), ("articles", None)]
        rows = []
        for name, _ in owners:
            for item in self.load(name):
                mfs = item.get("metafields") or {}
                for mf in (mfs.get("nodes", []) if isinstance(mfs, dict) else mfs):
                    if skip_namespace(mf["namespace"]):
                        continue
                    rows.append((item["id"], mf))
        shop = self.load("shop")
        shop_mfs = ((shop or {}).get("shop") or {}).get("metafields", {}).get("nodes", []) if shop else []
        print(f"  {len(rows) + len(shop_mfs)} metafield values (references remapped)")
        if not self.apply:
            return
        shop_id = self.t.gql(M["existing"], {"o": "SHOP"})["shop"]["id"]
        batch = []
        def flush():
            if batch:
                try:
                    self.call("mf_set", {"m": list(batch)}, "metafieldsSet")
                except ShopifyError as e:
                    self.note(f"metafields batch: {e}")
                batch.clear()
        unmapped = 0
        for old_owner, mf in rows + [(None, m) for m in shop_mfs if not skip_namespace(m["namespace"])]:
            owner = shop_id if old_owner is None else self.lookup(old_owner)
            if not owner:
                unmapped += 1
                continue
            value = self.remap_value(mf["type"], mf["value"])
            if value in (None, ""):
                continue
            batch.append({"ownerId": owner, "namespace": mf["namespace"], "key": mf["key"], "type": mf["type"], "value": value})
            if len(batch) == 25:
                flush()
        flush()
        if unmapped:
            self.note(f"{unmapped} metafield value(s) skipped because their owner wasn't copied (run the owner's phase first)")

    def _menu_items(self, items):
        out = []
        for it in items or []:
            entry = {"title": it["title"], "type": it["type"]}
            if it.get("resourceId"):
                new = self.lookup(it["resourceId"])
                if new:
                    entry["resourceId"] = new
                else:
                    entry["type"], entry["url"] = "HTTP", it.get("url") or "/"
            elif it.get("url") and it["type"] == "HTTP":
                entry["url"] = it["url"]
            if it.get("tags"):
                entry["tags"] = it["tags"]
            if it.get("items"):
                entry["items"] = self._menu_items(it["items"])
            out.append(entry)
        return out

    def menus(self):
        menus = self.load("menus")
        print(f"  {len(menus)} menus")
        if not self.apply:
            return
        existing = {m["handle"]: m["id"] for m in self.t.gql(M["menus"])["menus"]["nodes"]}
        for m in menus:
            items = self._menu_items(m.get("items"))
            try:
                if m["handle"] in existing:
                    self.call("menu_update", {"id": existing[m["handle"]], "t": m["title"], "h": m["handle"], "i": items}, "menuUpdate")
                else:
                    self.call("menu_create", {"t": m["title"], "h": m["handle"], "i": items}, "menuCreate")
            except ShopifyError as e:
                self.note(f"menu {m['handle']}: {e}")

    def redirects(self):
        reds = self.load("redirects")
        print(f"  {len(reds)} redirects")
        if not self.apply:
            return
        for r in reds:
            try:
                self.call("redirect", {"r": {"path": r["path"], "target": r["target"]}}, "urlRedirectCreate")
            except ShopifyError as e:
                if "taken" not in str(e).lower() and "exists" not in str(e).lower():
                    self.note(f"redirect {r['path']}: {e}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--to", required=True, help="store alias from stores.json (role must be dev or staging)")
    ap.add_argument("--from", dest="run", help="export folder, default: latest complete export in docs/data/raw")
    ap.add_argument("--only", nargs="*", choices=PHASES)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--limit", type=int, help="copy only the first N products and N files")
    ap.add_argument("--redo", action="store_true", help="run every phase again, including products already copied")
    ap.add_argument("--reauth", action="store_true", help="ignore the saved token and get a new one")
    a = ap.parse_args()
    try:
        run = a.run or latest_run()
        target = Store(a.to)
        target.require_role(["dev", "staging"])
    except ShopifyError as e:
        die(str(e))
    summary_path = os.path.join(run, "summary.json")
    if not os.path.exists(summary_path):
        die(f"{run} has no summary.json. Point --from at a complete export.")
    summary = json.load(open(summary_path, encoding="utf-8"))
    if summary.get("partial"):
        print(f"Note: {run} is a partial export (--only {', '.join(summary.get('parts', []))}); only those parts can be copied.")
    if summary.get("shop") == target.shop:
        die("Refusing: the target is the store the export came from.")
    phrase = f"Approved: migrate {a.to} {target.shop}"
    print(f"{'APPLY' if a.apply else 'DRY RUN'}: {run} -> {target.shop} ({target.role})")
    if a.apply:
        require_approval(phrase)
        try:
            target.ensure_token(READ_SCOPES + MIGRATE_SCOPES, reauth=a.reauth)
            target.ensure_scopes(MIGRATE_SCOPES, READ_SCOPES + MIGRATE_SCOPES)
        except ShopifyError as e:
            die(str(e))
    mig = Migration(target, run, a.apply, a.limit, summary.get("shop"))
    mig.redo = a.redo
    failed = None
    try:
        for phase in PHASES:
            if a.only and phase not in a.only:
                continue
            if a.apply and not a.only and not a.redo and phase in mig.state["done"]:
                print(f"- {phase} (done earlier, skipped)")
                continue
            print(f"- {phase}")
            try:
                getattr(mig, phase)()
            except ShopifyError as e:
                failed = f"{phase}: {e}"
                mig.note(failed)
                break
            except Exception as e:  # noqa: BLE001 - keep the state and the issues list whatever happened
                failed = f"{phase}: {type(e).__name__}: {e}"
                mig.note(failed)
                break
            if a.apply and phase not in mig.state["done"]:
                mig.state["done"].append(phase)
            mig.save()
    finally:
        mig.save()
        if mig.log and a.apply:
            path = docs_path("data", "migrate", f"{target.alias}-issues.txt")
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "a", encoding="utf-8") as f:
                f.write("\n".join(mig.log) + "\n")
            print(f"\n{len(mig.log)} issue(s) noted, appended to {path}")
    if failed:
        die(f"Stopped at {failed}. Fix the cause and run again; finished phases are skipped.")
    if not a.apply:
        print(f"\nNothing was written. To run it, add this row to the approval log in docs/plan.md, then rerun with --apply:")
        print(f"  | {phrase} | YYYY-MM-DD | Jeet | |")


if __name__ == "__main__":
    main()
