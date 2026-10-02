# social-gallery

## Ticket
From docs/architecture.md (social-gallery). Figma: Insta component 978:4341 (WEB 978:4340, MOB 978:4339).
- "Follow on Instagram" heading, then a horizontally scrolling row of tiles on Linen, with an Instagram icon on one tile.
- CSS scroll-snap, no JS; images lazy-loaded; each tile links out (`rel="noopener"`, new tab).
- Blocks: `tile` with image and link. Manual images (D-4).
- Merchant can set heading, profile link, background colour and padding.

## Plan
- `sections/social-gallery.liquid`, a `<ul>` track with `overflow-x: auto` and `scroll-snap-type: x mandatory`; scrollbar hidden.
- Tiles 252 x 290 as in Figma (`calc(var(--space-112) * 2 + var(--space-24) + var(--space-4))` by `calc(var(--space-112) * 2 + var(--space-60) + var(--space-6))`); gap 16 desktop, 10 mobile. That shows about 5.4 tiles at 1440 and 1.5 at 390, as the frames do.
- Heading uses the H1 role (60/54 desktop, 32/1.1 mobile), left aligned, and links to the profile when set.
- Optional Instagram glyph (Horizon `icon` snippet), 20, White, bottom right.

## Reasoning
- **What:** a static, link-out gallery.
- **Why:** D-4 chose manual images, so no feed app or API; scroll-snap gives swipe without JS.
- **Alternatives rejected:** `slideshow-component` (adds JS for a row that only needs native scrolling); an Instagram app embed (D-4).
- **Impact:** the architecture's "2.3 tiles on mobile" differs from the Figma frame (1.5); built to Figma.
- **Approver:** Jeet (delegated).

## QA checklist
- [ ] Desktop 1440: heading 60 uppercase left at the gutter; row of 252 x 290 tiles, 16 apart, scrolls sideways and snaps.
- [ ] Mobile 390: heading 32 on two lines; tiles 10 apart, swipe snaps.
- [ ] Each tile opens its link (or the profile link) in a new tab with `rel="noopener"`; screen readers hear "Opens in a new window."
- [ ] Instagram icon only on tiles with it switched on.
- [ ] Images are lazy; keyboard focus on each tile is visible.

## Merchant guide
1. In the footer group, open "Social gallery"; set the heading and the Instagram profile link.
2. Add Tile blocks, upload a photo to each and optionally a post link (blank uses the profile link).
3. Tick "Show Instagram icon" on the tile that should carry the glyph.
4. Set the background colour to Linen and adjust padding.

## Figma diff 2026-10-02
Measured against HOMEPAGE 965:1253 and 965:3078. Deltas and fixes: `docs/qa/figma-diff-home.md`.
