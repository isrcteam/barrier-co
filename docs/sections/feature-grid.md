# feature-grid

## Ticket
From docs/architecture.md (feature-grid). Figma: 787:9003 / 787:9428 ("Better materials, chosen from the inside out").
- Centred heading over a grid of features: icon, title, text.
- Desktop: two columns with Tan rules between rows and columns. Mobile: one column with a rule under each item.

## Plan
- `sections/feature-grid.liquid`, a `<ul>` grid. No JS.
- Content column 1312 wide (the Figma 65 inset at 1440), centred beyond.
- Desktop: icon 76, title 24, text 18 / 1.4. Mobile: icon 56, title 16, text 14 / 1.4, 16 gap.
- Rules are borders on the items; the first row and the first column drop theirs so lines only sit between items.

## Reasoning
- **What:** an icon-and-text grid with dividing rules.
- **Why:** feature-icons is a centred badge row; this is a left-aligned two-column list with rules.
- **Alternatives rejected:** Horizon's multicolumn (no rules, icon above text).
- **Impact:** **Desktop columns** (1–3) re-flows the grid and the rules follow.
- **Approver:** Jeet (delegated).

## QA checklist
- [ ] 1440: 2 × 2 grid, heading 60 centred, rules only between items, text column starts at 164.
- [ ] 390: one column, 16 page gutter, icon then text, a rule under every item but the last.
- [ ] An empty icon shows a soft square placeholder; icons have empty alt.
- [ ] **Anchor** `materials` makes `#materials` links land here.

## Merchant guide
1. Add a Feature block for each point: upload the icon (SVG or PNG), type the title (Enter for a line break) and the text.
2. Set **Desktop columns** to 2 for the design; padding and background as needed.
3. Give the section an **Anchor** if the hero labels link to it.
