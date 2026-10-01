# brand-overrides: settings to set

Setting ids and values checked against the schemas in this repo (Horizon 4.2.0). Colours use palette references, which resolve to: `background` Sandstone, `foreground` Clay, `color1` Linen, `color2` Tan, `color3` Fossil, `color4` Sepia, `color5` White (current `color_palette` in `config/settings_data.json`). `snippets/brand-overrides.liquid` assumes these values; without them the CSS alone won't match the design.

## config/settings_data.json (`current`)
| Setting | Value | Why |
| --- | --- | --- |
| `icon_stroke` | `"thin"` | Thin chevrons and arrows (announcements, slideshows) |
| `button_border_radius_primary` / `button_border_radius_secondary` | `0` / `0` | Already set |
| `primary_button_border_width` / `secondary_button_border_width` | `0` / `1` | Already set (Outline/Secondary have a 1 border) |
| `button_text_case_primary` / `button_text_case_secondary` | `"uppercase"` | Already set |
| `type_font_button_primary` / `type_font_button_secondary` | `"accent"` / `"accent"` | Akzidenz family; the CSS sets the ExtraBold weight |
| `palette_input_border` | `"{{ settings.color_palette.color3 }}"` | Already set. **Required**: every Fossil hairline in the overrides reads `--color-input-border` |
| `inputs_border_radius` | `0` | Already set |
| `logo` / `logo_inverse` | Clay logotype / white logotype | Inverse is used by the transparent home header |
| `logo_height` / `logo_height_mobile` | `16` / `14` | Figma 197×16 desktop, 170×14 mobile |

## sections/header-group.json
### header-announcements
| Setting | Value |
| --- | --- |
| `background_color` | `"{{ settings.color_palette.foreground }}"` |
| `section_width` | `"full-width"` |
| `divider_width` | `0` |
| `padding-block-start` / `padding-block-end` | `0` / `0` (the arrows set the 34 bar height) |
| `speed` | `5` |

`_announcement` blocks: `text` `"Free shipping on orders over $50"`, `font` `"var(--font-heading--family)"`, `font_size` `"0.75rem"`, `weight` `"400"`, `case` `"uppercase"`. Use two or more blocks to get the chevrons.

### header
| Setting | Value |
| --- | --- |
| `logo_position` | `"left"` |
| `menu_position` | `"center"` |
| `menu_row` / `search_row` | `"top"` / `"top"` |
| `show_search` / `search_position` | `true` / `"right"` |
| `show_country` / `show_language` | `false` / `false` |
| `actions_display_style` | `"text"` |
| `actions_font` | `"subheading"` (GT America Medium) |
| `actions_font_size` | `"0.875rem"` |
| `actions_text_case` | `"uppercase"` |
| `background_color_top` | `"{{ settings.color_palette.background }}"` |
| `text_color_top` | `"{{ settings.color_palette.foreground }}"` |
| `enable_transparent_header_home` | `true` |
| `home_inverse_logo` | `true` |
| `text_color_transparent_home` | `"{{ settings.color_palette.color5 }}"` |
| `enable_transparent_header_product` / `_collection` | `false` / `false` |
| `divider_width` / `border_width` | `0` / `0` |
| `enable_sticky_header` | `"always"` |

`_header-menu` (static block `header-menu`): `menu` `"main-menu"` (Shop, Science, About), `menu_style` `"text"`, `type_font_primary_link` `"subheading"`, `type_font_primary_size` `"0.875rem"`, `type_case_primary_link` `"uppercase"`.

## templates/index.json
### marquee, press strip (after the hero)
| Setting | Value |
| --- | --- |
| `background_color` | `"{{ settings.color_palette.color2 }}"` (Tan) |
| `padding-block-start` / `padding-block-end` | `18` / `18` (56 strip) |
| `gap_between_elements` | `30` |
| `movement_direction` | `"normal"` |

Blocks, repeated per press quote: `icon` with `image_upload` = press logo, `width` `76`; then `text` with `text` `"<p>“Lorem ipsum dolor sid ed” - FORBES</p>"` (placeholder copy from Figma until the client supplies quotes), `font_size` `"1rem"`. The image block keeps the bar styling off.

### marquee, ticker (after the image carousel)
| Setting | Value |
| --- | --- |
| `background_color` | `"{{ settings.color_palette.foreground }}"` (Clay) |
| `padding-block-start` / `padding-block-end` | `11` / `11` (54 strip) |
| `gap_between_elements` | `20` |

Blocks: only `text` blocks, one word each: Cleanse, Moisturise, Protect, Regenerate. Bars and the `title_bold` role come from the overrides.

