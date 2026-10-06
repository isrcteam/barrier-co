# product-showcase

## Ticket
A two-product store needs a collection page that presents both products properly rather than as two small grid cards (Jeet, 2026-10-02). He chose the side-by-side panels plus comparison option. Acceptance:
- Equal-width editorial panels, one per product.
- Each panel shows: image, title, one-line purpose, highlights, a "starts from" price with the price per cloth, and a Shop button.
- A comparison table: cloths per pack, best for, price per cloth, subscribe & save, plus custom rows.
- Products come from the collection automatically (flagship first), or from blocks when used off a collection.
- Panels stack on mobile.

## Plan
- **Data:**
  - `descriptors.subtitle` (Shopify standard) for the purpose line.
  - `custom.cloth_count` and `custom.best_for`, both new.
  - `custom.highlights` and `custom.media_badge`, both existing.
  - Selling plans for the subscription row and the lowest price.
- **Template:** `templates/collection.json`, the only section on the collection page. It replaces Horizon's grid, which only showed two small cards.

## Reasoning (2026-10-02)
- **What:** a new curated section. Panels sit 50/50 on tablet and desktop. The panel body stacks below 1600 so titles keep one or two lines; above 1600 the price and button sit beside the copy. The price row is pinned to the panel bottom so both panels align.
- **Why:** with two products, a grid leaves the page empty and doesn't answer "which one should I buy?". The comparison does.
- **Alternatives rejected:**
  - Hero + companion: favours one product.
  - A table on its own: less editorial.
- **Impact:**
  - The collection page no longer lists products in a grid. If the catalogue grows past four products, re-add `main-collection` below the showcase.
  - The table needs `cloth_count` and `best_for` filled on each product; empty values show "–".
- **Approver:** Jeet.

## QA checklist
- [ ] `/collections/all` at 1440: both panels equal height; price rows aligned; flagship (highest price) first.
- [ ] At 1920 and 2000: panels and table on the 1860 grid.
- [ ] At 390: panels stacked; the table readable without horizontal page scroll (the table scrolls inside its own box if needed).
- [ ] Price per cloth = lowest price (selling plan or one-time) ÷ cloth count.
- [ ] Subscribe & save shows a tick once Recharge plans exist on the product.
- [ ] Off a collection (e.g. on a page), add product blocks: their image, if set, replaces the product image.

## Merchant guide
- **Content:** each product's purpose line is its Subtitle; cloths per pack and "Best for" are product fields under Custom data. Highlights are the same ticked points as on the product page.
- **Section settings:** heading, labels and comparison rows. "Order" puts the highest price first by default.
- **Extra comparison rows:** add a "Comparison row" block and type one value per product, in the order the products appear.

### Reasoning, 2026-10-02: comparison redesign, panel content, Shop mega menu
- **Comparison:**
  - A visible "Compare the cloths" heading; product column headers with a thumbnail, name and "starts from" price.
  - The first (flagship) column is tinted Linen with a Tan "Most popular" flag.
  - Cloth counts are set large; ticks sit in Tan circles; when a product has no plans it says "One-time only" rather than a bare dash.
  - Shop buttons in the footer row: primary for the flagship, outline for the rest.
  - Jeet's feedback: the plain table looked dull.
- **Panels:** The 8 had no highlights, so its panel looked empty beside the flagship. Four placeholder highlights were added to The 8 (D-17, client to replace).
- **Shop mega menu:** the primary menu's Shop item is now the catalog link, with both products and "Compare the cloths" (anchor `#compare`) as children. The header menu uses Horizon's `featured_products` style with 1:1 images, so the dropdown shows both product cards.
- **Known limit:** the mega menu's product cards follow the catalog's default order, so The 8 shows first. A manual "Shop" collection with the flagship first would fix that, but it has to be published to the Online Store (Jeet's call).
- **Approver:** Jeet.

## Changes 2026-10-06 (internal QA and Dev Ready)
- The comparison table now uses the shared `comparison-column` snippet, so it matches the homepage table (QA 75). Points come from `custom.comparison_points`, or are built from the row values until that metafield exists.
- Recognition seals under each product (QA 73), Medium full-width buttons (QA 74), ticks from the `--icon-tick` token (QA 72).
