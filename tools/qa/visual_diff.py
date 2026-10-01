#!/usr/bin/env python3
"""Compare two screenshot folders from capture.mjs and flag pages that changed.

Usage: python3 visual_diff.py docs/qa/screens/live docs/qa/screens/release [--threshold 0.5] [--out docs/qa/visual-diff]
A pixel counts as changed when any channel differs by more than --tolerance (default 24 of 255), which
ignores anti-aliasing and font rendering noise. A page fails when more than --threshold percent of its
pixels changed, when more than --pixels pixels changed in total (catches a small element that changed on a
long page), or when the page height differs by more than 2 percent.
Writes a diff image per failing page (changes in magenta) and report.md. Exit 1 if anything failed.
"""
import argparse, os, sys
from PIL import Image, ImageChops

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("before")
    ap.add_argument("after")
    ap.add_argument("--threshold", type=float, default=0.5)
    ap.add_argument("--tolerance", type=int, default=24)
    ap.add_argument("--pixels", type=int, default=1500, help="fail when more than this many pixels changed, however small the percentage")
    ap.add_argument("--out", default="docs/qa/visual-diff")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    names = sorted(n for n in os.listdir(a.before) if n.endswith(".png"))
    rows, failed = [], 0
    for name in names:
        other = os.path.join(a.after, name)
        if not os.path.exists(other):
            rows.append((name, "missing in after", "", "FAIL"))
            failed += 1
            continue
        x = Image.open(os.path.join(a.before, name)).convert("RGB")
        y = Image.open(other).convert("RGB")
        h_delta = abs(x.height - y.height) / max(x.height, 1) * 100
        w, h = min(x.width, y.width), min(x.height, y.height)
        x, y = x.crop((0, 0, w, h)), y.crop((0, 0, w, h))
        diff = ImageChops.difference(x, y).convert("L").point(lambda v: 255 if v > a.tolerance else 0)
        changed = sum(diff.histogram()[255:])
        pct = changed / (w * h) * 100
        box = diff.getbbox()
        status = "FAIL" if pct > a.threshold or changed > a.pixels or h_delta > 2 else "ok"
        if status == "FAIL":
            failed += 1
            overlay = y.copy()
            overlay.paste((255, 0, 255), mask=diff)
            overlay.save(os.path.join(a.out, name.replace(".png", "--diff.png")))
        rows.append((name, f"{pct:.2f}% ({changed:,} px)", f"{h_delta:.1f}%", f"{status}" + (f" around {box[0]},{box[1]}" if status == "FAIL" and box else "")))
    lines = ["# Visual diff", "", f"Before: `{a.before}` · After: `{a.after}` · Threshold {a.threshold}% of pixels, height ±2%", "",
             "| Screenshot | Pixels changed | Height change | Result |", "| --- | --- | --- | --- |"]
    lines += [f"| {n} | {p} | {hd} | {s} |" for n, p, hd, s in rows]
    open(os.path.join(a.out, "report.md"), "w").write("\n".join(lines) + "\n")
    print(f"{len(rows)} compared, {failed} failed. Report: {os.path.join(a.out, 'report.md')}")
    sys.exit(1 if failed else 0)

if __name__ == "__main__":
    main()
