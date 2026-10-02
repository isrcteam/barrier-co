# Data model

Naming follows the /isrc:plan skill's references/naming.md. Built on export run `2026-10-01T141913Z`: the store has no products, no metaobjects and no `custom.*` definitions. The only existing definitions belong to the Google Shopping app (`mm-google-shopping.*`, `mm_google_shopping_extension.*`). They stay as they are, and nothing below clashes with them.

Content rule: content that belongs to one product sits in a product metafield. Content that repeats across the home page and the PDP sits in a metaobject, so it's entered once. Copy for a single placement stays in section or block settings.

## Metafields
| Owner | Namespace.key | Standard | Type | Definition name | Description | Renders in | Entered by | Migration |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Product | custom.highlights | none, no standard list of selling points | list.single_line_text_field | Highlights | Ticked selling points under the product description. | PDP buy box | Client | New |
| Product | custom.media_badge | none | single_line_text_field | Media badge | Short label on the main product image, for example "Flagship". | PDP gallery, featured product | Client | New |
| Product | custom.how_to_use | none, `descriptors.care_guide` is for care, not usage | rich_text_field | How to use | First accordion row on the product. | PDP and featured product accordion | Client | New |
| Product | custom.claims | none | rich_text_field | Claims | Accordion row. | PDP and featured product accordion | Client | New |
| Product | custom.size_and_pack_details | none | rich_text_field | Size and pack details | Accordion row. | PDP and featured product accordion | Client | New |
| Product | custom.full_ingredient_list | none | rich_text_field | Full ingredient list | Full INCI list in the accordion. | Featured product accordion, PDP accordion | Client | New |
| Product | custom.ingredients | none | list.metaobject_reference → ingredient | Ingredients | Key ingredients with image and benefits. | PDP key ingredients | Client | New |
| Product | custom.faq_items | none | list.metaobject_reference → faq_item | FAQ items | Questions for this product. | PDP "Most asked questions" | Client | New |
| Product | custom.testimonials | none | list.metaobject_reference → testimonial | Testimonials | Expert quotes ("Read the clinical trial"). | PDP buy box | Client | New |
| Product | custom.recognitions | none | list.metaobject_reference → recognition | Recognitions | Seals and endorsements. | PDP buy box "Recognition by" | Client | New |
| Product | custom.clinical_results | none | list.metaobject_reference → clinical_result | Clinical results | Study percentages. | "Clinically proven" stats on PDP | Client | New |
| Product | custom.ugc_videos | none | list.metaobject_reference → ugc_video | UGC videos | Customer videos. | PDP "Real use. Real routines." | Client | New |
| Product | custom.before_afters | none | list.metaobject_reference → before_after | Before and afters | Result comparisons. | PDP before/after | Client | New |
| Product | custom.subscription_plans | none, Recharge has no card copy | list.metaobject_reference → subscription_plan | Subscription plans | Copy for each Recharge plan card, matched by plan name or order. | PDP purchase options | Client | New (2026-10-01) |
| Product | descriptors.subtitle | Standard (descriptors.subtitle) | single_line_text_field | Subtitle | One-line purpose under the title | Collection showcase | Client | Enabled 2026-10-02 |
| Product | custom.cloth_count | none | number_integer | Cloth count | Cloths per pack; also used for the price per cloth | Collection comparison | Client | New 2026-10-02 |
| Product | custom.best_for | none | single_line_text_field | Best for | Who or when it suits | Collection comparison | Client | New 2026-10-02 |
| Product | reviews.rating, reviews.rating_count | Standard (reviews) | rating, number_integer | Product rating, Rating count | Written by Judge.me when "Sync to Shopify" is on. | PDP stars, product cards, JSON-LD | Judge.me | Enabled by the app, not created by us |

Subscriptions run on **Recharge** (Jeet, 2026-10-01), which creates native Shopify selling plans for prices, savings and checkout. The card copy does not come from Recharge: it comes from `custom.subscription_plans`. Each entry is matched to a Recharge plan by its "Selling plan name", or by order when that field is empty. If a product has no entries, the block falls back to the plan's description.

## Metaobjects
Every type: storefront access on, "Publishable" on so placeholder entries import as Draft and never render.

### faq_item (FAQ item)
Display name field: question
| Field key | Field type | Required | Renders in | Entered by |
| --- | --- | --- | --- | --- |
| question | single_line_text_field | yes | FAQ accordions | Client |
| answer | rich_text_field | yes | FAQ accordions | Client |

