#!/usr/bin/env python3
"""Audit SEO titles, meta descriptions and image alt text from an export, and draft recommendations.

Usage: python3 tools/shopify/seo_audit.py [docs/data/raw/<timestamp>] [--brand "Brand"] [--out docs/seo/seo-review.csv]
Checks published products, collections, pages and articles, plus product image alt text:
  missing, too long (title > 60, description > 160), too short (title < 20, description < 70),
  duplicated across records, description identical to the title, alt text missing.
Flagged fields get a draft in Recommended, built from the record's own content, where there's enough
content to draft from. A blank Recommended means it needs writing. Drafts are a starting point: rewrite
them properly before the client sees the sheet.
Approve is pre-filled Y only where the current value is empty AND the draft meets the length rules.
Image alt rows are never pre-approved: a generic "Product name, view 3" isn't worth writing to the store.
Replacing an existing value needs the client to put Y in Approve themselves.
"""
import argparse, collections, csv, html, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shopify_client import ShopifyError, die, docs_path, latest_run

TITLE_MAX, TITLE_MIN, DESC_MAX, DESC_MIN = 60, 20, 160, 70

def strip(h):
    t = re.sub(r"<[^>]+>", " ", h or "")
    return re.sub(r"\s+", " ", html.unescape(t)).strip()

def cut(text, limit):
    """Cut at a word boundary. No ellipsis: search engines show one anyway when they truncate."""
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0].rstrip(",;:-")

def draft_title(name, brand):
    name = name.strip()
    if brand and name.lower().endswith(brand.lower()):
        return cut(name, TITLE_MAX)
    suffix = f" | {brand}" if brand else ""
    if len(name) + len(suffix) <= TITLE_MAX:
        return name + suffix
    return cut(name, TITLE_MAX)

def title_ok(t):
    return TITLE_MIN <= len(t) <= TITLE_MAX

def desc_ok(d):
    return DESC_MIN <= len(d) <= DESC_MAX

def draft_desc(body, fallback):
    text = strip(body) or fallback
    sentences = re.split(r"(?<=[.!?])\s+", text)
    out = ""
    for s in sentences:
        if len(out) + len(s) + 1 > 155:
            break
        out = (out + " " + s).strip()
    out = out if len(out) >= DESC_MIN else cut(text, 155)
    return out if len(out) >= 50 else ""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run", nargs="?")
    ap.add_argument("--brand", default="")
    ap.add_argument("--out", default=docs_path("seo", "seo-review.csv"))
    a = ap.parse_args()
    try:
        run = a.run or latest_run()
    except ShopifyError as e:
        die(str(e))
    load = lambda n: json.load(open(os.path.join(run, f"{n}.json"), encoding="utf-8")) if os.path.exists(os.path.join(run, f"{n}.json")) else []
    shop = load("shop")
    brand = a.brand or (((shop or {}).get("shop") or {}).get("name", "") if isinstance(shop, dict) else "")

    records = []
    for p in load("products"):
        if p.get("status") == "ACTIVE":
            records.append(("product", p["handle"], p["id"], p["title"], (p.get("seo") or {}).get("title"), (p.get("seo") or {}).get("description"), p.get("descriptionHtml")))
    for c in load("collections"):
        records.append(("collection", c["handle"], c["id"], c["title"], (c.get("seo") or {}).get("title"), (c.get("seo") or {}).get("description"), c.get("descriptionHtml")))
    for pg in load("pages"):
        if pg.get("isPublished", True):
            records.append(("page", pg["handle"], pg["id"], pg["title"], (pg.get("seoTitle") or {}).get("value"), (pg.get("seoDescription") or {}).get("value"), pg.get("body")))
    for ar in load("articles"):
        if ar.get("isPublished", True):
            records.append(("article", f"{(ar.get('blog') or {}).get('handle')}/{ar['handle']}", ar["id"], ar["title"],
                            (ar.get("seoTitle") or {}).get("value"), (ar.get("seoDescription") or {}).get("value"), ar.get("summary") or ar.get("body")))

    titles = collections.Counter((r[4] or r[3]).strip().lower() for r in records)
    descs = collections.Counter((r[5] or "").strip().lower() for r in records if r[5])
    rows, counts = [], collections.Counter()
    for kind, handle, gid, name, st, sd, body in records:
        effective = (st or "").strip()
        issues = []
        if not effective:
            issues.append("missing (falls back to the page name)")
        elif len(effective) > TITLE_MAX:
            issues.append(f"too long ({len(effective)} chars)")
        elif len(effective) < TITLE_MIN:
            issues.append(f"too short ({len(effective)} chars)")
        if titles[(st or name).strip().lower()] > 1:
            issues.append(f"duplicate of {titles[(st or name).strip().lower()] - 1} other(s)")
        if issues:
            draft = draft_title(name, brand)
            draft = "" if draft == effective else draft
            rows.append([kind, handle, gid, "title", st or "", "; ".join(issues), draft, "", "Y" if not st and draft and title_ok(draft) else ""])
            counts["title"] += 1
        d = (sd or "").strip()
        issues = []
        if not d:
            issues.append("missing")
        elif len(d) > DESC_MAX:
            issues.append(f"too long ({len(d)} chars)")
        elif len(d) < DESC_MIN:
            issues.append(f"too short ({len(d)} chars)")
        if d and descs[d.lower()] > 1:
            issues.append(f"duplicate of {descs[d.lower()] - 1} other(s)")
        if d and d.lower() == (st or name).strip().lower():
            issues.append("same as the title")
        if issues:
            draft = draft_desc(body, name)
            rows.append([kind, handle, gid, "description", sd or "", "; ".join(issues), draft, "", "Y" if not d and draft and desc_ok(draft) else ""])
            counts["description"] += 1
    for p in load("products"):
        if p.get("status") != "ACTIVE":
            continue
        for i, m in enumerate(((p.get("media") or {}).get("nodes") or []), 1):
            if m.get("image") and not (m.get("alt") or "").strip():
                rows.append(["image", p["handle"], m["id"], "alt", "", "missing alt text", f"{p['title']}" + (f", view {i}" if i > 1 else ""), "", ""])
                counts["alt"] += 1

    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    with open(a.out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["Type", "Handle", "ID", "Field", "Current", "Issue", "Recommended", "Reason", "Approve"])
        w.writerows(rows)
    total = len(records)
    print(f"Audited {total} records from {run}. Flagged: {counts['title']} titles, {counts['description']} descriptions, {counts['alt']} images without alt text.")
    pre = sum(1 for r in rows if r[-1] == "Y")
    print(f"Wrote {a.out}. {pre} row(s) pre-approved (empty today and the draft meets the length rules); alt text rows are never pre-approved.")
    print("Rewrite the drafts in Recommended and fill Reason before sending it to the client.")
    print("Not covered by the API export: the home page title and description (Online Store > Preferences). Check them by hand.")

if __name__ == "__main__":
    main()
