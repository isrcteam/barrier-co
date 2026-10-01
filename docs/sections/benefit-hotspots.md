# benefit-hotspots

## Ticket
From docs/architecture.md (benefit-hotspots, PDP 965:2198 / mobile 965:3615):
- Left: a Linen panel with a heading and a product image with dotted callout lines to labels and text (Cleanse, Hydrate, Protect).
- Callouts are section blocks with x/y position (range, %), label and text; lines are CSS borders.
- On mobile the panels stack and the callouts become a list under the image.
- Right: a photo with a glass card holding a heading and text; several messages page through Horizon `slideshow-component` with dots.
- Merchant configuration: heading, product image, photo, background colour, padding.

## Plan
- `sections/benefit-hotspots.liquid`, blocks `callout` (label, text, x, y, line length) and `message` (heading, text).
- Panel colours through a second `contrast-override` call (`<section id>-panel`) fed by `panel_color` and `panel_text_color`.
- Desktop: panel is a size container; each callout sits at x/y, its dot and dotted line come from `::before`/`::after`, the line width is `line_length × 1cqi`.
- Mobile: markers hidden, callouts render as a plain list under the image.
- Messages: one message renders static; two or more render Horizon's `slideshow` + `slideshow-controls` (dots), restyled to square 6 dots.

## Reasoning
- **What:** a two-column benefits section with positioned callouts and a glass message card.
- **Why:** callout copy and positions must be editable per product; blocks with % positions survive image swaps and keep the lines in CSS, not baked into the image.
- **Alternatives rejected:** Horizon `product-hotspots` (it shows product popovers, not labelled callouts with lines); SVG lines (not editable); a custom carousel (Horizon's slideshow covers it, so no new JS).
- **Impact:** no new JS, CSS only in this file. Panel colour needs `panel_color` (Linen) and `panel_text_color` (Sepia) set in the template.
- **Approver:** Jeet (delegated).

## QA checklist
- [ ] Desktop 1440: panel 3fr, photo 2fr, both about 620 high; heading top-left in Sepia over the image.
- [ ] Each callout's dot sits at its x/y; the dotted line runs right to a white label chip; text sits under the chip.
- [ ] Changing a callout's x, y or line length in the editor moves it live.
- [ ] Mobile 390: heading centred above the image; no dots or lines; callouts listed under the image (chip, then text).
- [ ] Photo has the 30% dark overlay; glass card at the bottom with white centred heading and text.
- [ ] Two or more messages: dots appear, swipe and dot clicks change messages, dots are keyboard focusable with a visible ring. One message: no dots.
- [ ] Blank `background_color` shows Sandstone; `panel_color` Linen and `panel_text_color` Sepia match Figma.
- [ ] Padding settings and the "Same at mobile" toggle work.
- [ ] Reduced motion: slides change without smooth scrolling.

## Merchant guide
- Add "Benefit hotspots" to the product page. Upload the product image (and a mobile crop if needed) and the photo.
- Each **Callout** block is one label: type the label and text, then drag Horizontal and Vertical position until the dot sits on the product, and set Line length so the label clears the image.
- Each **Message** block is one slide in the glass card. Add more than one to show dots.
- Panel color and panel text color set the left panel; Background color sets the gaps around it.
