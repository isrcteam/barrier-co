# image-carousel

## Ticket
From docs/architecture.md (image-carousel). Figma: Routine 965:1339 / mobile 965:3157; Lifestyle 965:1587 / mobile 965:3302.
- Heading (and optional subheading), then 3 or more cards with images.
- Desktop: the middle card is offset ("Routine") or taller ("Lifestyle"); Tan side bars at the page edges; arrows below.
- Mobile: one card per view, dots below; arrows hidden.
- Uses Horizon `slideshow-component` for paging, arrows and dots.
- Card label with bars ("| CLEANSE |") uses the `card_label` type role.
- Optional product overlay on a card renders `product-spotlight` with style `glass`.
- Merchant can set heading, subheading, background colour, side bars, middle card style and padding.

## Plan
- `sections/image-carousel.liquid`, section-local `card` blocks (image, label, caption, product, price label, button label). No new JS.
- Slides go through `slideshow` + `slideshow-slide`; controls are `slideshow-controls` (dots + arrows). CSS hides dots on desktop and arrows on mobile, and restyles dots as 6 square Tan dots (`--opacity-brand-inactive` when not selected).
- Desktop widths come from the slideshow container (`100cqi`): Even/Offset = three equal cards with a 60 gap; Tall = sides 30% and middle 40% of the card row with an 86 gap; the middle image is 6:7 (Figma 397 x 458). Every second card of each group of three is the "middle" card.
- Side bars sit outside the scroller in a three-column grid: 12 x 70 centred on the image on mobile, 30 wide and as tall as a side card on desktop (aligned to the side card image in Tall).
- Label bars are `::before`/`::after` (4 x 16, Figma 5 x 17) in White over the image.

## Reasoning
- **What:** one section with two presets rather than two sections.
- **Why:** both designs are the same component (cards, bars, paging) differing only in the middle card and caption style, so a select keeps one file and one stylesheet.
- **Alternatives rejected:** a custom carousel script (Horizon's slideshow already does paging, arrows and dots); absolute positioning from Figma (not fluid); a carousel-controls snippet (not built yet, Horizon's controls restyled locally instead).
- **Impact:** Lifestyle middle card offset values: Figma gaps 50 and 84 snapped to 60 and 86 (T-11); middle offset 100 is `calc(var(--space-80) + var(--space-20))`. Caption colour uses `--color-caption` (Ink, T-8) in both presets; Routine's Figma caption is Clay.
- **Approver:** Jeet (delegated).

## QA checklist
- [ ] Desktop 1440 Routine: heading 60/54 uppercase centred; three square cards, middle pushed down 100; Tan bars at both edges as tall as the cards; arrows bottom left and right.
- [ ] Desktop 1440 Lifestyle: subheading 18; middle card taller (6:7) with the glass product card at the bottom; side cards bottom-aligned with the middle image; captions left-aligned.
- [ ] Mobile 390: one card at a time, swipe pages, 6px square dots below with the active one solid; bars 12 wide centred on the image; no arrows.
- [ ] Card label shows "| LABEL |" in White, 18 on mobile and 24 on desktop.
- [ ] Glass product card shows title, "Starts from" price and Shop now; hidden when no product is chosen.
- [ ] More than three cards: arrows scroll on desktop, dots count matches cards on mobile.
- [ ] Keyboard: arrows and dots reachable with a visible focus ring; reduced motion turns smooth scrolling off.
- [ ] Turning off "Show side bars" removes the bars and the cards fill the width.

## Merchant guide
1. Add "Image carousel: Routine" or "Image carousel: Lifestyle" from the Storytelling category.
2. Edit the heading (press Enter for a line break), heading tag and optional subheading.
3. Add or reorder Card blocks: image, optional label (shown with bars over the image) and caption.
4. To show a product over a card, choose a product in the card's "Product overlay" fields; edit the price label ([price] is filled in) and the button label.
5. Choose the middle card style (Even, Offset, Tall), side bars, caption alignment and size.
6. Set the background colour (Linen for Routine, blank for Lifestyle) and padding.

## Figma diff 2026-10-02
Measured against HOMEPAGE 965:1253 and 965:3078. Deltas and fixes: `docs/qa/figma-diff-home.md`.

## Changes 2026-10-06 (internal QA and Dev Ready)
- **Show arrows** (off for Routine, QA 8) and **Background on mobile only** (Routine's Linen band, QA 7).
- **Arrows bring the next card to the centre** and **Show product on hover** for Lifestyle (annotations 5 and 6, QA 22 and 23).
