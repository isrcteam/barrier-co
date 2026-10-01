#!/usr/bin/env python3
"""Build the theme's token layer from docs/tokens.json. Every value is defined once.

Writes:
  src/scss/lib/_variables.scss        colours as CSS variables, everything else via pxtorem()
  src/scss/lib/_typography.scss       type role mixins
  src/scss/lib/global/_breakpoints.scss
  snippets/color-schemes.liquid       CSS variables from the merchant's colour schemes
  config/settings_schema.json         colour scheme group + fixed colours (merged, other settings kept)
  config/settings_data.json           scheme values (protected once the store has edited them)
  locales/en.default.schema.json      labels for the generated settings
  snippets/fonts.liquid               font_face, preload and --font-* variables for Shopify-library fonts
  docs/tokens.lock.json               what was last generated, for change detection
  --reference <file>                  token reference page

Usage: build_tokens.py [docs/tokens.json] [--theme .] [--reference docs/token-reference.html]
       [--scss-only] [--overwrite-store-changes]
"""
import argparse, copy, hashlib, html, json, os, re, sys

REQUIRED_SHOPIFY_ROLES = ["background", "text", "primary_button", "on_primary_button", "primary_button_border",
                          "secondary_button", "on_secondary_button", "secondary_button_border", "links", "icons"]
REF = re.compile(r"\{([^}]+)\}")
# Where a stock theme keeps its own font settings, for --scss-only builds that use Shopify-library fonts
HOST_FONT_VARS = {"horizon": {"heading": "--font-heading--family", "body": "--font-body--family"},
                  "dawn": {"heading": "--font-heading-family", "body": "--font-body-family"}}
HEX = re.compile(r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})\b")



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

def fail(msg):
    sys.exit(f"tokens.json: {msg}")


def lookup(t, path):
    node = t
    for part in path.split("."):
        if not isinstance(node, dict) or part not in node:
            fail(f"unknown reference {{{path}}}")
        node = node[part]
    return node


def resolve(t, v, depth=0):
    if isinstance(v, str):
        m = REF.fullmatch(v.strip())
        if m:
            if depth > 10:
                fail(f"reference loop at {v}")
            return resolve(t, lookup(t, m.group(1)), depth + 1)
    return v


def kebab(s):
    return s.replace("_", "-")


def norm_hex(v):
    v = v.lower()
    if len(v) == 4:
        v = "#" + "".join(c * 2 for c in v[1:])
    return v


def scss_ref(path):
    parts = path.split(".")
    return "$" + "-".join(kebab(p) for p in parts)


def lenient_loads(raw):
    return json.loads(strip_jsonc(raw))


def load_json_with_banner(path):
    raw = open(path, encoding="utf-8").read()
    banner = ""
    m = re.match(r"\s*/\*.*?\*/\s*", raw, re.S)
    if m:
        banner, raw = m.group(0), raw[m.end():]
    return banner, lenient_loads(raw)


