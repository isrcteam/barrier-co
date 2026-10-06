# feature-icons

## Ticket
From docs/architecture.md (feature-icons). Figma: 965:1502 / mobile 965:3293.
- Four round badge icons ("100% proven") with two-line captions.
- Desktop: one row, max width 1150, centred. Mobile: 2 x 2 grid.
- Blocks: `item` with an icon image (SVG) and caption.
- Merchant can set desktop columns (2–6), background colour and padding.

## Plan
- `sections/feature-icons.liquid`, a `<ul>` grid. No JS.
- Max width `calc(var(--space-112) * 10 + var(--space-30))` = 1150. Desktop column gap 86 (Figma 90); mobile gaps 30 rows / 10 columns as in Figma.
- Icon box 110 (`calc(var(--space-86) + var(--space-24))`), caption 16 on both sizes (body-large size on mobile, body size on desktop), balanced wrapping, max 224 wide.

## Reasoning
- **What:** a simple list section with image icons.
- **Why:** the badges are illustrated SVGs with curved text, so they are uploaded images rather than icon-font glyphs.
- **Alternatives rejected:** Horizon's "Icons with text" blocks (no round badge image, different layout); fixed line breaks in captions (the design breaks differently on mobile), so captions use `text-wrap: balance`.
- **Impact:** icon to caption gap 16 (Figma 18).
- **Approver:** Jeet (delegated).

## QA checklist
- [ ] Desktop 1440: four badges in one row, total width 1150 centred; captions 16 centred under each.
- [ ] Mobile 390: 2 x 2 grid, 30 between rows.
- [ ] Desktop columns setting 2–6 changes the row.
- [ ] Empty icon shows a round placeholder; icons have empty alt (decorative, the caption carries the meaning).
- [ ] Mobile padding defaults to 30; "Same at mobile" applies the desktop values.

## Merchant guide
1. Add "Feature icons" and upload each badge SVG to its Feature block.
2. Type the caption; it wraps evenly on its own (press Enter to force a line break).
3. Set desktop columns to match the number of features, the background colour and padding.

## Figma diff 2026-10-02
Measured against HOMEPAGE 965:1253 and 965:3078. Deltas and fixes: `docs/qa/figma-diff-home.md`.

## Changes 2026-10-06 (internal QA and Dev Ready)
- Optional **Heading** and **Text** above the icons, and **Icon height**, so the section can show the sustainability certification logos.
- Captions with a typed line break keep those lines exactly (QA 19); a last odd item spans the row on mobile.
- Per-icon **Icon height** (0 uses the section's): balances wide and tall logos, for the sustainability certifications. On mobile every icon fits a square of the section's icon height, so wide logos shrink as in the mobile frame; square badges are unaffected.
