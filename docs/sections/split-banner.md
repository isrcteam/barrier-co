# split-banner

## Ticket
From docs/architecture.md (split-banner). Figma: Sustainablity desktop 787:9003, mobile 787:9428 (hero).
- Two image tiles side by side under a centred "| BARRIER |" logotype; each tile has an underlined label that links to a section of the page.
- Mobile: tiles stack, each 220 high, label centred.
- Holds the page's h1, visually hidden.

## Plan
- `sections/split-banner.liquid`, a `<ul>` of tiles (up to 3). Each tile is one `<picture>` (mobile source when **Same at mobile** is off). First-section images load eager and high priority.
- Logotype bars drawn with `::before` / `::after` in the text colour.
- Height range 320–900 (670 default) on desktop; **Height on mobile** is the height of each stacked tile.

## Reasoning
- **What:** a dedicated hero for landing pages.
- **Why:** the hero-banner section is a single image with a text block; this design is a split of linked tiles with a logotype over them.
- **Alternatives rejected:** two hero-banner sections side by side (Shopify sections can't sit side by side); Horizon's collage (no logotype, different label style).
- **Impact:** the page h1 comes from the hidden heading or the page title, so there is one h1 even though no heading is visible.
- **Approver:** Jeet (delegated).

## QA checklist
- [ ] 1440: two tiles, 670 high, labels at the top corners, logotype centred between bars.
- [ ] 390: tiles stacked, 220 each, logotype over the first tile, labels centred.
- [ ] A label with a link of `#materials` scrolls to the feature grid.
- [ ] Turning **Same at mobile** off and choosing a mobile image swaps the image below 990 only.
- [ ] The page has exactly one h1 (hidden), read by a screen reader.

## Merchant guide
1. Add a Tile block per image (two or three). Upload the image and type the label; set the link to a page section (for example `#mail-back`) or any URL.
2. For a different crop on phones, turn off **Same at mobile** and pick the mobile image.
3. Set the height for desktop and the height of each tile on mobile.
4. Leave **Page heading** blank to use the page title as the hidden h1.
