# product-rating

## Ticket
From docs/architecture.md (product-rating). Figma: buy box 965:2045 (top), mobile 965:3468.
- Stars plus a review label at the top of the buy box, linking to the reviews section.
- Renders `star-rating` from `product.metafields.reviews.rating` and `rating_count`; nothing when the count is 0.
- Link target is a setting (default `#reviews`). Label format is a setting (default "[count] reviews").

## Plan
- Theme block `blocks/product-rating.liquid`, no JS; `star-rating` at the medium (16) size, label in the `micro` role (10), uppercase, 8 gap.
- `[count]` and `[rating]` placeholders in the label; blank anchor renders a plain row instead of a link.

## Reasoning
- **What:** a thin wrapper around the shared `star-rating` snippet.
- **Why:** Horizon's `review` block draws its own SVG stars and can't take the brand star colour token or the label format.
- **Alternatives rejected:** styling the stock review block (its markup and type preset settings don't match).
- **Impact:** needs Judge.me "Sync to Shopify" on so the reviews metafields are filled. Figma shows "4.7 Reviews" (rating); the architecture default "[count] reviews" was kept and `[rating]` is available.
- **Approver:** Jeet (delegated).

## QA checklist
- [ ] Product with reviews: 5 amber stars filled to the rating, label "N REVIEWS".
- [ ] Product with 0 or no reviews: nothing renders.
- [ ] Click scrolls to the element with id `reviews`.
- [ ] Screen reader reads "Rating of this product is X out of 5" and the label.
- [ ] Focus ring visible on the link.

## Merchant guide
1. Add "Product rating" at the top of the product details.
2. Edit "Label" ([count] = number of reviews, [rating] = average). Set "Link to" to the anchor of the reviews section (default #reviews), or clear it for no link.
