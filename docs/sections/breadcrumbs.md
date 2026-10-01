# breadcrumbs

## Ticket
From docs/architecture.md (breadcrumbs). Figma: 977:716 (desktop only; no mobile breadcrumb in the design).
- A "| Home | Collection | Title" trail in a `<nav aria-label>` with an `<ol>`; the current page uses `aria-current="page"`.
- `body_small` type role; the trail and bars in Tan, the current item in Clay.
- Desktop only by default, with a "Show on mobile" toggle.
- Data: `product`, `collection` or `page`, plus `product.collections.first` when available.

## Plan
- Theme block `blocks/breadcrumbs.liquid`, no JS. Works in any section that accepts theme blocks.
- Product from `closest.product`, falling back to the template `product`; collection from the `collection` context, else `product.collections.first` (setting "Show collection").
- Bars are `::before` pseudo-content with empty alt text (`content: '|' / ''`), so screen readers read only the names.
- Outputs BreadcrumbList JSON-LD (data-model JSON-LD mapping).
- Storefront strings: `accessibility.breadcrumbs`, `content.breadcrumbs_home` (new, in breadcrumbs.storefront.json).

## Reasoning
- **What:** a block, so it can sit in a stock `section` above product-information.
- **Why:** product-information renders its own section-level blocks below the product grid, so a breadcrumb there can't sit above the gallery as the design shows.
- **Alternatives rejected:** a section (the architecture lists it as a block, and a block reuses the stock `section` shell); placing it in the buy-box column (it would not span above the gallery).
- **Impact:** Tan comes from the fixed `--color-accent-bar` token (Tan), the only Tan variable in the token layer.
- **Approver:** Jeet (delegated).

## QA checklist
- [ ] Desktop 1440 on a product: "| Home | <collection> | <title>", trail Tan, title Clay, 14 regular.
- [ ] Mobile 390: hidden by default; shown when "Show on mobile" is on.
- [ ] Product with no collection: "| Home | <title>".
- [ ] Screen reader announces "Breadcrumb" navigation, the links and the current page, without the bars.
- [ ] Rich results test finds a valid BreadcrumbList.
- [ ] Link focus ring visible.

## Merchant guide
1. On the product template, add a "Section" above "Product information" and add the "Breadcrumbs" block inside it.
2. Turn "Show collection" off to drop the middle step; turn "Show on mobile" on to show the trail on phones.