def validate(t):
    c = t.get("color") or fail("missing color")
    palette = c.get("palette") or fail("missing color.palette")
    seen = {}
    for name, v in palette.items():
        if not isinstance(v, str) or not HEX.fullmatch(v):
            fail(f"color.palette.{name} must be a hex value, got {v!r}")
        n = norm_hex(v)
        if n in seen:
            fail(f"color.palette.{name} repeats {v}, already defined as color.palette.{seen[n]}. Define each colour once.")
        seen[n] = name
    roles = c.get("roles") or fail("missing color.roles")
    for rid in roles:
        if not re.fullmatch(r"[a-z][a-z0-9_]*", rid):
            fail(f"role id {rid!r} must be snake_case")
    role_map = c.get("role_map") or fail("missing color.role_map")
    for r in REQUIRED_SHOPIFY_ROLES:
        if r not in role_map:
            fail(f"color.role_map needs '{r}' (Shopify requires it for scheme previews)")
        if role_map[r] not in roles:
            fail(f"color.role_map.{r} points to unknown role '{role_map[r]}'")
    schemes = c.get("schemes") or fail("missing color.schemes")
    for sid, s in schemes.items():
        if "name" not in s:
            fail(f"color.schemes.{sid} needs a name")
        for rid in roles:
            if rid not in s:
                fail(f"color.schemes.{sid} is missing role '{rid}'")
            v = s[rid]
            if not (isinstance(v, str) and REF.fullmatch(v) and v.strip("{}").startswith("color.palette.")):
                fail(f"color.schemes.{sid}.{rid} must reference the palette, like {{color.palette.ink}}, not {v!r}")
            lookup(t, v.strip("{}"))
    for fid, f in (c.get("fixed") or {}).items():
        v = f.get("value", "")
        if not (REF.fullmatch(v) and v.strip("{}").startswith("color.palette.")):
            fail(f"color.fixed.{fid}.value must reference the palette")
    if "desktop" not in t.get("breakpoint", {}):
        fail("breakpoint.desktop is required")
    weights = t.get("font", {}).get("weight", {})
    for name, f in (t.get("font", {}).get("family") or {}).items():
        if isinstance(f, str):
            continue
        if not isinstance(f, dict) or f.get("source") not in ("shopify", "self"):
            fail(f"font.family.{name} must be a CSS font stack, or an object with source 'shopify' or 'self'")
        if f["source"] == "shopify":
            if not isinstance(f.get("family"), str) or not f["family"].strip():
                fail(f"font.family.{name}.family must name a font from Shopify's library, like 'Assistant'")
            ws = f.get("weights") or [400]
            if not all(isinstance(w, int) and 100 <= w <= 900 and w % 100 == 0 for w in ws):
                fail(f"font.family.{name}.weights must be numbers like 400 and 700")
            used = {weights.get(spec.get("weight")) for spec in t.get("type", {}).values() if spec.get("family") == name}
            missing = sorted(w for w in used if isinstance(w, int) and w not in ws)
            if missing:
                fail(f"type roles use weight(s) {', '.join(map(str, missing))} of font.family.{name}, which lists {ws}. Add the weight (if the library has it) or change the role.")
        elif not isinstance(f.get("stack"), str):
            fail(f"font.family.{name} with source 'self' needs a 'stack', the CSS font-family value")


def size(t, v):
    if isinstance(v, str) and REF.fullmatch(v.strip()):
        return scss_ref(v.strip("{} "))
    if isinstance(v, (int, float)):
        return f"pxtorem({v})"
    return v


def build_variables(t, host=None):
    c = t["color"]
    out = ["@use 'global/functions' as *;", ""]
    for rid in c["roles"]:
        out.append(f"$color-{kebab(rid)}: var(--color-{kebab(rid)});")
    for fid in c.get("fixed") or {}:
        out.append(f"$color-{kebab(fid)}: var(--color-{kebab(fid)});")
    out.append("")
    for group in ("space", "layout", "radius", "border", "icon"):
        for name, v in t.get(group, {}).items():
            out.append(f"${group}-{kebab(name)}: {size(t, v)};")
    for name, v in t.get("z", {}).items():
        out.append(f"$z-{kebab(name)}: {v};")
    for name, v in t.get("motion", {}).get("duration", {}).items():
        out.append(f"$duration-{kebab(name)}: {v};")
    for name, v in t.get("motion", {}).get("easing", {}).items():
        out.append(f"$easing-{kebab(name)}: {v};")
    for name, v in t.get("font", {}).get("family", {}).items():
        out.append(f"$font-family-{kebab(name)}: {font_stack(name, v, host)};")
    for name, v in t.get("font", {}).get("weight", {}).items():
        out.append(f"$font-weight-{kebab(name)}: {v};")
    return "\n".join(out) + "\n"


def em(n):
    return "0" if n == 0 else f"{n}em"


def shopify_fonts(t):
    """{name: entry} for font.family entries served from Shopify's font library."""
    return {n: f for n, f in (t.get("font", {}).get("family") or {}).items() if isinstance(f, dict) and f.get("source") == "shopify"}


def font_setting_id(name, f):
    return f.get("setting") or f"type_{kebab(name).replace('-', '_')}_font"


def font_handle(f):
    """Shopify font handle: family, then n (normal) or i (italic) and the weight's hundreds digit, e.g. assistant_n4."""
    ws = f.get("weights") or [400]
    base = 400 if 400 in ws else min(ws)
    style = "i" if f.get("style") == "italic" else "n"
    return re.sub(r"[^a-z0-9]+", "_", f["family"].strip().lower()).strip("_") + f"_{style}{base // 100}"


