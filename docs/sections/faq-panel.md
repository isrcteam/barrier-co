# faq-panel

## Ticket
From docs/architecture.md (faq-panel, FAQs component 978:4244, WEB 978:4243, MOB 978:4242):
- A background image with a Sandstone panel (Tan side bars on desktop) holding "Most asked questions", an accordion and a "Read more FAQ" button.
- Horizon `accordion-custom` with `<details>`; items from `faq_item` metaobjects (section setting, or the product's `custom.faq_items` on the PDP).
- Outputs FAQPage JSON-LD when on the PDP; the first item open by default (setting).
- Merchant configuration: image desktop and mobile, heading, source toggle, items, open first, button label and link, padding.

## Plan
- `sections/faq-panel.liquid`. Rows reuse Horizon's markup from `blocks/_accordion-row.liquid`: `<details class="details">` + `summary.details__header` + `.details-content`, wrapped by `accordion-custom-component`, with the `icon-plus` that animates to a minus.
- Source: `product.metafields.custom.faq_items` when "Use product data" is on and the product has items; otherwise the `faq_items` metaobject_list.
- JSON-LD: only when items come from the product, `<script type="application/ld+json">` with every value passed through `json` (answer is the rich text rendered, tags stripped).
- Background picture: desktop/mobile pair in one `<picture>`; side bars are inline borders in `--color-accent-bar`.

## Reasoning
- **What:** a FAQ accordion over an image, data-driven.
- **Why:** FAQs differ per product and feed rich results; metaobjects keep one source for the accordion and the structured data.
- **Alternatives rejected:** Horizon `section` + `accordion` block (questions would be typed per template and couldn't feed JSON-LD from data); a custom accordion script (`accordion-custom` already handles it).
- **Impact:** no new JS. JSON-LD only on product pages with product data, so the home page never claims FAQPage.
- **Approver:** Jeet (delegated).

## QA checklist
- [ ] Desktop: image fills the section, 160 above and below the panel; bars 30 wide each side; panel about 646 wide, 30 padding.
- [ ] Mobile: panel full width, 40/10 padding, image visible 60 above and below.
- [ ] First item open when "Open first question" is on; closed when off.
- [ ] Clicking or pressing Enter/Space on a question toggles it; the icon switches plus/minus; focus ring visible.
- [ ] Fossil hairline under every item (with divider color set).
- [ ] Button full width, links to the chosen URL; hidden without a label or link.
- [ ] PDP: page source has one FAQPage JSON-LD matching the questions; Rich Results Test passes. Home: no FAQPage.
- [ ] Empty data: placeholders in the editor only; nothing on the live page.

## Merchant guide
- Content > Metaobjects > FAQ item: add the question and answer.
- On each product, fill **FAQ items**; the PDP section shows them and adds FAQ rich results.
- Elsewhere, pick entries in **FAQ items** on the section. Set the background image (and a mobile one if needed), the button label and link.