### testimonial (Testimonial)
Display name field: name
| Field key | Field type | Required | Renders in | Entered by |
| --- | --- | --- | --- | --- |
| name | single_line_text_field | yes | Quote cards, press marquee (publication name) | Client |
| quote | multi_line_text_field | yes | Quote cards, press marquee | Client |
| role | single_line_text_field | no | Expert card under the name | Client |
| avatar | file_reference (image) | no | Quote cards | Client |
| rating | rating (1 to 5) | no | Stars on quote cards | Client |

### recognition (Recognition)
Display name field: title
| Field key | Field type | Required | Renders in | Entered by |
| --- | --- | --- | --- | --- |
| title | single_line_text_field | yes | Recognition slider | Client |
| description | multi_line_text_field | yes | Recognition slider | Client |
| logo | file_reference (image) | yes | Recognition slider | Client |

### clinical_result (Clinical result)
Display name field: title
| Field key | Field type | Required | Renders in | Entered by |
| --- | --- | --- | --- | --- |
| title | single_line_text_field | yes | Stat caption, for example "Experienced increased skin hydration" | Client |
| value | number_integer | yes | Big number | Client |
| unit | single_line_text_field | no, defaults to "%" in the theme | Unit after the number | Client |

### ingredient (Ingredient)
Display name field: name
| Field key | Field type | Required | Renders in | Entered by |
| --- | --- | --- | --- | --- |
| name | single_line_text_field | yes | Key ingredients | Client |
| image | file_reference (image) | yes | Key ingredients | Client |
| benefits | list.single_line_text_field | no | Ticked list | Client |

### ugc_video (UGC video)
Display name field: title
| Field key | Field type | Required | Renders in | Entered by |
| --- | --- | --- | --- | --- |
| title | single_line_text_field | yes | Accessible name for the video | Client |
| video | file_reference (video) | yes | Video card | Client |
| poster | file_reference (image) | no | Video poster, before playing | Client |

### subscription_plan (Subscription plan)
Display name field: title
| Field key | Field type | Required | Renders in | Entered by |
| --- | --- | --- | --- | --- |
| title | single_line_text_field | yes | Card heading, for example "3 Month Subscription" (overrides the Recharge plan name) | Client |
| selling_plan_name | single_line_text_field | no | Not shown. The exact Recharge plan name this entry belongs to; empty means match by order | Client |
| summary | single_line_text_field | no | Line under the heading | Client |
| timeline | list.single_line_text_field | no | Delivery timeline bullets | Client |
| perks | list.single_line_text_field | no | Perks line, joined with " \| " | Client |
| is_recommended | boolean | no | "Recommended" tag and default selection | Client |
| days_per_delivery | number_integer | no | Divisor for the per-day price | Client |

### before_after (Before and after)
Display name field: title
| Field key | Field type | Required | Renders in | Entered by |
| --- | --- | --- | --- | --- |
| title | single_line_text_field | yes | Admin only | Client |
| before_image | file_reference (image) | yes | Comparison | Client |
| after_image | file_reference (image) | yes | Comparison | Client |
| before_label | single_line_text_field | no, theme default "Before" | Label on the image | Client |
| after_label | single_line_text_field | no, theme default "After" | Label on the image, for example "After · Day 14" | Client |
| testimonial | metaobject_reference → testimonial | no | Quote card under the images | Client |

## JSON-LD mapping
| Schema type | Property | Source (Liquid object or metafield) |
| --- | --- | --- |
| Product | name, description, image, sku, brand | `product` (Horizon's `structured-data` output kept) |
| Product | offers | `product.selected_or_first_available_variant`, price and availability |
| Product | aggregateRating | `product.metafields.reviews.rating`, `reviews.rating_count` (only when count > 0) |
| FAQPage | mainEntity | `product.metafields.custom.faq_items` on the PDP |
| Organization | name, logo, sameAs | `shop`, settings logo, footer social links |
| BreadcrumbList | itemListElement | Breadcrumb block on the PDP |

## Import file
Not built yet: there are no products in the store, and the Figma copy is placeholder in places ("Lorem ipsum"). Built once the products are created (open decision D-1).

## Open decisions
| # | Decision | Options | Who decides | Status |
| --- | --- | --- | --- | --- |
| D-1 | Create the two products ("The 30. The Everyday.", "The 8.") so the PDP can be built and QA'd | Create, leave unpublished; publish to Online Store; build without products | Jeet | 2026-10-01 Jeet: create them unpublished, Jeet publishes |
| D-2 | Subscription app for selling plans | Shopify Subscriptions; Recharge; Skio; other | Client | 2026-10-01 Jeet: Recharge. Card copy from custom.subscription_plans |
| D-3 | Reviews and Q&A | Judge.me (already installed) styled to the design; another app | Client | Assumed Judge.me |
| D-4 | Instagram feed source | App (for example Instafeed); manual image blocks | Client | Assumed manual image blocks with links |
