# step-timeline

## Ticket
From docs/architecture.md (step-timeline). Figma: 787:9003 / 787:9428 (how it works).
- Centred eyebrow, heading and intro; then numbered steps on a vertical rail beside an image.
- Finished steps are solid on a solid rail; the rest are faded on a dashed rail.

## Plan
- `sections/step-timeline.liquid`, an `<ol>` of steps with the rail and dots drawn by pseudo-elements. No JS.
- **Steps done** sets how many steps are solid (0 = all the same).
- Desktop: a 453 steps column beside a 380 image column, centred under the header; mobile: image first, then the header, then steps 38 in from the rail.
- Step titles 24 desktop, 20 mobile; labels 16 / 14; intro 20 / 14.

## Reasoning
- **What:** an ordered steps list with progress styling.
- **Why:** no Horizon section draws a progress rail.
- **Alternatives rejected:** accordion rows (the steps are meant to be read in order, all open).
- **Impact:** a title link (step 1) is underlined like a link; faded steps keep their links working.
- **Approver:** Jeet (delegated).

## QA checklist
- [ ] 1440: header centred, steps left, image right, rail solid to step 2 and dashed to step 3.
- [ ] 390: steps at x 54, rail at 24, step titles 20, faded step 3.
- [ ] **Steps done** 0 shows every step solid; 3 shows all three solid.
- [ ] Screen readers announce the steps as a list of three.

## Merchant guide
1. Add a Step block per step: label (for example "Step 01"), title, optional title link, text, and an optional link under it.
2. Set **Steps done** to how many steps should look complete.
3. Upload the image; leave it empty for a single column.

## Changes 2026-10-06
- **Animate the steps** (default on): as soon as the section's top edge reaches the screen, a line grows from the first dot to the last in 1.5s, whether or not the shopper keeps scrolling (`--step-progress` × `--step-rail-length`, measured by `assets/step-timeline.js` and kept right on resize) and each step lights up as the line reaches it. Plays once. Reduced motion, the theme editor and no-JavaScript show the static **Steps done** look.
