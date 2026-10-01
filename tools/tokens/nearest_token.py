#!/usr/bin/env python3
"""Match raw Figma values to the nearest tokens and draft alignment report rows.

Usage: nearest_token.py tokens.json findings.csv
findings.csv columns: frame,element,property,value (hardcoded values only, not bound variables)
property: color | space | radius | font-size (anything else is matched against space)
Output: markdown table rows for the token alignment report. A proposal, not a decision.
"""
import csv, json, math, re, sys

def hex_to_lab(h):
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    def lin(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = lin(r), lin(g), lin(b)
    x = (r * 0.4124 + g * 0.3576 + b * 0.1805) / 0.95047
    y = r * 0.2126 + g * 0.7152 + b * 0.0722
    z = (r * 0.0193 + g * 0.1192 + b * 0.9505) / 1.08883
    def f(t):
        return t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116
    fx, fy, fz = f(x), f(y), f(z)
    return 116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)

def delta_e(a, b):
    return math.dist(hex_to_lab(a), hex_to_lab(b))

def resolve(t, v):
    m = re.fullmatch(r"\{([^}]+)\}", str(v))
    if not m:
        return v
    node = t
    for p in m.group(1).split("."):
        node = node[p]
    return resolve(t, node)

def main():
    t = json.load(open(sys.argv[1], encoding="utf-8"))
    colors = {f"color/palette/{k}": v for k, v in t.get("color", {}).get("palette", {}).items()}
    scales = {
        "space": t.get("space", {}),
        "radius": t.get("radius", {}),
        "font-size": {f"{r}-{bp}": s[bp]["size"] for r, s in t.get("type", {}).items() for bp in ("mobile", "desktop")},
    }
    print("| Frame | Element | Value used | Nearest token | Issue | Proposal | Question for |")
    print("| --- | --- | --- | --- | --- | --- | --- |")
    for row in csv.DictReader(open(sys.argv[2], encoding="utf-8")):
        prop, val = row["property"].strip().lower(), row["value"].strip()
        if prop == "color":
            name, tv = min(colors.items(), key=lambda kv: delta_e(val, kv[1]))
            d = delta_e(val, tv)
            if d < 0.5:
                issue, proposal, who = "Unbound, exact match", "Use token, designer to bind in Figma", "Designer"
            else:
                issue = f"Unbound, dE {d:.1f}"
                proposal, who = ("Merge into token", "Designer") if d < 3 else ("New token or ask", "Designer")
            nearest = f"{name} {tv}"
        else:
            scale = scales.get(prop, scales["space"])
            if not scale:
                continue
            num = float(re.sub(r"[^0-9.]", "", val) or 0)
            name, tv = min(scale.items(), key=lambda kv: abs(num - kv[1]))
            diff = abs(num - tv)
            if diff == 0:
                issue, proposal, who = "Unbound, on scale", "Use token, designer to bind in Figma", "Designer"
            else:
                issue = f"Off scale by {diff:g}px"
                proposal, who = ("Round to scale", "Designer") if diff <= 2 else ("New step or ask", "Designer")
            nearest = f"{prop}/{name} {tv}px"
        print(f"| {row['frame']} | {row['element']} | {val} | {nearest} | {issue} | {proposal} | {who} |")

if __name__ == "__main__":
    main()
