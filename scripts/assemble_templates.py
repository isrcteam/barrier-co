#!/usr/bin/env python3
"""Assemble the first version of the home and product templates and the header and footer groups.

Each custom section starts from its own schema preset (so it carries the Figma copy) and gets the
page-specific settings below. Images come from docs/assets/manifest.json when a slot is filled.
Run once to create the JSON for the first push; after that the theme editor owns it (core rule 18)
and `shopify theme pull --only templates/*.json ...` brings changes back.
  python3 scripts/assemble_templates.py
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)

TOKENS = json.load(open(P("docs", "tokens.json")))["color"]["palette"]
MANIFEST_PATH = P("docs", "assets", "manifest.json")
MANIFEST = json.load(open(MANIFEST_PATH)) if os.path.exists(MANIFEST_PATH) else {}
HEADER = "/*\n * ------------------------------------------------------------\n * IMPORTANT: The contents of this file are auto-generated.\n *\n * This file may be updated by the Shopify admin theme editor\n * or related systems. Please exercise caution as any changes\n * made to this file may be overwritten.\n * ------------------------------------------------------------\n */\n"

FLAGSHIP = "the-30-the-everyday"
TRAVEL = "the-8-made-to-go-where-you-go"
PALETTE = lambda key: "{{ settings.color_palette.%s }}" % key


SEED = json.load(open(P("docs", "data", "seed-result.json")))


def mo(mtype, handle):
    assert f"{mtype}/{handle}" in SEED["metaobjects"], f"unknown metaobject {mtype}/{handle}"
    return handle


def img(slot, variant="desktop", fallback=None):
    entry = MANIFEST.get(slot) or {}
    name = entry.get(variant) or (entry.get("desktop") if variant == "mobile" else None) or fallback
    return f"shopify://shop_images/{name}" if name else None


def load_jsonc(path):
    raw = open(path, encoding="utf-8").read()
    return json.loads(re.sub(r"^/\*.*?\*/", "", raw, flags=re.S))


def write_jsonc(path, data):
    open(path, "w", encoding="utf-8").write(HEADER + json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def schema(kind, name):
    src = open(P(kind, f"{name}.liquid"), encoding="utf-8").read()
    return json.loads(src[src.index("{% schema %}") + 12: src.index("{% endschema %}")])


def normalise_blocks(blocks, prefix):
    if not blocks:
        return {}, []
    if isinstance(blocks, dict):
        out = {}
        for key, b in blocks.items():
            nb = {k: v for k, v in b.items() if k not in ("blocks", "block_order")}
            nb.setdefault("settings", {})
            if b.get("blocks"):
                nb["blocks"], nb["block_order"] = normalise_blocks(b["blocks"], f"{prefix}_{key}")
                if b.get("block_order"):
                    nb["block_order"] = b["block_order"]
            out[key] = nb
        order = [k for k, b in blocks.items() if not b.get("static")]
        return out, order
    out, order = {}, []
    for i, b in enumerate(blocks, 1):
        key = f"{prefix}_{b['type'].strip('_').replace('-', '_')}_{i}"
        nb = {"type": b["type"], "settings": dict(b.get("settings", {}))}
        if b.get("static"):
            nb["static"] = True
            key = b.get("id", key)
        if b.get("blocks"):
            nb["blocks"], nb["block_order"] = normalise_blocks(b["blocks"], key)
        out[key] = nb
        if not b.get("static"):
            order.append(key)
    return out, order


LOCALE = None


def translate(value):
    global LOCALE
    if isinstance(value, str) and value.startswith("t:"):
        if LOCALE is None:
            LOCALE = load_jsonc_full(P("locales", "en.default.schema.json"))
        node = LOCALE
        for part in value[2:].split("."):
            node = node.get(part) if isinstance(node, dict) else None
        return node if isinstance(node, str) else value
    if isinstance(value, dict):
        return {k: translate(v) for k, v in value.items()}
    if isinstance(value, list):
        return [translate(v) for v in value]
    return value


def load_jsonc_full(path):
    sys.path.insert(0, P("scripts"))
    from merge_locale_fragments import strip_jsonc
    return json.loads(strip_jsonc(open(path, encoding="utf-8").read()))


def from_preset(name, preset_index=0, settings=None, prefix=None):
    sch = schema("sections", name)
    preset = translate(sch["presets"][preset_index])
    blocks, order = normalise_blocks(preset.get("blocks"), prefix or name.replace("-", "_"))
    if isinstance(preset.get("blocks"), dict) and preset.get("block_order"):
        order = preset["block_order"]
    s = {"type": name, "settings": dict(preset.get("settings", {}))}
    for k, v in (settings or {}).items():
        if v is not None:
            s["settings"][k] = v
    if blocks:
        s["blocks"], s["block_order"] = blocks, order
    return s


def set_block_images(section, setting, slots):
    keys = section.get("block_order", [])
    for key, slot in zip(keys, slots):
        val = img(slot)
        if val:
            section["blocks"][key]["settings"][setting] = val


def home():
    sections = {}
    sections["hero"] = from_preset("hero-banner", 0, {
        "image_desktop": img("home_hero", "desktop", "Hero_Banner.jpg"),
        "image_mobile": img("home_hero", "mobile", "banner1_mobile.jpg"),
        "heading_tag": "h1",
        "spotlight_product": FLAGSHIP,
        "play_poster": img("home_intro_video_poster"),
    })
    press_blocks, press_order = {}, []
    for i in range(1, 4):
        press_blocks[f"quote_{i}"] = {"type": "text", "settings": {"text": "<p>“Lorem ipsum dolor sid ed” - FORBES</p>", "type_preset": "custom", "font_size": "1rem"}}
        press_blocks[f"stars_{i}"] = {"type": "icon", "settings": {"icon": "star", "width": 16, "icon_color": TOKENS["sandstone"]}}
        press_order += [f"quote_{i}", f"stars_{i}"]
    sections["press"] = {
        "type": "marquee",
        "settings": {"background_color": PALETTE("color2"), "padding-block-start": 18, "padding-block-end": 18, "gap_between_elements": 30},
        "blocks": press_blocks,
        "block_order": press_order,
    }
    sections["intro"] = from_preset("intro-media", 0, {"poster": img("home_intro_video_poster"), "image": img("home_intro_video_poster")})
    sections["routine"] = from_preset("image-carousel", 0, {"background_color": TOKENS["linen"]}, "routine")
    set_block_images(sections["routine"], "image", ["routine_cleanse", "routine_hydrate", "routine_protect"])
    words = ["Cleanse", "Moisturise", "Protect", "Regenerate"]
    sections["ticker"] = {
        "type": "marquee",
        "settings": {"background_color": PALETTE("foreground"), "padding-block-start": 11, "padding-block-end": 11, "gap_between_elements": 20},
        "blocks": {f"word_{i}": {"type": "text", "settings": {"text": f"<p>{w}</p>"}} for i, w in enumerate(words, 1)},
        "block_order": [f"word_{i}" for i in range(1, 5)],
    }
    sections["featured"] = featured_product()
    sections["real_use"] = from_preset("video-testimonials", 0, {"quote_background_color": TOKENS["clay"]})
    sections["results"] = from_preset("clinical-results", 0, {
        "image": img("stats_background", "desktop", "Results_Section_1.jpg"),
        "image_mobile": img("stats_background", "mobile", "Results_section_-_mobile.jpg"),
        "results": [mo("clinical_result", h) for h in ["improved-facial-appearance", "reduced-fine-lines", "increased-skin-hydration", "improved-skin-elasticity"]],
    })
    sections["proof_icons"] = from_preset("feature-icons", 0)
    set_block_images(sections["proof_icons"], "icon", [f"feature_icon_{i}" for i in range(1, 5)])
    sections["banner"] = from_preset("hero-banner", 1, {
        "image_desktop": img("inset_banner", "desktop", "Hero_Banner1.jpg"),
        "image_mobile": img("inset_banner", "mobile", "Mobile_banner.jpg"),
    }, "banner")
    sections["lifestyle"] = from_preset("image-carousel", 1, {}, "lifestyle")
    set_block_images(sections["lifestyle"], "image", ["lifestyle_1", "lifestyle_2", "lifestyle_3"])
    mid = sections["lifestyle"]["block_order"][1] if len(sections["lifestyle"].get("block_order", [])) > 1 else None
    if mid:
        sections["lifestyle"]["blocks"][mid]["settings"]["product"] = TRAVEL
    sections["before_after"] = from_preset("before-after", 0, {
        "product": TRAVEL,
        "comparisons": [mo("before_after", "the-30-day-14")],
        "card_background_color": TOKENS["linen"],
    })
    return {"sections": sections, "order": list(sections)}


def product_details_blocks(include_buy_box_extras):
    blocks, order = {}, []

    def add(key, btype, settings=None, **extra):
        blocks[key] = {"type": btype, "settings": settings or {}, **extra}
        order.append(key)

    if include_buy_box_extras:
        add("rating", "product-rating", {"link_anchor": "#judgeme_product_reviews"})
    add("title", "text", {"text": "<h1>{{ closest.product.title }}</h1>", "type_preset": "h2"})
    add("description", "text", {"text": "{{ closest.product.description }}", "type_preset": "rte"})
    if include_buy_box_extras:
        add("highlights", "product-highlights")
        add("clinicians", "clinician-proof", {"background_color": TOKENS["linen"], "mark_image": img("clinician_mark"),
                                              "avatar_1": img("clinician_avatar_1"), "avatar_2": img("clinician_avatar_2"), "avatar_3": img("clinician_avatar_3")})
        add("purchase", "purchase-options")
    add("price", "price", {"type_preset": "paragraph"})
    add("buy_buttons", "buy-buttons", {}, blocks={
        "quantity": {"type": "quantity", "static": True, "disabled": True, "settings": {}},
        "add-to-cart": {"type": "add-to-cart", "static": True, "settings": {"style_class": "button"}},
        "accelerated-checkout": {"type": "accelerated-checkout", "static": True, "disabled": True, "settings": {}},
    }, block_order=[])
    add("guarantee", "text", {"text": "<p>90-day money-back guarantee | Free 2–3 day shipping</p>", "type_preset": "custom", "font_size": "0.625rem", "case": "uppercase", "alignment": "center"})
    if include_buy_box_extras:
        add("recognition", "recognition-slider")
        add("promo", "promo-card", {"background_color": TOKENS["white"], "image": img("promo_card_image")})
        add("quotes", "quote-slider", {"background_color": TOKENS["linen"]})
    rows = [("How to use", "how_to_use", True), ("Claims", "claims", False), ("Size & pack details", "size_and_pack_details", False)]
    if not include_buy_box_extras:
        rows.append(("Ingredients", "full_ingredient_list", False))
    acc_blocks, acc_order = {}, []
    for i, (heading, key, open_) in enumerate(rows, 1):
        rk = f"row_{i}"
        acc_blocks[rk] = {"type": "_accordion-row", "settings": {"heading": heading, "open_by_default": open_},
                          "blocks": {f"{rk}_text": {"type": "text", "settings": {"text": "{{ closest.product.metafields.custom.%s | metafield_tag }}" % key, "type_preset": "rte"}}},
                          "block_order": [f"{rk}_text"]}
        acc_order.append(rk)
    add("details", "accordion", {"icon": "plus", "dividers": False, "type_preset": "h5", "border": "none"}, blocks=acc_blocks, block_order=acc_order)
    return blocks, order


GALLERY = {"media_presentation": "carousel", "slideshow_controls_style": "thumbnails", "slideshow_mobile_controls_style": "thumbnails",
           "thumbnail_position": "left", "thumbnail_width": 72, "thumbnail_radius": 0, "media_radius": 0, "aspect_ratio": "1",
           "media_fit": "cover", "constrain_to_viewport": False, "extend_media": False, "icons_style": "chevron", "zoom": True, "hide_variants": True}


def featured_product():
    blocks, order = product_details_blocks(False)
    return {"type": "featured-product-information",
            "settings": {"product": FLAGSHIP, "desktop_media_position": "left", "content_width": "content-center-aligned", "equal_columns": False, "gap": 28,
                         "padding-block-start": 0, "padding-block-end": 0},
            "blocks": {"media-gallery": {"type": "_featured-product-information-carousel", "static": True, "settings": dict(GALLERY)},
                       "product-details": {"type": "_product-details", "static": True,
                                           "settings": {"gap": 24, "sticky_details_desktop": False, "details_position": "center", "padding-block-start": 0, "padding-block-end": 0},
                                           "blocks": blocks, "block_order": order}},
            "block_order": []}


def product():
    tpl = load_jsonc(P("templates", "product.json"))
    main = tpl["sections"]["main"]
    main["settings"].update({"desktop_media_position": "left", "content_width": "content-center-aligned", "equal_columns": False, "gap": 28,
                             "enable_sticky_add_to_cart": True})
    main["blocks"]["media-gallery"]["settings"].update(GALLERY)
    details = main["blocks"]["product-details"]
    details["blocks"], details["block_order"] = product_details_blocks(True)
    details["settings"].update({"gap": 24, "sticky_details_desktop": False, "padding-block-start": 0, "padding-block-end": 0})
    main["block_order"] = []
    for k in [k for k, b in main["blocks"].items() if not b.get("static")]:
        del main["blocks"][k]

    sections = {"breadcrumb_bar": {"type": "section", "settings": {"padding-block-start": 8, "padding-block-end": 8},
                                   "blocks": {"breadcrumbs": {"type": "breadcrumbs", "settings": {"show_collection": False}}}, "block_order": ["breadcrumbs"]},
                "main": main}
    sections["hotspots"] = from_preset("benefit-hotspots", 0, {"panel_color": TOKENS["linen"], "panel_text_color": TOKENS["sepia"],
                                                               "product_image": img("pdp_hotspot_cloth"), "photo": img("pdp_benefit_photo")})
    sections["real_use"] = from_preset("video-testimonials", 0, {"use_product_data": True, "quote_background_color": TOKENS["clay"]})
    sections["results"] = from_preset("clinical-results", 0, {"use_product_data": True,
                                                              "image": img("stats_background", "desktop", "Results_Section_1.jpg"),
                                                              "image_mobile": img("stats_background", "mobile", "Results_section_-_mobile.jpg")})
    sections["ingredients"] = from_preset("ingredient-list", 0, {"use_product_data": True, "divider_color": TOKENS["fossil"]})
    sections["film"] = from_preset("video-banner", 0, {"poster_desktop": img("video_banner_poster"), "poster_mobile": img("video_banner_poster", "mobile")})
    sections["before_after"] = from_preset("before-after", 0, {"use_product_data": True, "card_background_color": TOKENS["linen"]})
    sections["reviews"] = {"type": "section", "settings": {"padding-block-start": 80, "padding-block-end": 80},
                           "blocks": {"reviews_heading": {"type": "text", "settings": {"text": "<h2>Reviews</h2>", "type_preset": "h1"}},
                                      "judgeme_reviews": {"type": "shopify://apps/judge-me-reviews/blocks/review_widget/61ccd3b1-a9f2-4160-9fe9-4fec8413e5d8", "settings": {}}},
                           "block_order": ["reviews_heading", "judgeme_reviews"]}
    sections["faq"] = from_preset("faq-panel", 0, {"use_product_data": True, "divider_color": TOKENS["fossil"],
                                                  "image": img("faq_background"), "image_mobile": img("faq_background", "mobile")})
    tpl["sections"] = sections
    tpl["order"] = list(sections)
    return tpl


def header_group():
    g = load_jsonc(P("sections", "header-group.json"))
    ann_id = next(k for k, s in g["sections"].items() if s["type"] == "header-announcements")
    ann = g["sections"][ann_id]
    ann["settings"].update({"background_color": PALETTE("foreground"), "section_width": "full-width", "divider_width": 0,
                            "padding-block-start": 0, "padding-block-end": 0})
    msgs = ["Free shipping on orders over $50", "90-day money-back guarantee"]
    ann["blocks"] = {f"announcement_{i}": {"type": "_announcement", "settings": {"text": m, "font": "var(--font-heading--family)", "font_size": "0.75rem",
                                                                                   "weight": "400", "case": "uppercase"}} for i, m in enumerate(msgs, 1)}
    ann["block_order"] = list(ann["blocks"])
    hdr = g["sections"]["header_section"]
    hdr["settings"].update({"logo_position": "left", "menu_position": "center", "menu_row": "top", "search_row": "top", "show_search": True,
                            "search_position": "right", "show_country": False, "show_language": False, "actions_display_style": "text",
                            "actions_font": "subheading", "actions_font_size": "0.875rem", "actions_text_case": "uppercase",
                            "background_color_top": PALETTE("background"), "text_color_top": PALETTE("foreground"),
                            "enable_transparent_header_home": True, "home_inverse_logo": True, "text_color_transparent_home": PALETTE("color5"),
                            "enable_transparent_header_product": False, "enable_transparent_header_collection": False,
                            "divider_width": 0, "border_width": 0, "enable_sticky_header": "always"})
    hdr["blocks"]["header-menu"]["settings"].update({"menu": "primary-menu", "menu_style": "text", "type_font_primary_link": "subheading",
                                                     "type_font_primary_size": "0.875rem", "type_case_primary_link": "uppercase"})
    return g


def footer_group():
    g = load_jsonc(P("sections", "footer-group.json"))
    sections = {}
    sections["social"] = from_preset("social-gallery", 0, {"background_color": TOKENS["linen"], "profile_link": "https://www.instagram.com/"})
    set_block_images(sections["social"], "image", [f"insta_{i}" for i in range(1, 7)])
    sections["logos"] = from_preset("logo-list", 0)
    set_block_images(sections["logos"], "image", ["logo_equinox", "logo_delta_one", "logo_credo"] * 2)
    names = ["Equinox", "Delta One", "Credo"] * 2
    for key, name in zip(sections["logos"].get("block_order", []), names):
        sections["logos"]["blocks"][key]["settings"]["alt"] = name
    footer = g["sections"]["footer"]
    footer["settings"].update({"background_color": PALETTE("foreground"), "section_width": "page-width", "gap": 56,
                               "padding-block-start": 56, "padding-block-end": 0})
    community = {"type": "group", "settings": {"content_direction": "column", "gap": 30}, "blocks": {
        "join": {"type": "text", "settings": {"text": "<p>Join the community</p>", "type_preset": "custom", "font": "var(--font-heading--family)", "font_size": "1.125rem", "case": "uppercase"}},
        "signup": {"type": "email-signup", "settings": {"heading": "", "border_style": "underline", "input_style": "custom", "border_width": 1,
                                                        "input_text_color": PALETTE("background"), "input_border_color": PALETTE("background"),
                                                        "style_class": "button-custom", "custom_button_background": PALETTE("background"),
                                                        "custom_button_text": PALETTE("foreground"), "custom_button_border": PALETTE("background"),
                                                        "display_type": "text", "label": "Submit"}},
        "consent": {"type": "text", "settings": {"text": "<p>By submitting, you agree to the Terms & Conditions and Privacy Policy.</p>", "type_preset": "custom", "font_size": "0.75rem"}},
        "tagline": {"type": "text", "settings": {"text": "<p>Body care, reformatted.</p>", "type_preset": "custom", "font": "var(--font-heading--family)", "font_size": "0.875rem", "case": "uppercase"}},
    }, "block_order": ["join", "signup", "consent", "tagline"]}
    footer["blocks"] = {
        "community": community,
        "menu_company": {"type": "menu", "settings": {"menu": "footer-company", "heading": "Company", "heading_preset": "paragraph", "link_preset": "paragraph", "show_as_accordion": False}},
        "menu_support": {"type": "menu", "settings": {"menu": "footer-support", "heading": "Support", "heading_preset": "paragraph", "link_preset": "paragraph", "show_as_accordion": False}},
        "menu_community": {"type": "menu", "settings": {"menu": "footer-community", "heading": "Community", "heading_preset": "paragraph", "link_preset": "paragraph", "show_as_accordion": False}},
        "wordmark": {"type": "jumbo-text", "settings": {"text": "BARRIER", "font": "heading", "alignment": "center", "line_height": "0.8",
                                                        "letter_spacing": "normal", "case": "uppercase", "text_effect": "none"}},
    }
    footer["block_order"] = list(footer["blocks"])
    sections["footer"] = footer
    util = g["sections"]["utilities"]
    util["settings"].update({"background_color": PALETTE("foreground"), "divider_thickness": 0, "padding-block-start": 56, "padding-block-end": 24})
    util["blocks"].pop("social_icons", None)
    util["blocks"].get("copyright", {}).setdefault("settings", {}).update({"show_powered_by": False, "font_size": "0.875rem"})
    util["blocks"].get("policy_list", {}).setdefault("settings", {}).update({"font_size": "0.875rem"})
    util["block_order"] = [k for k in util.get("block_order", list(util["blocks"])) if k in util["blocks"]]
    sections["utilities"] = util
    g["sections"] = sections
    g["order"] = list(sections)
    return g


def main():
    write_jsonc(P("templates", "index.json"), home())
    write_jsonc(P("templates", "product.json"), product())
    write_jsonc(P("sections", "header-group.json"), header_group())
    write_jsonc(P("sections", "footer-group.json"), footer_group())
    missing = sorted(s for s in ["home_hero", "routine_cleanse", "stats_background", "feature_icon_1", "lifestyle_1", "insta_1", "logo_equinox",
                                 "pdp_hotspot_cloth", "video_banner_poster", "faq_background"] if s not in MANIFEST)
    print("Wrote templates/index.json, templates/product.json, sections/header-group.json, sections/footer-group.json")
    if missing:
        print("Image slots not in the manifest yet (re-run after the asset pack): " + ", ".join(missing))


if __name__ == "__main__":
    main()
