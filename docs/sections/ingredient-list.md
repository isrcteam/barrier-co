# ingredient-list

## Ticket
From docs/architecture.md (ingredient-list, 965:2290 / mobile 965:3712):
- "Key ingredients" heading on the left; rows on the right with an ingredient image, name and ticked benefits, separated by Fossil hairlines.
- Reads `product.metafields.custom.ingredients`, or a section `metaobject_list` off the PDP.
- Ingredient images are transparent PNGs with the shadow baked in (T-23).
- Merchant configuration: heading, source toggle, list, background colour, padding.

## Plan
- `sections/ingredient-list.liquid`. "Use product data" checkbox reads `product.metafields.custom.ingredients` when `product` exists; otherwise, or when empty, the `ingredients` metaobject_list setting.
- Fields: `name`, `image`, `benefits` (list). Ticks are Horizon `icon-checkmark.svg` in `--color-accent-bar` (Tan).
- Hairline colour: `divider_color` setting (set Fossil in the template), falling back to Tan mixed at `--opacity-brand-pressed`, which renders close to Fossil on Sandstone.
- In the theme editor with no data, three placeholder rows with the Figma copy are shown (storefront strings in `docs/locale-fragments/ingredient-list.storefront.json`); on the live store the section hides when empty.

## Reasoning
- **What:** a data-driven ingredient list.
- **Why:** ingredients repeat across products, so they live in metaobjects and are entered once.
- **Alternatives rejected:** section blocks per ingredient (duplicate entry per product); CSS shadows on images (T-23 bakes them in).
- **Impact:** no JS. The section renders nothing on the storefront when no source has entries.
- **Approver:** Jeet (delegated).

### 2026-10-02: Fixed image box
- **What:** Images sit in a 112 × 94 box (273 × 229 desktop) with object-fit contain (P14).
- **Why:** The ingredient PNGs have uneven canvases, so rows were 270 to 470 high.
- **Alternatives rejected:** Re-exporting the PNGs (needs the designer; the box keeps any future upload in line).
- **Impact:** None.
- **Approver:** Jeet (delegated)

## QA checklist
- [ ] PDP with ingredients in the metafield shows them in order; with the checkbox off it shows the section list.
- [ ] Off the PDP the section list is used.
- [ ] Desktop: heading column about 432 wide, 160 gap, image column 272, name 32 uppercase, 40 between rows.
- [ ] Mobile: heading 32, image 112 wide above the name, name 18, 24 between rows.
- [ ] Hairline under every row but the last, in Fossil (with divider color set).
- [ ] Ticks are Tan and align with each benefit line.
- [ ] Empty data: placeholders in the editor only; nothing on the live page.

## Merchant guide
- Content > Metaobjects > Ingredient: add name, image (transparent PNG) and benefits.
- On each product, fill the **Ingredients** metafield. The PDP section shows them automatically.
- To show ingredients elsewhere, untick "Use product data" (or use it off the PDP) and pick entries in **Ingredients**.
