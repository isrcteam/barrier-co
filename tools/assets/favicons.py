#!/usr/bin/env python3
"""Generate favicons and the social share image from the brand mark.

Usage: python3 favicons.py <mark.svg|mark.png> [--bg "#FFFFFF"] [--logo logo.png] [--out docs/assets/source/brand]
The mark must be square. SVG needs cairosvg, rsvg-convert or ImageMagick; otherwise export a PNG of
at least 1024 px from Figma. Writes, named by the asset convention (no project prefix):
  favicon-32.png, favicon-48.png, apple-touch-icon-180.png, icon-192.png, icon-512.png, favicon.svg (if SVG given)
  social-share-1200x628.png  (logo or mark centred on --bg)
--bg must be a colour from the palette in docs/tokens.json; pass it by name with --bg-token instead to be sure.
"""
import argparse, json, os, shutil, subprocess, sys, tempfile
from PIL import Image

def rasterise(svg, size=1024):
    out = os.path.join(tempfile.mkdtemp(), "mark.png")
    try:
        import cairosvg
        cairosvg.svg2png(url=svg, write_to=out, output_width=size, output_height=size)
        return out
    except ImportError:
        pass
    for cmd in (["rsvg-convert", "-w", str(size), "-h", str(size), svg, "-o", out],
                ["magick", "-background", "none", "-density", "600", svg, "-resize", f"{size}x{size}", out],
                ["convert", "-background", "none", "-density", "600", svg, "-resize", f"{size}x{size}", out]):
        if shutil.which(cmd[0]) and subprocess.run(cmd, capture_output=True).returncode == 0 and os.path.exists(out):
            return out
    sys.exit("Can't render SVG here. Export the mark as a PNG of at least 1024 px (Figma download_assets) and pass that.")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mark")
    ap.add_argument("--bg")
    ap.add_argument("--bg-token")
    ap.add_argument("--logo")
    ap.add_argument("--out", default="docs/assets/source/brand")
    a = ap.parse_args()
    bg = a.bg
    if a.bg_token:
        bg = json.load(open("docs/tokens.json"))["color"]["palette"][a.bg_token]
    bg = bg or "#FFFFFF"
    os.makedirs(a.out, exist_ok=True)
    src = rasterise(a.mark) if a.mark.lower().endswith(".svg") else a.mark
    im = Image.open(src).convert("RGBA")
    if abs(im.width - im.height) > 2:
        sys.exit(f"The mark is {im.width}x{im.height}. Favicons need a square mark: ask the designer for one.")
    if im.width < 512:
        sys.exit(f"The mark is only {im.width}px. Export at least 512px, ideally 1024px.")
    made = []
    for size, name in ((32, "favicon-32"), (48, "favicon-48"), (180, "apple-touch-icon-180"), (192, "icon-192"), (512, "icon-512")):
        canvas = Image.new("RGBA", (size, size), bg if name.startswith("apple") else (0, 0, 0, 0))
        pad = int(size * 0.1) if name.startswith("apple") else 0
        mark = im.resize((size - 2 * pad, size - 2 * pad), Image.LANCZOS)
        canvas.paste(mark, (pad, pad), mark)
        path = os.path.join(a.out, f"{name}.png")
        canvas.save(path, optimize=True)
        made.append(path)
    if a.mark.lower().endswith(".svg"):
        shutil.copy(a.mark, os.path.join(a.out, "favicon.svg"))
        made.append(os.path.join(a.out, "favicon.svg"))
    logo = Image.open(rasterise(a.logo) if a.logo and a.logo.lower().endswith(".svg") else (a.logo or src)).convert("RGBA")
    share = Image.new("RGB", (1200, 628), bg)
    scale = min(700 / logo.width, 300 / logo.height)
    logo = logo.resize((max(1, int(logo.width * scale)), max(1, int(logo.height * scale))), Image.LANCZOS)
    share.paste(logo, ((1200 - logo.width) // 2, (628 - logo.height) // 2), logo)
    path = os.path.join(a.out, "social-share-1200x628.png")
    share.save(path, optimize=True)
    made.append(path)
    print("Wrote:\n  " + "\n  ".join(made))

if __name__ == "__main__":
    main()
