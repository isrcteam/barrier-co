#!/usr/bin/env python3
"""Build the checkout and brand settings sheet from docs/tokens.json.

Usage: python3 checkout_sheet.py [docs/tokens.json] [--scheme scheme-1] [--out docs/assets/checkout-settings.md]
Maps the default scheme's roles to Shopify's checkout editor fields and Settings > Brand, and checks the
contrast of every text-on-background pair (WCAG AA: 4.5 for text, 3 for large text and UI).
A failing pair is reported with its measured ratio. The colour is never changed: it's a question for the designer.
"""
import argparse, json, os, re

def lum(hexv):
    h = hexv.lstrip("#")
    h = "".join(c * 2 for c in h) if len(h) == 3 else h[:6]
    def ch(c):
        c = int(c, 16) / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(h[i:i + 2]) for i in (0, 2, 4))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def ratio(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tokens", nargs="?", default="docs/tokens.json")
    ap.add_argument("--scheme")
    ap.add_argument("--out", default="docs/assets/checkout-settings.md")
    a = ap.parse_args()
    t = json.load(open(a.tokens))
    c = t["color"]
    sid = a.scheme or next(iter(c["schemes"]))
    s = c["schemes"][sid]
    rm = c["role_map"]
    def col(role):
        ref = s[role].strip("{}").split(".")[-1]
        return ref, c["palette"][ref].upper()
    bg, text, btn, btn_label = col(rm["background"]), col(rm["text"]), col(rm["primary_button"]), col(rm["on_primary_button"])
    link = col(rm["links"])
    def font_name(f):
        if isinstance(f, dict):
            return f"{f['family']} (Shopify font library)" if f.get("source") == "shopify" else f.get("stack", "")
        return f
    fonts = {k: font_name(v) for k, v in t.get("font", {}).get("family", {}).items()}
    radius = t.get("radius", {})
    rows = [
        ("Checkout › Colors › Main area background", bg),
        ("Checkout › Colors › Main area text", text),
        ("Checkout › Colors › Order summary background", bg),
        ("Checkout › Colors › Accent (links, focus)", link),
        ("Checkout › Colors › Buttons", btn),
        ("Checkout › Colors › Button text", btn_label),
        ("Settings › Brand › Primary colour", btn),
        ("Settings › Brand › Contrasting colour", btn_label),
    ]
    L = ["# Checkout and brand settings", "", f"From `{a.tokens}`, scheme `{sid}` ({s['name']}). Enter these by hand in the checkout editor and Settings › Brand.", "",
         "| Field | Palette colour | Value |", "| --- | --- | --- |"]
    L += [f"| {f} | {name} | `{hexv}` |" for f, (name, hexv) in rows]
    L += ["", "## Type and shape", "", "| Field | Value | Note |", "| --- | --- | --- |",
          f"| Checkout › Typography › Headings | {fonts.get('heading', '')} | Checkout only offers Shopify's font library. A library font is picked as it is; for a self-hosted brand font pick the closest and note it here |",
          f"| Checkout › Typography › Body | {fonts.get('body', '')} | Same |",
          f"| Checkout › Corner radius | {'Small' if (radius.get('sm', 0) or 0) <= 4 else 'Large'} | From radius tokens: {', '.join(f'{k} {v}px' for k, v in radius.items())} |",
          "", "## Logo", "", "| Where | File | Size |", "| --- | --- | --- |",
          "| Checkout › Logo | `logo-checkout-400.png` | Small, medium or large per design |",
          "| Settings › Brand › Logo | `logo-default-1024.png` | |",
          "| Settings › Brand › Square logo | `icon-512.png` | From favicons.py |",
          "| Settings › Brand › Cover image | `brand-cover-1920x1080.jpg` | |",
          "", "## Contrast", "", "| Pair | Ratio | AA text 4.5 | AA large/UI 3 |", "| --- | --- | --- | --- |"]
    fails = []
    for label, fg, bgc in (("Text on background", text, bg), ("Button text on button", btn_label, btn), ("Links on background", link, bg)):
        r = ratio(fg[1], bgc[1])
        ok, ok3 = r >= 4.5, r >= 3
        L.append(f"| {label} ({fg[0]} on {bgc[0]}) | {r:.2f}:1 | {'pass' if ok else 'FAIL'} | {'pass' if ok3 else 'FAIL'} |")
        if not ok:
            fails.append(f"{label}: {fg[1]} on {bgc[1]} measures {r:.2f}:1")
    if fails:
        L += ["", "## Questions for the designer", ""] + [f"- {x}. Keep, or adjust? (Colour not changed.)" for x in fails]
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    open(a.out, "w").write("\n".join(L) + "\n")
    print(f"Wrote {a.out}" + (f" with {len(fails)} contrast question(s)" if fails else ""))

if __name__ == "__main__":
    main()