def font_stack(name, f, host=None):
    """What $font-family-<name> compiles to."""
    if isinstance(f, str):
        return f
    if f.get("source") == "self":
        return f["stack"]
    if host:
        mapping = HOST_FONT_VARS.get(host, {})
        if name not in mapping:
            fail(f"on {host.capitalize()}, a Shopify-library font maps to the host theme's own font settings, which cover 'heading' and 'body'. "
                 f"Name font.family.{name} one of those, or give it a self-hosted stack.")
        return f"var({mapping[name]})"
    return f"var(--font-{kebab(name)})"


def build_fonts_snippet(t):
    """snippets/fonts.liquid: font_face for every weight, a preload for the base file, and --font-<name> variables."""
    fonts = shopify_fonts(t)
    if not fonts:
        return ""  # theme.liquid renders the snippet either way; empty when every font is self-hosted
    lines = ["{%- liquid"]
    for name, f in fonts.items():
        var = kebab(name).replace("-", "_")
        lines.append(f"  assign {var}_font = settings.{font_setting_id(name, f)}")
        base = 400 if 400 in (f.get("weights") or [400]) else min(f.get("weights") or [400])
        for w in sorted(f.get("weights") or [400]):
            if w != base:
                lines.append(f"  assign {var}_font_{w} = {var}_font | font_modify: 'weight', '{w}'")
    lines.append("-%}")
    for name, f in fonts.items():
        var = kebab(name).replace("-", "_")
        lines.append(f"{{{{ {var}_font | font_url | preload_tag: as: 'font', type: 'font/woff2', crossorigin: 'anonymous' }}}}")
    lines.append("{%- style -%}")
    for name, f in fonts.items():
        var = kebab(name).replace("-", "_")
        base = 400 if 400 in (f.get("weights") or [400]) else min(f.get("weights") or [400])
        lines.append(f"  {{{{ {var}_font | font_face: font_display: 'swap' }}}}")
        for w in sorted(f.get("weights") or [400]):
            if w != base:
                lines.append(f"  {{%- if {var}_font_{w} -%}}{{{{ {var}_font_{w} | font_face: font_display: 'swap' }}}}{{%- endif -%}}")
    lines.append("  :root {")
    for name, f in fonts.items():
        var = kebab(name).replace("-", "_")
        lines.append(f"    --font-{kebab(name)}: {{{{ {var}_font.family }}}}, {{{{ {var}_font.fallback_families }}}};")
    lines += ["  }", "{%- endstyle -%}"]
    return "\n".join(lines) + "\n"


def typography_group(t):
    fonts = shopify_fonts(t)
    settings = [{"type": "font_picker", "id": font_setting_id(n, f), "label": f"t:settings_schema.typography.{font_setting_id(n, f)}",
                 "default": font_handle(f)} for n, f in fonts.items()]
    return {"name": "t:settings_schema.typography.name", "settings": settings}


def build_typography(t):
    out = ["@use 'global/functions' as *;", "@use 'global/breakpoints' as *;", "@use 'variables' as *;", ""]
    fams, wts = t.get("font", {}).get("family", {}), t.get("font", {}).get("weight", {})
    for role, spec in t.get("type", {}).items():
        if spec.get("family") not in fams:
            fail(f"type.{role}.family '{spec.get('family')}' isn't in font.family ({', '.join(fams) or 'empty'})")
        if spec.get("weight") not in wts:
            fail(f"type.{role}.weight '{spec.get('weight')}' isn't in font.weight ({', '.join(wts) or 'empty'})")
        for bp in ("mobile", "desktop"):
            if not isinstance(spec.get(bp), dict) or not all(k in spec[bp] for k in ("size", "line", "tracking")):
                fail(f"type.{role}.{bp} needs size, line and tracking")
        m, d = spec["mobile"], spec["desktop"]
        out += [f"@mixin type-{kebab(role)} {{",
                f"  font-family: $font-family-{kebab(spec['family'])};",
                f"  font-weight: $font-weight-{kebab(spec['weight'])};",
                f"  font-size: pxtorem({m['size']});",
                f"  line-height: {m['line']};",
                f"  letter-spacing: {em(m['tracking'])};"]
        changes = [f"    font-size: pxtorem({d['size']});"] if d["size"] != m["size"] else []
        if d["line"] != m["line"]:
            changes.append(f"    line-height: {d['line']};")
        if d["tracking"] != m["tracking"]:
            changes.append(f"    letter-spacing: {em(d['tracking'])};")
        if changes:
            out += ["", "  @media (width >= $breakpoint-desktop) {"] + changes + ["  }"]
        out += ["}", ""]
    return "\n".join(out)


