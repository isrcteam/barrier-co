# product-highlights

## Ticket
From docs/architecture.md (product-highlights). Figma: buy box 965:2045, mobile 965:3468.
- A ticked list of selling points: a `<ul>` with Horizon's `icon-checkmark`.
- Data: `product.metafields.custom.highlights`. Hidden when empty.

## Plan
- Theme block `blocks/product-highlights.liquid`, no JS, no settings beyond an info paragraph.
- Check icon 12 (`--icon-xs`) in Tan (`--color-accent-bar`), 10 gap, 6 row gap.

## Reasoning
- **What:** a metafield-driven list.
- **Why:** highlights are per product (data model).
- **Alternatives rejected:** a text block with a rich-text list (no icon, copy would live in the template, not the product).
- **Impact:** the type is `caption` (12), as in Figma desktop and mobile, not `body_small` (14) as the architecture entry says.
- **Approver:** Jeet (delegated).

## QA checklist
- [ ] Product with highlights: one ticked row per item, 12 text, Tan ticks.
- [ ] Product without highlights: nothing renders.
- [ ] Long items wrap with the tick aligned to the row.

## Merchant guide
1. In the product admin, fill "Highlights" (one line per point).
2. Add "Product highlights" to the product details where the list should show.
