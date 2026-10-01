# clinician-proof

## Ticket
From docs/architecture.md (clinician-proof). Figma: 965:2075 (desktop), in 965:3468 (mobile).
- A strip with a "Clinicians' Choice" laurel mark, a text line, up to 3 avatar images (26) and a "View clinicians" link.
- Mark is an image setting (SVG from the asset pack); text is inline_richtext.
- Settings: mark image, text, avatars 1–3, link label, link URL, background colour.

## Plan
- Theme block `blocks/clinician-proof.liquid`, no JS; own `contrast-override` scoped to the block id.
- Desktop: mark | text | avatars over link (right aligned). Mobile: mark | text, then avatars and link in a row (as in 965:3468).
- Mark divider: hairline Tan on the inline end. Mark image 24 high. "Mark text" is the image alt, and shows as text when there's no image.

## Reasoning
- **What:** a self-contained strip block.
- **Why:** copy and images belong to this placement, so they're block settings.
- **Alternatives rejected:** a stock group with image and text blocks (can't produce the mobile reflow or the divider).
- **Impact:** avatar size 26 has no token: `calc(var(--space-24) + var(--space-2))`. Avatars are square, as in Figma.
- **Approver:** Jeet (delegated).

## QA checklist
- [ ] Desktop: Linen strip, 10 padding, mark with Tan divider, text 12, three 26 avatars 2 apart, "VIEW CLINICIANS" underlined below them.
- [ ] Mobile: avatars and link move to a second row.
- [ ] Blank background shows the page background.
- [ ] No avatars or link: the strip still lays out.
- [ ] Link focus ring visible; mark image has alt text.

## Merchant guide
1. Upload the laurel lockup SVG as "Mark image" and keep "Mark text" as its description.
2. Edit the text, choose up to three avatars, and set the link label and URL.
3. Set "Background color" (Linen in the design).
