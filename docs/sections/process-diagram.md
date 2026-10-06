# process-diagram

## Ticket
From docs/architecture.md (process-diagram). Figma: 787:9003 / 787:9428 ("VEOCEL™ Lyocell production process").
- Heading and text over a diagram: wood → pulp → a cycle (water, fibre production, solvent) → Veocel lyocell fibres.
- Desktop: one horizontal row. Mobile: wood and pulp stacked on the left, the cycle on the right, the result below.
- An (i) beside "Solvent" reveals ">99%" and a note.

## Plan
- `sections/process-diagram.liquid`. Artwork is inline SVG from `assets/icon-process-wood.svg`, `-pulp`, `-arrow`, `-cycle` and `logo-veocel.svg`, so it takes the text colour.
- Labels are live text from settings; the layout is a CSS grid placed per breakpoint (aspect ratio 1091 / 310 on desktop).
- The note is a CSS-only tooltip on a `<button>` (hover and focus), described by the note text.
- Desktop body 18, mobile 14 with a 22 inset (Figma 312 wide text).

## Reasoning
- **What:** a coded diagram with editable labels.
- **Why:** in Figma the labels are outlined vectors; a single exported SVG would make the copy uneditable and unreadable to screen readers and search.
- **Alternatives rejected:** one SVG image (labels frozen, no translation); an image per breakpoint (two files to keep in sync).
- **Impact:** Sandstone on Tan is about 2.9:1, under WCAG 4.5:1. Kept as drawn and flagged (plan D-24); text colour is a setting.
- **Approver:** Jeet (delegated).

## QA checklist
- [ ] 1440: one row, labels 14, heading 60, text 18 centred, max 896.
- [ ] 390: two-column layout as in the mobile frame, labels 10, text 14.
- [ ] Hover or Tab to the (i): the ">99%" note shows, and hides again when the pointer or focus moves away; the button has an accessible name.
- [ ] Changing a label updates the diagram; a long label wraps without overlapping the arrows.
- [ ] **Result logo** replaces the Veocel logo when set.

## Merchant guide
1. Edit the heading and text; the diagram labels are under **Diagram**.
2. The info note under **Info note** is what shows when shoppers hover or tap the (i).
3. Change background and text colour together and check the labels stay readable.