def build_breakpoints(t):
    return "\n".join(f"$breakpoint-{kebab(n)}: {v}px;" for n, v in t["breakpoint"].items()) + "\n"


def build_snippet(t):
    c = t["color"]
    lines = ["{%- style -%}", "  {%- for scheme in settings.color_schemes -%}",
             "    {%- if forloop.first -%}:root,{%- endif -%}", "    .color-{{ scheme.id }} {"]
    for rid in c["roles"]:
        lines.append(f"      --color-{kebab(rid)}: {{{{ scheme.settings.{rid} }}}};")
    lines += ["    }", "  {%- endfor -%}"]
    if c.get("fixed"):
        lines.append("  :root {")
        for fid in c["fixed"]:
            lines.append(f"    --color-{kebab(fid)}: {{{{ settings.color_{fid} }}}};")
        lines.append("  }")
    lines.append("{%- endstyle -%}")
    return "\n".join(lines) + "\n"


def scheme_values(t):
    c = t["color"]
    out = {}
    for sid, s in c["schemes"].items():
        out[sid] = {"settings": {rid: norm_hex(resolve(t, s[rid])).upper() for rid in c["roles"]}}
    return out


def fixed_values(t):
    return {f"color_{fid}": norm_hex(resolve(t, f["value"])).upper() for fid, f in (t["color"].get("fixed") or {}).items()}


def schema_group(t):
    c = t["color"]
    first = next(iter(c["schemes"].values()))
    definition = [{"type": "color", "id": rid, "label": f"t:settings_schema.colors.roles.{rid}",
                   "default": norm_hex(resolve(t, first[rid])).upper()} for rid in c["roles"]]
    settings = [{"type": "header", "content": "t:settings_schema.colors.schemes_header"},
                {"type": "paragraph", "content": "t:settings_schema.colors.contrast_info"},
                {"type": "color_scheme_group", "id": "color_schemes", "definition": definition, "role": c["role_map"]}]
    for fid, f in (c.get("fixed") or {}).items():
        settings.append({"type": "color", "id": f"color_{fid}", "label": f"t:settings_schema.colors.fixed.{fid}",
                         "default": norm_hex(resolve(t, f["value"])).upper()})
    return {"name": "t:settings_schema.colors.name", "settings": settings}


def merge_schema(theme, t):
    path = os.path.join(theme, "config", "settings_schema.json")
    if not os.path.exists(path):
        return None
    banner, data = load_json_with_banner(path)
    group = schema_group(t)
    idx = next((i for i, g in enumerate(data) if any(s.get("id") == "color_schemes" for s in g.get("settings", []))), None)
    if idx is None:
        data.append(group)
    else:
        data[idx] = group
    fonts = shopify_fonts(t)
    if fonts:
        ids = {font_setting_id(n, f) for n, f in fonts.items()}
        tg = typography_group(t)
        idx = next((i for i, g in enumerate(data) if any(s.get("id") in ids for s in g.get("settings", []))), None)
        if idx is None:
            data.append(tg)
        else:
            data[idx] = tg
    open(path, "w", encoding="utf-8").write(banner + json.dumps(data, indent=2) + "\n")
    return path


