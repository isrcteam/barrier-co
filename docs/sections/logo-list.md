# logo-list

## Ticket
From docs/architecture.md (logo-list). Figma: logo bar inside 965:1652 (965:1668), mobile 965:3381.
- A row of partner or stockist logos. Spaced out on desktop; Horizon `marquee-component` scrolls them on mobile.
- Blocks: `logo` with image, alt and link.
- Merchant can set logo height, scroll on mobile, background colour and padding.

## Plan
- `sections/logo-list.liquid`. With "Scroll on mobile" on, logos sit in `marquee-component` (loads `assets/marquee.js`, Horizon's own); otherwise a static list.
- Mobile: marquee animation (own keyframes so the section doesn't depend on the marquee section's stylesheet), 60 gap. Desktop: animation off, clones hidden, one row with `space-between` across the content width (Figma: 24 top and bottom, gutter 30).
- Logo height setting (16–80, default 32) sets the image height; width follows the file.

## Reasoning
- **What:** a logo row that reuses Horizon's marquee script.
- **Why:** the design scrolls on mobile only; the marquee component handles cloning and speed.
- **Alternatives rejected:** the stock marquee section (no desktop static mode and it's disabled in the footer group); a CSS-only marquee (needs duplicated markup by hand).
- **Impact:** marquee.js loads only when the setting is on. Reduced motion stops the animation and makes the row scrollable instead.
- **Approver:** Jeet (delegated).

## QA checklist
- [ ] Desktop 1440: logos in one row spread edge to edge inside the 30 gutter, 32 high, no movement.
- [ ] Mobile 390: logos scroll continuously; hover/touch slows them (Horizon behaviour).
- [ ] "Scroll on mobile" off: logos wrap and centre on mobile.
- [ ] Reduced motion: no animation, row scrolls by swipe.
- [ ] Each logo has alt text (the Alt text field or the image alt); linked logos show a focus ring.

## Merchant guide
1. In the footer group, open "Logo list" and add a Logo block per brand: upload the logo (transparent PNG or SVG), type the brand name in Alt text, and add a link if wanted.
2. Set the logo height so the logos look balanced.
3. Turn "Scroll on mobile" off to show a static wrapped grid on phones.
4. Leave the background blank for Sandstone and adjust padding.

## Figma diff 2026-10-02
Measured against HOMEPAGE 965:1253 and 965:3078. Deltas and fixes: `docs/qa/figma-diff-home.md`.

## Changes 2026-10-06 (internal QA and Dev Ready)
- Per-logo **Logo height** to balance wide and tall logos (QA 27); 0 uses the section height.
