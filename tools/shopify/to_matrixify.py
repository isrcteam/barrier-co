#!/usr/bin/env python3
"""Convert an export into Matrixify-shaped sheets, for review or for a Matrixify import route.

Usage: python3 tools/shopify/to_matrixify.py [docs/data/raw/<timestamp>] [--out docs/data/raw/<timestamp>/matrixify.xlsx]
Sheets: Products (one row per product, metafield columns), Metaobjects (Field/Value rows), Redirects.
Column names follow Matrixify's docs. Uses openpyxl if installed, otherwise writes one CSV per sheet.
Command is MERGE on every row. Review before importing anything.
"""
import argparse, csv, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shopify_client import ShopifyError, die, latest_run

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run", nargs="?")
    ap.add_argument("--out")
    a = ap.parse_args()
    try:
        run = a.run or latest_run()
    except ShopifyError as e:
        die(str(e))
    load = lambda n: json.load(open(os.path.join(run, f"{n}.json"), encoding="utf-8")) if os.path.exists(os.path.join(run, f"{n}.json")) else []
    products, metaobjects, redirects = load("products"), load("metaobjects"), load("redirects")

    mf_cols = sorted({(m["namespace"], m["key"], m["type"]) for p in products for m in (p.get("metafields") or {}).get("nodes", [])})
    header = ["ID", "Handle", "Command", "Title", "Status", "Template Suffix", "SEO Title", "SEO Description"] + \
             [f"Metafield: {ns}.{k} [{t}]" for ns, k, t in mf_cols]
    prows = []
    for p in products:
        vals = {(m["namespace"], m["key"]): m["value"] for m in (p.get("metafields") or {}).get("nodes", [])}
        prows.append([p["id"].split("/")[-1], p["handle"], "MERGE", p["title"], p["status"].title(), p.get("templateSuffix") or "",
                      (p.get("seo") or {}).get("title") or "", (p.get("seo") or {}).get("description") or ""] +
                     [vals.get((ns, k), "") for ns, k, _ in mf_cols])
    mrows = []
    for m in metaobjects:
        status = ((m.get("capabilities") or {}).get("publishable") or {}).get("status") or "ACTIVE"
        if not m["fields"]:
            mrows.append([m["id"].split("/")[-1], m["handle"], "MERGE", status.title(), m["type"], "", ""])
        for i, f in enumerate(m["fields"]):
            mrows.append([m["id"].split("/")[-1] if i == 0 else "", m["handle"], "MERGE" if i == 0 else "", status.title() if i == 0 else "",
                          m["type"], f["key"], f["value"] if f["value"] is not None else ""])
    sheets = {
        "Products": (header, prows),
        "Metaobjects": (["ID", "Handle", "Command", "Status", "Definition: Handle", "Field", "Value"], mrows),
        "Redirects": (["ID", "Path", "Target", "Command"], [[r["id"].split("/")[-1], r["path"], r["target"], "MERGE"] for r in redirects]),
    }
    try:
        import openpyxl
        out = a.out or os.path.join(run, "matrixify.xlsx")
        wb = openpyxl.Workbook()
        wb.remove(wb.active)
        for name, (h, rows) in sheets.items():
            ws = wb.create_sheet(name)
            ws.append(h)
            for r in rows:
                ws.append(r)
        wb.save(out)
        print(f"Wrote {out}")
    except ImportError:
        base = os.path.splitext(a.out)[0] if a.out else os.path.join(run, "matrixify")
        for name, (h, rows) in sheets.items():
            out = f"{base}-{name}.csv"
            with open(out, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(h)
                w.writerows(rows)
            print(f"Wrote {out} (install openpyxl for a single .xlsx)")
    print("Blank metafield cells delete values on import in Matrixify. Remove columns you don't intend to change.")

if __name__ == "__main__":
    main()
