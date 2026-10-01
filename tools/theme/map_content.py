#!/usr/bin/env python3
"""Carry merchant content from the old theme's templates into the new theme's sections.

Step 1, list what exists:
  python3 tools/theme/map_content.py --init --old docs/data/raw/<ts>/theme
  Writes docs/data/content-map.json with every old section type, its settings and block types, each mapped
  to null. Fill in the new section type and setting IDs for everything worth keeping.
Step 2, apply:
  python3 tools/theme/map_content.py --old docs/data/raw/<ts>/theme --out templates [--only index product]
  Writes new template JSON files with the old values under the new setting IDs, and
  docs/data/content-map-report.md listing everything that wasn't carried across.

Map entry shape:
  "image-with-text": {"to": "image-text", "settings": {"title": "heading", "text": "body"},
                      "blocks": {"button": {"to": "button", "settings": {"button_label": "label", "button_link": "link"}}}}
A section or setting mapped to null is dropped on purpose and not reported again.
"""
import argparse, glob, json, os, re


def strip_jsonc(raw):
    """Remove // and /* */ comments and trailing commas outside strings, so Shopify's theme JSON parses."""
    out, i, n, in_str = [], 0, len(raw), False
    while i < n:
        c = raw[i]
        if in_str:
            out.append(c)
            if c == "\\" and i + 1 < n:
                out.append(raw[i + 1])
                i += 2
                continue
            if c == '"':
                in_str = False
            i += 1
            continue
        if c == '"':
            in_str = True
            out.append(c)
            i += 1
        elif raw.startswith("//", i):
            j = raw.find("\n", i)
            i = n if j < 0 else j
        elif raw.startswith("/*", i):
            j = raw.find("*/", i + 2)
            i = n if j < 0 else j + 2
        elif c == ",":
            j = i + 1
            while j < n and raw[j] in " \t\r\n":
                j += 1
            if j < n and raw[j] in "}]":
                i += 1
            elif raw.startswith("//", j) or raw.startswith("/*", j):
                # a comment follows; decide after it
                k = j
                while True:
                    while k < n and raw[k] in " \t\r\n":
                        k += 1
                    if raw.startswith("//", k):
                        e = raw.find("\n", k)
                        k = n if e < 0 else e
                    elif raw.startswith("/*", k):
                        e = raw.find("*/", k + 2)
                        k = n if e < 0 else e + 2
                    else:
                        break
                if k < n and raw[k] in "}]":
                    i += 1
                else:
                    out.append(c)
                    i += 1
            else:
                out.append(c)
                i += 1
        else:
            out.append(c)
            i += 1
    return "".join(out)

def lenient(path):
    raw = open(path, encoding="utf-8").read()
    banner = re.match(r"\s*/\*.*?\*/\s*", raw, re.S)
    body = raw[banner.end():] if banner else raw
    return (banner.group(0) if banner else ""), json.loads(strip_jsonc(body))

def templates(old, only):
    for path in sorted(glob.glob(os.path.join(old, "templates", "*.json"))):
        name = os.path.basename(path)[:-5]
        if only and name.split(".")[0] not in only and name not in only:
            continue
        yield name, path

def init(old, only, out):
    found = {}
    for name, path in templates(old, only):
        _, data = lenient(path)
        for s in (data.get("sections") or {}).values():
            t = s.get("type", "")
            if t.startswith("shopify://apps/"):
                continue
            e = found.setdefault(t, {"to": None, "settings": {}, "blocks": {}, "_used_in": []})
            if name not in e["_used_in"]:
                e["_used_in"].append(name)
            for k in (s.get("settings") or {}):
                e["settings"].setdefault(k, None)
            for b in (s.get("blocks") or {}).values():
                be = e["blocks"].setdefault(b.get("type", ""), {"to": None, "settings": {}})
                for k in (b.get("settings") or {}):
                    be["settings"].setdefault(k, None)
    if os.path.exists(out):
        current = json.load(open(out))
        for t, e in found.items():
            if t in current:
                e["to"] = current[t].get("to")
                e["settings"].update({k: v for k, v in current[t].get("settings", {}).items()})
                for bt, be in current[t].get("blocks", {}).items():
                    if bt in e["blocks"]:
                        e["blocks"][bt]["to"] = be.get("to")
                        e["blocks"][bt]["settings"].update(be.get("settings", {}))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump({"sections": found}, open(out, "w"), indent=2)
    print(f"Wrote {out}: {len(found)} section types. Fill in 'to' and the setting IDs, then run without --init.")

def apply(old, only, mapping, out_dir, report):
    m = json.load(open(mapping))["sections"]
    lost, done = [], 0
    os.makedirs(out_dir, exist_ok=True)
    for name, path in templates(old, only):
        banner, data = lenient(path)
        new_sections, order = {}, []
        for sid in data.get("order") or list((data.get("sections") or {}).keys()):
            s = data["sections"][sid]
            t = s.get("type", "")
            if t.startswith("shopify://apps/"):
                lost.append(f"{name}: app block {t.split('/')[3]} (re-add from the app after launch, see the app migration plan)")
                continue
            entry = m.get(t)
            if not entry or not entry.get("to"):
                if entry is None or "to" not in entry:
                    lost.append(f"{name}: section '{t}' has no mapping")
                continue
            settings = {}
            for k, v in (s.get("settings") or {}).items():
                target = entry["settings"].get(k)
                if target:
                    settings[target] = v
                elif k not in entry["settings"] and v not in (None, "", False):
                    lost.append(f"{name}/{t}: setting '{k}' = {str(v)[:60]!r} not mapped")
            blocks, block_order = {}, []
            for bid in s.get("block_order") or list((s.get("blocks") or {}).keys()):
                b = s["blocks"][bid]
                be = (entry.get("blocks") or {}).get(b.get("type"))
                if not be or not be.get("to"):
                    if be is None:
                        lost.append(f"{name}/{t}: block '{b.get('type')}' has no mapping")
                    continue
                bs = {be["settings"][k]: v for k, v in (b.get("settings") or {}).items() if be["settings"].get(k)}
                blocks[bid] = {"type": be["to"], "settings": bs}
                if b.get("disabled"):
                    blocks[bid]["disabled"] = True
                block_order.append(bid)
            new = {"type": entry["to"], "settings": settings}
            if blocks:
                new["blocks"], new["block_order"] = blocks, block_order
            if s.get("disabled"):
                new["disabled"] = True
            new_sections[sid] = new
            order.append(sid)
        out = {"sections": new_sections, "order": order}
        for key in ("layout", "wrapper"):
            if key in data:
                out[key] = data[key]
        open(os.path.join(out_dir, f"{name}.json"), "w").write(banner + json.dumps(out, indent=2) + "\n")
        done += 1
    lines = ["# Content mapping report", "", f"{done} templates written to `{out_dir}`. Everything below was not carried across.", ""]
    lines += [f"- [ ] {x}" for x in lost] or ["Nothing lost."]
    open(report, "w").write("\n".join(lines) + "\n")
    print(f"{done} templates written, {len(lost)} item(s) not carried across. See {report}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--old", required=True)
    ap.add_argument("--init", action="store_true")
    ap.add_argument("--map", default="docs/data/content-map.json")
    ap.add_argument("--out", default="templates")
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--report", default="docs/data/content-map-report.md")
    a = ap.parse_args()
    if a.init:
        init(a.old, a.only, a.map)
    else:
        apply(a.old, a.only, a.map, a.out, a.report)

if __name__ == "__main__":
    main()
