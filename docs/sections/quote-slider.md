# quote-slider

## Ticket
From docs/architecture.md (quote-slider). Figma: Clinical trial component 978:3947 (WEB 978:3946, MOB 978:3945).
- "Read the clinical trial" quotes: quote mark, text, round avatar, name and role, with dots.
- Horizon `slideshow-component`; a Linen card; avatar uses `--radius-full`.
- Data: `product.metafields.custom.testimonials`. Settings: heading, background colour.

## Plan
- Theme block `blocks/quote-slider.liquid`; Horizon `slideshow` with dots (only when more than one quote).
- Each slide is a `figure` with `blockquote` and `figcaption`. Quote mark in the heading face, extrabold, `h2` size (24/36), Tan; quote `body`; name `h5` uppercase; role `caption`.
- Card colour is the block's background colour through `contrast-override` scoped to the block id; the card paints `--color-background`.
- Dots take their colours from brand-overrides; this block aligns them to the start with a 6 gap.

## Reasoning
- **What:** a metaobject-driven quote slider.
- **Why:** testimonials repeat across products and the home page (data model).
- **Alternatives rejected:** new JS (Horizon slideshow is enough).
- **Impact:** avatar 41 snapped to 40 (`--space-40`); card gap 19 snapped to 20.
- **Approver:** Jeet (delegated).

## QA checklist
- [ ] Linen card with 12 padding; Tan quote mark; quote text; 40 round avatar; name and role.
- [ ] Two or more quotes: dots below, start aligned, Tan squares.
- [ ] Empty metafield: nothing renders.
- [ ] Blank background colour: card takes the page background.
- [ ] Heading tag setting changes the element only.

## Merchant guide
1. Create entries in Content > Metaobjects > Testimonial (name, quote, role, avatar).
2. On each product, pick them in the "Testimonials" metafield.
3. Add "Quote slider" to the product details, edit the heading and set "Background color" (Linen in the design).
