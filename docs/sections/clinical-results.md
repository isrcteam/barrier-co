# clinical-results

## Ticket
From docs/architecture.md (clinical-results). Figma: STATS component 978:4053 (WEB 978:4052, MOB 978:4051).
- "Clinically proven": background image, heading, text and a white button on the left; a 2 x 2 glass grid of stats (big number, unit, caption) on the right. Stacked on mobile.
- Stats come from `clinical_result` metaobjects: the section's metaobject list, or `product.metafields.custom.clinical_results` on the PDP.
- Glass: `--color-glass` at `--opacity-brand-glass`, `backdrop-filter: blur(var(--layout-blur-glass))`, white borders at `--opacity-brand-glass-border`.
- Numbers use the `stat` and `stat_unit` type roles.
- Merchant can set desktop and mobile images, heading, text, button label and link, source toggle, results list, inset width and padding.

## Plan
- Section `sections/clinical-results.liquid`, no JS.
- Panel with the image absolutely behind the content in one `<picture>` (desktop `<source>` at 990px, mobile `image_tag`). Eager with high fetch priority only when the section is first on the page.
- Content grid: 3fr / 7fr columns on desktop with a 30 gap (Figma 394 / 924), stacked with a 20 gap on mobile.
- Stat cards: 2 columns at every width; inner hairline dividers only (right edge of odd cards, top edge of the second row), as in Figma.
- Unit falls back to "%" when the metaobject's unit is empty (data-model.md). Only the first four results render.
- "Inset width" on: on desktop the panel sits inside the page gutter at content width (1380). Mobile is always full bleed, as in the MOB frame.

## Reasoning
- **What:** one section with an image panel, intro copy and a stat grid fed by metaobjects.
- **Why:** the same results show on the home page and the PDP, so they're metaobjects with a per-product override.
- **Alternatives rejected:** Horizon's `section` with text blocks can't read a metaobject list. A separate white-button variant in the global button styles was rejected for now; the white button is scoped to this section by overriding the primary button variables locally.
- **Impact:** text over the image is fixed White. The button's text uses the section's foreground (Clay on a blank or Sandstone background). Values with no token: the button's minimum width is `calc(var(--space-112) * 2 + var(--space-30))` (254, Figma 253).
- **Approver:** Jeet (delegated).

## QA checklist
- [ ] Desktop 1440 with inset on: panel 1380 wide inside 30 gutters, 60/30 inner padding, intro left and the 2 x 2 grid right, both vertically filled.
- [ ] Desktop with inset off: panel spans the page width (max 1440).
- [ ] Mobile 390: full bleed, heading 32, text 16, button, then the 2 x 2 grid; numbers 64, unit 44, caption 14.
- [ ] Glass: translucent oat fill with blur; dividers only between cards.
- [ ] PDP with "Use product data": the product's results show; with none, the section list shows.
- [ ] Result with no unit shows "%".
- [ ] Button: white with Clay text; hover and pressed reduce opacity; keyboard focus shows outline and ring.
- [ ] As the first section, the image loads eagerly; elsewhere it lazy-loads.

## Merchant guide
1. Add results in Content > Metaobjects > Clinical result (caption title, number, optional unit; leave unit blank for "%").
2. In the theme editor, open "Clinical results", choose an image (and a mobile image after turning off "Same at mobile"), then edit heading, text, button label and link.
3. Pick up to four results. On the product template, turn on "Use product data" to use each product's "Clinical results" metafield.
4. Turn "Inset width" off to run the image edge to edge on desktop. Adjust padding as needed.

## Figma diff 2026-10-02
Measured against HOMEPAGE 965:1253 and 965:3078. Deltas and fixes: `docs/qa/figma-diff-home.md`.

## Changes 2026-10-06 (internal QA and Dev Ready)
- **Count up the numbers** (QA 15). The real numbers are in the HTML; the script only counts when it can animate, and never for reduced motion.
- Captions balance to two lines (QA 18); dividers use the faded opacity (QA 17).
