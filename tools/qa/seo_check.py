#!/usr/bin/env python3
"""Check storefront URLs for core technical SEO issues, and optionally a redirect map.

Usage: seo_check.py urls.txt [--redirects redirects.csv]
urls.txt: one URL per line. Use the live or preview URL.
redirects.csv: columns old_url,new_url (full URLs or paths with --base).
Exit code 1 on any failure.
"""
import argparse, csv, json, re, sys, urllib.error, urllib.parse, urllib.request
from html.parser import HTMLParser

UA = {"User-Agent": "Mozilla/5.0 (iSourceit SEO check)"}

class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title, self.in_title = "", False
        self.meta_desc = None
        self.canonicals, self.robots, self.h1 = [], [], 0
        self.jsonld, self.in_ld, self.buf = [], False, ""
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "title":
            self.in_title = True
        elif tag == "meta" and a.get("name", "").lower() == "description":
            self.meta_desc = a.get("content", "")
        elif tag == "meta" and a.get("name", "").lower() == "robots":
            self.robots.append(a.get("content", "").lower())
        elif tag == "link" and a.get("rel", "").lower() == "canonical":
            self.canonicals.append(a.get("href", ""))
        elif tag == "h1":
            self.h1 += 1
        elif tag == "script" and a.get("type", "").lower() == "application/ld+json":
            self.in_ld, self.buf = True, ""
    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        elif tag == "script" and self.in_ld:
            self.jsonld.append(self.buf)
            self.in_ld = False
    def handle_data(self, data):
        if self.in_title:
            self.title += data
        if self.in_ld:
            self.buf += data

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None

def fetch(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status, r.read().decode("utf-8", errors="ignore")

def types_in(obj):
    if isinstance(obj, dict):
        t = obj.get("@type")
        if t:
            yield from (t if isinstance(t, list) else [t])
        for v in obj.values():
            yield from types_in(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from types_in(v)

def check_url(url):
    problems = []
    try:
        status, body = fetch(url)
    except urllib.error.HTTPError as e:
        return [f"HTTP {e.code}"]
    except Exception as e:
        return [f"fetch failed: {e}"]
    p = Page()
    p.feed(body)
    title = p.title.strip()
    if not title:
        problems.append("missing <title>")
    elif len(title) > 65:
        problems.append(f"title {len(title)} chars (over 65)")
    if not p.meta_desc:
        problems.append("missing meta description")
    if len(p.canonicals) != 1:
        problems.append(f"{len(p.canonicals)} canonical tags")
    elif "/collections/" in p.canonicals[0] and "/products/" in p.canonicals[0]:
        problems.append("canonical is collection-scoped product URL")
    if any("noindex" in r for r in p.robots):
        problems.append("noindex present (check this is intended)")
    if p.h1 != 1:
        problems.append(f"{p.h1} h1 elements")
    all_types = []
    for block in p.jsonld:
        try:
            all_types += list(types_in(json.loads(block)))
        except json.JSONDecodeError:
            problems.append("invalid JSON-LD block")
    if all_types.count("Product") > 1:
        problems.append(f"{all_types.count('Product')} Product JSON-LD blocks (duplicate owner?)")
    return problems, sorted(set(all_types))

def check_redirect(old, new):
    opener = urllib.request.build_opener(NoRedirect)
    try:
        opener.open(urllib.request.Request(old, headers=UA), timeout=30)
        return "no redirect (200)"
    except urllib.error.HTTPError as e:
        if e.code not in (301, 308):
            return f"HTTP {e.code}, expected 301"
        loc = urllib.parse.urljoin(old, e.headers.get("Location", ""))
        if loc.rstrip("/") != new.rstrip("/"):
            return f"redirects to {loc}, expected {new}"
        try:
            opener.open(urllib.request.Request(loc, headers=UA), timeout=30)
        except urllib.error.HTTPError as e2:
            if e2.code in (301, 302, 307, 308):
                return f"redirect chain via {loc}"
            return f"target returns HTTP {e2.code}"
    return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("urls")
    ap.add_argument("--redirects")
    ap.add_argument("--base", default="")
    a = ap.parse_args()
    failures = 0
    for url in [u.strip() for u in open(a.urls) if u.strip() and not u.startswith("#")]:
        result = check_url(url)
        if isinstance(result, list):
            problems, types = result, []
        else:
            problems, types = result
        print(f"{'FAIL' if problems else 'OK  '} {url}  [{', '.join(types) or 'no JSON-LD'}]")
        for pr in problems:
            print(f"      - {pr}")
        failures += bool(problems)
    if a.redirects:
        rows = list(csv.DictReader(open(a.redirects)))
        for row in rows:
            old = urllib.parse.urljoin(a.base, row["old_url"])
            new = urllib.parse.urljoin(a.base, row["new_url"])
            issue = check_redirect(old, new)
            if issue:
                print(f"FAIL redirect {old}: {issue}")
                failures += 1
        print(f"{len(rows)} redirects checked")
    sys.exit(1 if failures else 0)

if __name__ == "__main__":
    main()
