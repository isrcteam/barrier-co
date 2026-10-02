# before-after

## Ticket
From docs/architecture.md (before-after). Figma: home 965:1614 / 965:3328, PDP 965:2350 / 965:3769.
- Heading, text and a product mini card on the left; on the right a before and after image pair with labels and a testimonial card underneath, paged with arrows (dots on mobile).
- Slides are `before_after` metaobjects (section setting, or `product.metafields.custom.before_afters` on the PDP).
- Uses `slideshow-component`; labels are white chips using the `label` type role; the mini card is `product-spotlight` (row).
- Merchant can set heading, text, product, source toggle, comparisons list, background colour and padding.

## Plan
- Section `sections/before-after.liquid`, no JS. Horizon `slideshow` + `slideshow-controls` (arrows on desktop, square Tan dots on mobile), one comparison per slide.
- Desktop grid: intro column `calc(var(--space-112) * 4 - var(--space-20))` (428, as in Figma) and the slider in the rest, 80 gap. Mobile stacks with a 24 gap.
- Images are 3:4 on mobile and 43:45 on desktop (Figma 179 x 240 and 430 x 450), each with a label chip 4 in from the top left. Labels default to "Before" and "After" (storefront keys).
- The testimonial card reads the comparison's `testimonial` reference: quote, avatar (40), stars, name, role.
- The product card and testimonial card share a "Card background" surface through a second `contrast-override` scoped to `<section id>-card` (Linen in the design).
- Product: the section's product setting; when blank on a product page, the current product.

## Reasoning
- **What:** a two-column section with a reused product-spotlight and a Horizon slideshow of metaobject slides.
- **Why:** comparisons and testimonials repeat between home and PDP, so they live in metaobjects.
- **Alternatives rejected:** Horizon's `comparison-slider` (drag reveal) doesn't match the side-by-side design. A fixed Linen fill was rejected because hex isn't allowed in Liquid; it's a colour setting instead.
- **Impact:** product-spotlight is adjusted only inside this section (124 image tile, 12 padding, 60 end padding on desktop, multiply blend on the packshot). Label chip text uses the section foreground.
- **Approver:** Jeet (delegated).

### 2026-10-02: Card size setting
- **What:** `card_size` select: Compact (default) and Large; the PDP template uses Large. Desktop only; mobile is compact in both frames.
- **Why:** The home frame draws a compact product card and the PDP frame a large one (design-corrections P11).
- **Alternatives rejected:** Two separate sections (duplicate code); one size everywhere (contradicts one of the frames).
- **Impact:** None.
- **Approver:** Jeet (delegated)

## QA checklist
- [ ] Desktop 1440: heading 60 uppercase, muted body text, product card on Linen, comparison on the right; arrows at the edges below; first-slide previous arrow hidden.
- [ ] Mobile 390: stacked; product card full width; image pair 3:4; dots centred below.
- [ ] Labels show the metaobject's labels, or "Before" and "After" when empty.
- [ ] Testimonial card shows quote, avatar, stars, name (and role when filled); hidden when the comparison has no testimonial.
- [ ] PDP with "Use product data": the product's comparisons show; product card shows the current product when no product is chosen.
- [ ] Product card price line shows "Starts from" with the lowest price (selling plan or product).
- [ ] Keyboard focus visible on arrows, dots and the Shop now button.

## Merchant guide
1. Add comparisons in Content > Metaobjects > Before and after: title (admin only), before and after images, optional labels (for example "After · Day 14") and an optional testimonial.
2. In the theme editor, open "Before and after", edit the heading and text, and choose a product for the mini card (leave it blank on the product template to show the current product).
3. Pick comparisons under "Comparisons". On the product template, turn on "Use product data" to use each product's "Before and afters" metafield.
4. Set "Card background" (Linen in the design) and the section background, then adjust padding.

## Figma diff 2026-10-02
Measured against HOMEPAGE 965:1253 and 965:3078. Deltas and fixes: `docs/qa/figma-diff-home.md`.
