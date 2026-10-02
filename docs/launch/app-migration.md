# App migration

The live theme ("Updated Barrier LP || 17.09") app embeds and blocks, and what the new theme does with each. Source: `config/settings_data.json` and `templates/index.json` of export run 2026-10-01T141913Z.

| App | On the live theme | New theme | Decision | Status |
| --- | --- | --- | --- | --- |
| Judge.me | App embed `judgeme_core`; `review_widget_homepage` block on index | Embed enabled. `review_widget` block in the PDP reviews section. Stars from `reviews.rating` in `product-rating` | Keep | Done on release/1 theme, 2026-10-01 |
| Recharge | App embed `recharge-theme` (customer portal styling) | Embed enabled, restyled to brand: Clay, square corners, Sandstone background. PDP plan picker is our `purchase-options` block on native selling plans; card copy from `custom.subscription_plans` | Keep | Done; selling plans to be created in Recharge. **Launch blocker:** the PDP shows preview plan cards (block setting Preview plans) until those plans exist; they never subscribe. Once Recharge creates the plans the preview is ignored; turn the setting off and set each `subscription_plan` `selling_plan_name` to match |
| Klaviyo | App embed `klaviyo-onsite-embed` | Embed enabled | Keep; footer signup uses Shopify customer signup, which Klaviyo syncs (confirm list mapping with client) | Done; list mapping open |
| Google & YouTube | Variant metafields only | Nothing to move | Keep | n/a |

Performance: each embed adds third-party script. Judge.me and Klaviyo are both loaded site-wide by their embeds, and the Lighthouse run in QA records their cost.