### featured product
Use the stock **`featured-product-information`** section instead of `featured-product`: the thumbnail rail, buy box width and accordion styling only apply to the product-information layout, and Horizon's `featured-product` (media + card) has no thumbnails. Settings: `product` = the 30-pack, `desktop_media_position` `"left"`, `content_width` `"content-center-aligned"`, `equal_columns` `false`, `gap` `28` (870 + 28 + 482 = 1380). Static `media-gallery` (`_featured-product-information-carousel`): same values as the PDP gallery below. Custom blocks go inside `product-details` as on the PDP.

## templates/product.json
### product-information
| Setting | Value |
| --- | --- |
| `desktop_media_position` | `"left"` |
| `content_width` | `"content-center-aligned"` |
| `equal_columns` | `false` |
| `gap` | `28` |
| `enable_sticky_add_to_cart` | `true` |

Static `media-gallery` (`_product-media-gallery`):
| Setting | Value |
| --- | --- |
| `media_presentation` | `"carousel"` |
| `slideshow_controls_style` | `"thumbnails"` |
| `slideshow_mobile_controls_style` | `"thumbnails"` |
| `thumbnail_position` | `"left"` |
| `thumbnail_width` | `72` (max; the CSS sets 80 desktop / 74 mobile) |
| `thumbnail_radius` / `media_radius` | `0` / `0` |
| `aspect_ratio` | `"1"` |
| `media_fit` | `"cover"` |
| `constrain_to_viewport` / `extend_media` | `false` / `false` |
| `icons_style` | `"chevron"` |

Static `product-details`: title text block keeps `"<h1>{{ closest.product.title }}</h1>"` (the overrides apply the h2 role to it and to a `product-title` block). Replace the `disclosures` block with an **`accordion`** block: `icon` `"plus"`, `dividers` `false` (the overrides draw the Fossil hairlines), `type_preset` `"h5"`, `border` `"none"`; `_accordion-row` blocks "How to use" (`open_by_default` `true`), "Claims", "Size & pack details", each with a `text` block inside.

## sections/footer-group.json
### footer
| Setting | Value |
| --- | --- |
| `background_color` | `"{{ settings.color_palette.foreground }}"` |
| `section_width` | `"page-width"` |
| `gap` | `56` |
| `padding-block-start` / `padding-block-end` | `56` / `0` |

Blocks in this order (five blocks puts the jumbo text on its own full-width row):
1. `group` (`content_direction` `"column"`, `gap` `30`): `text` "Join the community" (`font` `"var(--font-heading--family)"`, `font_size` `"1.125rem"`, `case` `"uppercase"`); `email-signup` with `heading` `""`, `border_style` `"underline"`, `input_style` `"custom"`, `border_width` `1`, `input_text_color` / `input_border_color` `"{{ settings.color_palette.background }}"`, `style_class` `"button-custom"`, `custom_button_background` `"{{ settings.color_palette.background }}"`, `custom_button_text` `"{{ settings.color_palette.foreground }}"`, `custom_button_border` `"{{ settings.color_palette.background }}"`, `display_type` `"text"`, `label` `"Submit"`; `text` "By submitting, you agree to the Terms & Conditions and Privacy Policy." (`font_size` `"0.75rem"`); `text` "Body care, reformatted." (`font` `"var(--font-heading--family)"`, `font_size` `"0.875rem"`, `case` `"uppercase"`).
2. `menu` `heading` "Company" (menu: About, Ingredients, Stores), `link_preset` `"paragraph"`, `show_as_accordion` `false`.
3. `menu` `heading` "Support" (FAQs, Shipping & Returns, Contact us, Accessibility).
4. `menu` `heading` "Community" (TikTok, YouTube, Instagram).
5. `jumbo-text`: `text` `"BARRIER"`, `font` `"heading"`, `alignment` `"center"`, `line_height` `"0.8"`, `letter_spacing` `"normal"`, `case` `"uppercase"`, `text_effect` `"none"`.

The three footer menus need creating in the admin (Online Store > Navigation).

### footer-utilities (legal row)
| Setting | Value |
| --- | --- |
| `background_color` | `"{{ settings.color_palette.foreground }}"` |
| `divider_thickness` | `0` |
| `padding-block-start` / `padding-block-end` | `56` / `24` |

Blocks: `footer-copyright` (`show_powered_by` `false`, `font_size` `"0.875rem"`), `footer-policy-list` (`font_size` `"0.875rem"`). Remove `social_icons` (Figma has no icons in this row).

## Layout
`{% render 'brand-overrides' %}` in `layout/theme.liquid` (and `layout/password.liquid` if the password page should match). Theme Check reports it as an orphaned snippet until then.
