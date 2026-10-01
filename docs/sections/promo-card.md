# promo-card

## Ticket
From docs/architecture.md (promo-card). Figma: 965:2157 (desktop), in 965:3468 (mobile).
- The quiz card: image, heading and text, with a small button ("Take the test").
- A row on desktop, stacked on mobile; the button uses the Small size.
- Settings: image, heading, text, button label, button link, background colour.

## Plan
- Theme block `blocks/promo-card.liquid`, no JS; `contrast-override` scoped to the block id.
- Grid: desktop `image | body | button`; mobile `image | body`, with the button on its own row, start aligned.
- Image 70 square; heading `h6` role uppercase; text `caption`; button `label` role, Small height (`--layout-button-small`), 20 inline padding.
- Heading tag setting (default h2) separate from its size.

## Reasoning
- **What:** a compact card block.
- **Why:** single-placement copy stays in block settings.
- **Alternatives rejected:** a stock group with image, text and button blocks (no mobile reflow of the button).
- **Impact:** image size 70 has no token: `calc(var(--space-60) + var(--space-10))`. The Figma button is 31 high; it uses the Small size (40) per T-19.
- **Approver:** Jeet (delegated).

## QA checklist
- [ ] Desktop: white card, 12 padding, 70 image, heading and text, Clay button on the right.
- [ ] Mobile: button below, left aligned.
- [ ] No button link: no button renders.
- [ ] Heading tag setting changes the element only, not the size.
- [ ] Button focus ring visible.

## Merchant guide
1. Choose the image, edit heading and text, and set the button label and link (for example the quiz page).
2. Set "Background color" (White in the design).
