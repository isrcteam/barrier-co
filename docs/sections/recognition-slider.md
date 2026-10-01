# recognition-slider

## Ticket
From docs/architecture.md (recognition-slider). Figma: 965:2147 (overlay 965:2904), mobile in 965:3468.
- "Recognition by" seals with logo and text, one per slide, with dots.
- Horizon `slideshow-component` (no new JS); hairline Fossil border.
- Data: `product.metafields.custom.recognitions`. Setting: heading.

## Plan
- Theme block `blocks/recognition-slider.liquid`; Horizon `slideshow`, `slideshow-slide`, `slideshow-controls` (dots, only when there's more than one).
- Card: 8/12 padding, 12 gap, logo 30 wide, text `caption` with the title in the heading face, medium, uppercase.
- Dots: Tan squares from brand-overrides; start aligned with a 6 gap here.
- Heading tag setting (default p, as it's a small label).

## Reasoning
- **What:** a metaobject-driven slider.
- **Why:** recognitions are reused across products (data model).
- **Alternatives rejected:** a new carousel script (Horizon's slideshow covers it).
- **Impact:** The Fossil border reads `var(--color-input-border)`, which Horizon fills from `palette_input_border` (Fossil), as brand-overrides does. Dot colours come from brand-overrides; this block only aligns them to the start with a 6 gap. Logo 33x45 snapped to 30 wide.
- **Approver:** Jeet (delegated).

## QA checklist
- [ ] One recognition: card shows, no dots.
- [ ] Two or more: swipe/scroll pages one card at a time; dots track the slide and can be clicked.
- [ ] Empty metafield: nothing renders.
- [ ] Logo alt is the recognition title.
- [ ] Dots have "Slide X of Y" labels and a visible focus ring.

## Merchant guide
1. Create entries in Content > Metaobjects > Recognition (title, description, logo).
2. On each product, pick them in the "Recognitions" metafield.
3. Add "Recognition slider" to the product details and edit the heading.
