#!/usr/bin/env python3
"""Generate snippets/design-tokens.liquid from docs/tokens.json.

Every size becomes a rem custom property, type roles become .type-<role> classes with their
desktop sizes behind the desktop breakpoint, and fixed colours read their theme settings.
Run after any change to docs/tokens.json:  python3 scripts/build_token_css.py
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "docs", "tokens.json")
OUT = os.path.join(ROOT, "snippets", "design-tokens.liquid")
REF = re.compile(r"^\{([a-z0-9_.-]+)\}$")


def kebab(s):
    return re.sub(r"[_\s]+", "-", str(s)).lower()


def rem(px):
    if px == 0:
        return "0"
    v = px / 16
    return f"{v:.4f}".rstrip("0").rstrip(".") + "rem"


def value(v):
    if isinstance(v, str):
        m = REF.match(v.strip())
        if m:
            group, *rest = m.group(1).split(".")
            return f"var(--{group}-{kebab('-'.join(rest))})"
        return v
    return rem(v)


def main():
    t = json.load(open(SRC, encoding="utf-8"))
    desktop = t["breakpoint"]["desktop"]
    root, wide, classes = [], [], []

    for group in ("space", "layout", "radius", "border", "icon"):
        for name, v in t.get(group, {}).items():
            root.append(f"--{group}-{kebab(name)}: {value(v)};")
    for name, v in t.get("opacity", {}).items():
        root.append(f"--opacity-brand-{kebab(name)}: {v};")
    for name, v in t.get("effect", {}).items():
        root.append(f"--effect-{kebab(name)}: {v};")
    for name, v in t.get("z", {}).items():
        root.append(f"--z-{kebab(name)}: {v};")
    for name, v in t.get("motion", {}).get("duration", {}).items():
        root.append(f"--duration-{kebab(name)}: {v};")
    for name, v in t.get("motion", {}).get("easing", {}).items():
        root.append(f"--easing-{kebab(name)}: {v};")

    for name, f in t["font"]["family"].items():
        stack = f["stack"] if isinstance(f, dict) else f
        root.append(f"--font-family-{kebab(name)}: {stack};")
    for name, w in t["font"]["weight"].items():
        root.append(f"--font-weight-{kebab(name)}: {w};")

    for fid, f in (t["color"].get("fixed") or {}).items():
        root.append(f"--color-{kebab(fid)}: {{{{ settings.color_{fid} }}}};")
        root.append(f"--color-{kebab(fid)}-rgb: {{{{ settings.color_{fid}.red }}}} {{{{ settings.color_{fid}.green }}}} {{{{ settings.color_{fid}.blue }}}};")

    for role, spec in t["type"].items():
        r = kebab(role)
        m, d = spec["mobile"], spec["desktop"]
        root += [f"--type-{r}-size: {rem(m['size'])};", f"--type-{r}-line: {m['line']};",
                 f"--type-{r}-tracking: {m['tracking']}em;" if m['tracking'] else f"--type-{r}-tracking: 0;"]
        for k, unit in (("size", "rem"), ("line", ""), ("tracking", "em")):
            if d[k] != m[k]:
                out = rem(d[k]) if k == "size" else f"{d[k]}{unit}"
                wide.append(f"--type-{r}-{k}: {out};")
        classes.append(
            f".type-{r} {{ font-family: var(--font-family-{kebab(spec['family'])}); "
            f"font-weight: var(--font-weight-{kebab(spec['weight'])}); font-size: var(--type-{r}-size); "
            f"line-height: var(--type-{r}-line); letter-spacing: var(--type-{r}-tracking); }}")

    for name, v in t.get("layout", {}).items():
        if name.endswith("-desktop"):
            base = name[: -len("-desktop")]
            root.append(f"--layout-{base}: var(--layout-{name[: -len('-desktop')]}-mobile);")
            wide.append(f"--layout-{base}: var(--layout-{name});")

    lines = ["{% style %}", "  :root {"] + [f"    {l}" for l in root] + ["  }", "",
             f"  @media screen and (min-width: {desktop}px) {{", "    :root {"] + \
            [f"      {l}" for l in wide] + ["    }", "  }", ""] + [f"  {c}" for c in classes] + ["{% endstyle %}", ""]
    open(OUT, "w", encoding="utf-8").write("\n".join(lines))
    print(f"Wrote {os.path.relpath(OUT, ROOT)}: {len(root)} variables, {len(wide)} desktop overrides, {len(classes)} type classes")


if __name__ == "__main__":
    sys.exit(main())
