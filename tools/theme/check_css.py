#!/usr/bin/env python3
"""Check compiled theme CSS: no px outside media queries, theme.css under the gzip budget.

Usage: check_css.py <theme-root> [--budget-kb 14]
Scans assets/*.css and {% stylesheet %} blocks in sections/, blocks/ and snippets/.
Exit code 1 on any failure.
"""
import argparse, glob, gzip, os, re, sys

PX = re.compile(r"(?<![\w.-])(-?\d*\.?\d+)px\b")

def strip_comments(css):
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)

def px_outside_media(css):
    hits = []
    css = re.sub(r"@(media|container|supports)[^{]*\{", r"@\1 {", css)
    for lineno, line in enumerate(css.splitlines(), 1):
        for m in PX.finditer(line):
            if float(m.group(1)) == 0:
                continue
            hits.append((lineno, line.strip()[:120]))
            break
    return hits

def main():
    p = argparse.ArgumentParser()
    p.add_argument("root")
    p.add_argument("--budget-kb", type=float, default=14)
    a = p.parse_args()
    failures = 0

    sources = []
    for path in glob.glob(os.path.join(a.root, "assets", "*.css")):
        sources.append((path, open(path, encoding="utf-8", errors="ignore").read()))
    for folder in ("sections", "blocks", "snippets"):
        for path in glob.glob(os.path.join(a.root, folder, "*.liquid")):
            text = open(path, encoding="utf-8", errors="ignore").read()
            for block in re.findall(r"{%-?\s*stylesheet\s*-?%}(.*?){%-?\s*endstylesheet\s*-?%}", text, re.S):
                sources.append((path, block))

    for path, css in sources:
        for lineno, line in px_outside_media(strip_comments(css)):
            print(f"PX  {os.path.relpath(path, a.root)}:{lineno}  {line}")
            failures += 1

    theme_css = os.path.join(a.root, "assets", "theme.css")
    if os.path.exists(theme_css):
        size = len(gzip.compress(open(theme_css, "rb").read(), compresslevel=9)) / 1024
        status = "OK " if size <= a.budget_kb else "BUDGET"
        print(f"{status} assets/theme.css {size:.1f} KB gzip (budget {a.budget_kb:g} KB)")
        if size > a.budget_kb:
            failures += 1
    else:
        print("NOTE assets/theme.css not found, budget not checked. Run the build first.")

    print(f"\n{len(sources)} stylesheet sources checked, {failures} failure(s)")
    sys.exit(1 if failures else 0)

if __name__ == "__main__":
    main()