def merge_locale(theme, t):
    path = os.path.join(theme, "locales", "en.default.schema.json")
    if not os.path.exists(path):
        return None
    data = lenient_loads(open(path, encoding="utf-8").read())
    ss = data.setdefault("settings_schema", {})
    colors = ss.setdefault("colors", {})
    colors["name"] = "Colours"
    colors["schemes_header"] = "Colour schemes"
    colors["contrast_info"] = "Keep enough contrast between text and background in every scheme. Low contrast makes text hard to read and fails accessibility checks."
    colors["roles"] = {rid: r.get("label", rid.replace("_", " ").capitalize()) for rid, r in t["color"]["roles"].items()}
    if t["color"].get("fixed"):
        colors["fixed"] = {fid: f.get("label", fid.replace("_", " ").capitalize()) for fid, f in t["color"]["fixed"].items()}
    fonts = shopify_fonts(t)
    if fonts:
        typ = ss.setdefault("typography", {})
        typ["name"] = "Typography"
        for n, f in fonts.items():
            typ[font_setting_id(n, f)] = f.get("label", f"{n.replace('_', ' ').capitalize()} font")
    open(path, "w", encoding="utf-8").write(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    return path


def normalise_colors(obj):
    """Shopify saves colours in lowercase; compare case-insensitively so a theme pull doesn't look like an edit."""
    if isinstance(obj, dict):
        return {k: normalise_colors(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [normalise_colors(v) for v in obj]
    if isinstance(obj, str) and HEX.fullmatch(obj):
        return norm_hex(obj)
    return obj


def fingerprint(obj):
    return hashlib.sha256(json.dumps(normalise_colors(obj), sort_keys=True).encode()).hexdigest()[:16]


HOST_THEMES = ("horizon", "dawn")


def host_theme(theme):
    """Name of a stock Shopify theme whose colour system this theme still uses, or None."""
    path = os.path.join(theme, "config", "settings_schema.json")
    if not os.path.exists(path):
        return None
    try:
        _, data = load_json_with_banner(path)
    except ValueError:
        return None
    info = next((g for g in data if isinstance(g, dict) and g.get("name") == "theme_info"), {})
    name = (info.get("theme_name") or "").strip().lower()
    return name if name in HOST_THEMES else None


def merge_data(theme, t, lock, overwrite):
    path = os.path.join(theme, "config", "settings_data.json")
    if not os.path.exists(path):
        return None, None
    banner, data = load_json_with_banner(path)
    targets = [data.setdefault("current", {})]
    targets += [p for p in (data.get("presets") or {}).values() if isinstance(p, dict)]
    new = {"color_schemes": scheme_values(t), **fixed_values(t)}
    current_live = {"color_schemes": targets[0].get("color_schemes"), **{k: targets[0].get(k) for k in fixed_values(t)}}
    last = lock.get("settings_data")
    if targets[0].get("color_schemes") and last and fingerprint(current_live) != last and not overwrite:
        return path, "store-edited"
    for target in targets:
        target["color_schemes"] = copy.deepcopy(new["color_schemes"])
        for k, v in fixed_values(t).items():
            target[k] = v
        for n, f in shopify_fonts(t).items():
            target.setdefault(font_setting_id(n, f), font_handle(f))
    open(path, "w", encoding="utf-8").write(banner + json.dumps(data, indent=2) + "\n")
    lock["settings_data"] = fingerprint(new)
    return path, "written"


def build_reference(t):
    e = html.escape
    c = t["color"]
    pal = "".join(f'<div class="sw"><div class="chip" style="background:{e(v)}"></div><b>{e(k)}</b><span>{e(v)}</span></div>' for k, v in c["palette"].items())
    schemes = ""
    for sid, s in c["schemes"].items():
        bg, tx = resolve(t, s[c["role_map"]["background"]]), resolve(t, s[c["role_map"]["text"]])
        btn, on = resolve(t, s[c["role_map"]["primary_button"]]), resolve(t, s[c["role_map"]["on_primary_button"]])
        rows = "".join(f"<li>{e(rid)}: {e(s[rid].strip('{}').split('.')[-1])}</li>" for rid in c["roles"])
        schemes += (f'<div class="sc" style="background:{e(bg)};color:{e(tx)}"><b>{e(s["name"])}</b> <small>{e(sid)}</small>'
                    f'<p>Body text on this scheme.</p><span class="btn" style="background:{e(btn)};color:{e(on)}">Button</span><ul>{rows}</ul></div>')
    fam = {n: (f if isinstance(f, str) else (f.get("stack") or f"'{f['family']}', {f.get('fallback', 'sans-serif')}")) for n, f in t.get("font", {}).get("family", {}).items()}
    wt = t.get("font", {}).get("weight", {})
    ty = "".join(f'<div class="ty"><span class="lab">{e(r)} · {s["mobile"]["size"]}/{s["desktop"]["size"]}px</span>'
                 f'<div style="font-family:{e(fam.get(s["family"], "inherit"))};font-weight:{wt.get(s["weight"], 400)};font-size:{s["desktop"]["size"]}px;line-height:{s["desktop"]["line"]}">The quick brown fox jumps over the lazy dog</div></div>'
                 for r, s in t.get("type", {}).items())
    def px(v):
        v = resolve(t, v)
        return v if isinstance(v, (int, float)) else 0
    sp = "".join(f'<div class="sp"><span class="lab">space-{e(k)} · {px(v)}px</span><div class="bar" style="width:{px(v)}px"></div></div>' for k, v in t.get("space", {}).items())
    rd = "".join(f'<div class="rd"><div class="box" style="border-radius:{min(px(v), 40)}px"></div><span class="lab">radius-{e(k)} · {px(v)}px</span></div>' for k, v in t.get("radius", {}).items())
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Token reference</title>
<style>body{{font:14px/1.5 system-ui,sans-serif;margin:2rem;color:#111;background:#fff}}h2{{margin:2.5rem 0 1rem;font-size:1rem}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(10rem,1fr));gap:1rem}}.sw .chip{{height:4rem;border:1px solid #ddd;border-radius:4px;margin-bottom:.4rem}}.sw b,.sw span{{display:block;font-size:12px}}
.sc{{padding:1.25rem;border-radius:6px;border:1px solid #ddd}}.sc ul{{font-size:12px;padding-left:1rem}}.btn{{display:inline-block;padding:.4rem .9rem;border-radius:4px}}
.ty{{padding:1rem 0;border-bottom:1px solid #eee}}.lab{{font-size:12px;color:#666;display:block;margin-bottom:.3rem}}.bar{{height:12px;background:#111}}.sp{{margin:.5rem 0}}
.rd{{display:inline-block;margin:0 1.5rem 1rem 0}}.box{{width:5rem;height:5rem;background:#111;margin-bottom:.4rem}}</style></head><body>
<h1>Token reference</h1><h2>Palette</h2><div class="grid">{pal}</div><h2>Colour schemes</h2><div class="grid">{schemes}</div><h2>Type</h2>{ty}<h2>Spacing</h2>{sp}<h2>Radius</h2>{rd}</body></html>"""


def write(path, text):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    open(path, "w", encoding="utf-8").write(text)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tokens", nargs="?", default="docs/tokens.json")
    ap.add_argument("--theme", default=".")
    ap.add_argument("--reference")
    ap.add_argument("--scss-only", action="store_true")
    ap.add_argument("--overwrite-store-changes", action="store_true")
    a = ap.parse_args()
    t = json.load(open(a.tokens, encoding="utf-8"))
    validate(t)
    host = host_theme(a.theme)
    if host and not a.scss_only:
        fail(f"this theme is {host.capitalize()}, which has its own colour scheme settings. Run with --scss-only to generate only the SCSS layer; "
             "replacing a stock theme's colour group breaks every section that reads its variables.")
    lib = os.path.join(a.theme, "src", "scss", "lib")
    write(os.path.join(lib, "_variables.scss"), build_variables(t, host if a.scss_only else None))
    write(os.path.join(lib, "_typography.scss"), build_typography(t))
    write(os.path.join(lib, "global", "_breakpoints.scss"), build_breakpoints(t))
    done = ["src/scss/lib/_variables.scss", "_typography.scss", "global/_breakpoints.scss"]
    lock_path = os.path.join(os.path.dirname(a.tokens), "tokens.lock.json")
    lock = json.load(open(lock_path)) if os.path.exists(lock_path) else {}
    if not a.scss_only:
        write(os.path.join(a.theme, "snippets", "color-schemes.liquid"), build_snippet(t))
        done.append("snippets/color-schemes.liquid")
        write(os.path.join(a.theme, "snippets", "fonts.liquid"), build_fonts_snippet(t))
        done.append("snippets/fonts.liquid")
        for fn in (merge_schema, merge_locale):
            p = fn(a.theme, t)
            if p:
                done.append(os.path.relpath(p, a.theme))
        p, status = merge_data(a.theme, t, lock, a.overwrite_store_changes)
        if status == "store-edited":
            print("settings_data.json: the colour schemes were changed in the theme editor since the last build. Left untouched.")
            print("  The store is the source of truth after launch. To replace the merchant's values anyway, get approval, then rerun with --overwrite-store-changes.")
        elif p:
            done.append(os.path.relpath(p, a.theme))
    lock["tokens"] = fingerprint(t)
    write(lock_path, json.dumps(lock, indent=2) + "\n")
    if a.reference:
        write(a.reference, build_reference(t))
        done.append(a.reference)
    print("Wrote " + ", ".join(done))


if __name__ == "__main__":
    main()
