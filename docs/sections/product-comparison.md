# product-comparison

## Ticket
From docs/architecture.md (product-comparison). Figma: Dev Ready 776:4700, Homepage Final ("compare"), annotation "to be developed and language to be carried forward on Collection page".
- Heading, text and a product card on the left; a comparison table of product columns (one dark) on the right, with product images overlapping the top edge, ticked points and a button per column. Mobile: heading, table, then the card.

## Plan
- `sections/product-comparison.liquid` renders each column with `snippets/comparison-column.liquid`, which `product-showcase` (collection) also uses, so both tables match.
- Points: when **Use product comparison points** is on and the product's `custom.comparison_points` list is filled, those lines; otherwise the block's **Points** (one per line).
- Ticks use the `--icon-tick` token.

## Reasoning
- **What:** a shared column snippet and a home section around it.
- **Why:** the annotation asks for the same table and wording on the homepage and the collection page.
- **Alternatives rejected:** copying the collection table markup into a new section (two copies to keep in sync).
- **Impact:** the metafield definition and values are prepared in docs/data but not yet created in the store (plan D-20); until then the block text shows.
- **Approver:** Jeet (delegated).

## QA checklist
- [ ] 1440: heading and card on the left; table on the right with the dark column first and thumbnails overlapping its top edge.
- [ ] 390: heading, then the two columns side by side with their rows lined up, then the card.
- [ ] With the metafield filled, the homepage and collection tables show the same points.
- [ ] Buttons go to each product.

## Merchant guide
1. Add a Column block per product, choose the product, and tick **Dark column** for the highlighted one.
2. Fill the product's **Comparison points** metafield to share the wording with the collection page, or type points in the block (one per line).
3. Choose the card product, its price label (`[price]` becomes the lowest price) and button label.
