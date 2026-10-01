# purchase-options

## Ticket
From docs/architecture.md (purchase-options). Figma: Subscription component 978:3703 (WEB 978:3702, MOB 978:3701).
- Radio cards per selling plan with a "Recommended" tag, description, price, "Save $X vs try once", per-day price and the plan's delivery timeline and perks; a "Try once for $X" option selects one-time purchase.
- Native `selling_plan_groups`; radios named `selling_plan` tied to the product form with `form`.
- On change, the add-to-cart label price updates.
- Savings from `selling_plan_allocation.compare_at_price` minus `price`; per-day price = plan price / days (setting per plan position, defaults 90 and 30).
- No selling plans: renders nothing and the product falls back to one-time purchase.
- States: selected, unselected, focus-visible, disabled when the variant is unavailable.

## Plan
- Theme block `blocks/purchase-options.liquid` plus `assets/purchase-options.js` (Component, about 60 lines).
- Form wiring: `buy-buttons` renders `{% form 'product' %}` with id `BuyButtons-ProductForm-<section.id>`; every radio carries `form="BuyButtons-ProductForm-{{ section.id }}"`. Horizon's `product-form-component` posts `new FormData(form)`, which includes form-associated controls outside the form, so `selling_plan` reaches `/cart/add` with no hidden input. The one-time radio has an empty value.
- Default selection: `product.selected_selling_plan`, else the recommended position, else the first plan; one-time when there are no allocations.
- Plan copy from the selling plan: name = card title; description paragraphs (blank line between) = summary / timeline (one line per step) / perks. Timeline and perks show only on the selected card.
- Add-to-cart price: Horizon's add-to-cart label has no price and Horizon has no selling-plan event, so the block sets `--purchase-options-button-label` on the product form (initially from Liquid in a `{% style %}`, then from JS on change) and a rule in this block's stylesheet shows it as `::after` on `.add-to-cart-button` inside that form. It survives Horizon's morph of the button on variant change, and is hidden while disabled or showing the added animation.
- Variant change: Horizon only updates components that listen to `shopify:product:select` and copy from the fetched HTML (as `product-price` does). The module does the same for this block and restores the shopper's choice by value.

## Reasoning
- **What:** native radios plus a small module.
- **Why JS:** the label price and re-render on variant change have no Horizon hook; everything else (submission, focus, keyboard) is native.
- **Alternatives rejected:** a hidden `selling_plan` input synced by JS (the radios already submit); editing `add-to-cart-button.liquid` or `product-form.js` (stock files, blocks Horizon updates); dispatching Horizon's product-select event (it triggers a section fetch and ignores selling plans).
- **Impact:** queued adds (clicked while a variant fetch is in flight) go through Horizon's JSON batch path and drop `selling_plan`; rare with single-variant products. The sticky add-to-cart bar shows the product price, not the plan price. Fossil borders and timeline ticks read `var(--color-input-border)` (Horizon fills it from `palette_input_border`, Fossil); Linen dividers = Clay at `--opacity-brand-shadow`.
- **Approver:** Jeet (delegated).

## QA checklist
- [ ] Product with two plans: both cards; recommended tag on the chosen position; it's selected by default with a white fill and Clay border.
- [ ] Selecting a card moves the border and fill, shows its timeline and perks, and the add-to-cart label reads "ADD TO CART - <plan price>".
- [ ] "Try once for $X" selects one-time; label shows the variant price; cart line has no selling plan.
- [ ] Add to cart with a plan: the cart line shows the plan name.
- [ ] Savings badge only when the plan has a discount; amount = compare at minus price.
- [ ] Per-day price = plan price / days setting; hidden when "Show price per day" is off.
- [ ] Unavailable variant: radios disabled, card faded, no price on the sold-out button.
- [ ] Variant change: prices refresh, choice kept.
- [ ] Product without selling plans: nothing renders, add to cart works as one-time.
- [ ] Product that requires a selling plan: no one-time option.
- [ ] Keyboard: Tab into the group, arrows move between options, focus ring visible.

## Merchant guide
1. Set up subscriptions in your subscription app; each plan's name is the card title.
2. In each plan's description, write the summary, then a blank line, then one delivery step per line, then a blank line, then the perks line.
3. In the theme editor, add "Purchase options" above "Buy buttons". Set the heading, which plan is recommended and its label, the savings and per-day labels, the days each plan covers, the add to cart price label and the one-time label.


### Reasoning, 2026-10-01: card copy from metafields (Recharge)
- **What:** plan card copy (title, summary, delivery timeline, perks, recommended tag, per-day divisor) now reads from `product.metafields.custom.subscription_plans`, a list of `subscription_plan` metaobjects.
- **Why:** the client uses Recharge. Recharge supplies the selling plans and prices but not this copy, and Jeet asked for it to come from metafields.
- **Matching:** each entry matches a plan by "Selling plan name" (case-insensitive). With that field empty, it matches by position. An entry that names a different plan never matches by position.
- **Alternatives rejected:**
  - Parsing the selling plan description: Recharge controls that text, and it isn't editable per card.
  - Block settings: they'd be per template, not per product.
- **Impact:** with no entries, the old description parsing still applies.
- **Approver:** Jeet (direct instruction).
