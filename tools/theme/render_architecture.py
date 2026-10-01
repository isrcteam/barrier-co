#!/usr/bin/env python3
"""Render docs/architecture.md to a self-contained HTML file in Roboto Mono.

Usage: render_architecture.py docs/architecture.md docs/architecture.html
Local images are embedded as data URIs so the HTML can be shared on its own.
Requires: pip install markdown
"""
import base64, mimetypes, os, re, sys
try:
    import markdown
except ImportError:
    sys.exit("pip install markdown --break-system-packages")

CSS = """
:root{--paper:#fff;--ink:#16201c;--muted:#5a6862;--rule:#d5ddd8;--soft:#eef2ef;--accent:#0b6b4f;color-scheme:light}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font:0.875rem/1.7 "Roboto Mono",ui-monospace,Menlo,Consolas,monospace}
main{max-width:60rem;margin:0 auto;padding:3rem 1.25rem 6rem}
h1{font-size:1.75rem;font-weight:500;letter-spacing:-0.02em;line-height:1.2}
h2{font-size:1.25rem;font-weight:500;margin:3.5rem 0 1rem;padding-top:1.5rem;border-top:1px solid var(--rule)}
h3{font-size:1rem;font-weight:700;margin:2.5rem 0 0.75rem}
a{color:var(--accent)}
img{max-width:100%;height:auto;border:1px solid var(--rule);border-radius:4px;margin:0.5rem 0.5rem 0.5rem 0;vertical-align:top}
code{font-family:inherit;background:var(--soft);padding:0.1em 0.35em;border-radius:3px}
table{border-collapse:collapse;width:100%;font-size:0.8125rem;display:block;overflow-x:auto}
th,td{text-align:left;vertical-align:top;padding:0.5rem 0.7rem;border-bottom:1px solid var(--rule)}
th{background:var(--soft)}
"""

def embed(match, base):
    alt, src = match.group(1), match.group(2)
    path = os.path.join(base, src)
    if src.startswith(("http://", "https://", "data:")) or not os.path.exists(path):
        return match.group(0)
    mime = mimetypes.guess_type(path)[0] or "image/png"
    data = base64.b64encode(open(path, "rb").read()).decode()
    return f"![{alt}](data:{mime};base64,{data})"

def main():
    src, out = sys.argv[1], sys.argv[2]
    text = open(src, encoding="utf-8").read()
    text = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", lambda m: embed(m, os.path.dirname(src)), text)
    body = markdown.markdown(text, extensions=["tables", "fenced_code", "toc"])
    title = re.search(r"^# (.+)$", text, re.M)
    page = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title.group(1) if title else 'Project Architecture'}</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;500;700&display=swap" rel="stylesheet">
<style>{CSS}</style></head><body><main>{body}</main></body></html>"""
    open(out, "w", encoding="utf-8").write(page)
    print(f"Wrote {out}")

if __name__ == "__main__":
    main()
