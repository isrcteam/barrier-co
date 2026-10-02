# Barrier Co theme plan

Version: v1 (draft)

## Approval log
One row per approval. The scripts read this table: the first cell is the exact phrase, and a row without a date and an approver does not count. Only Jeet approves.

| Approval | Date | Approved by | Notes |
| --- | --- | --- | --- |
| Approved: design analysis | | | |
| Approved: tokens | | | |
| Approved: architecture | | | |
| Approved: data model | | | |
| Approved: seo | | | |
| Approved: prune | | | |
| Approved: asset pack <purpose> v<n> | | | |
| Approved: client design sign-off | | | Date the client signed off the design; changes after this are tickets |
| Approved: plan v1 | | | Phase 4 gate |
| Approved: release 1 | | | |

### Delegated authority
2026-10-01, Jeet: "you can plan everything and start developing. Create meta fields and meta objects as required. You can only push an unpublished theme. You cannot make it live. You cannot publish anything."

What this covers:
- Planning and building without stopping at each phase gate. Assumptions are logged under Open questions so they can be reviewed later.
- Creating metafield and metaobject definitions and entries on the store, each with a backup and a dry run first.

What stays forbidden:
- Publishing a theme, or pushing to the live theme.
- Publishing products, collections or pages to any sales channel.

`Approved: plan v1` and `Approved: release 1` are still Jeet's to write.

Not applicable to a new build (no existing store): export run, existing-inventory, migrate, seo push.

## Inputs
| Input | Status | Notes |
| --- | --- | --- |
| Project type | New build | Decided at kickoff 2026-10-01. No existing Shopify store, nothing to bring over |
| Base | Horizon 4.2.0, commit `f9aef27` | Merchant-facing build, default base (core rule 5). `upstream` = Shopify/horizon. Pruned after the build |
| Figma file and MCP access | Confirmed 2026-10-01 | [Design file](https://www.figma.com/design/oZ00gYRP11BAdFQYwo4fxj/BARRIER-CO-%7C%7C-DEV-READY--JEET--?node-id=965-1236&m=dev), jeet@isrcit.com, Full seat. No separate brand library. See tokens.md |
| Store | the-barrier-co.myshopify.com, alias `store`, role production | Custom app "Store Data Sync" installed 2026-10-01 with permanent token. Unpublished theme pushes only; no publishing (Delegated authority). No separate dev store |
| Fonts (supplied / missing) | Waiting | Files and licences, or looked up from the Figma text styles |
| Content sources | Waiting | Who writes the content; reviews or other content to bring in |
| Apps and integrations | Waiting | Apps the client already pays for; form, CRM or email platform |
| Brand assets | Waiting | Logo SVG, square mark for the favicon, share image |
| Launch date | Waiting | |
| Markets and languages | Waiting | |
| Existing store data | Export run 2026-10-01 | Read-only export to check for existing products and definitions before creating any |
| Tools | 1.6.2 | Installed by `setup_tools.sh` |

### Steps that apply (new build)
Figma links, fonts, launch app plan (new apps only), `/isrc:tokens` from Figma, Horizon base, `/isrc:import` for new content, `/isrc:assets`, `/isrc:seo` for new content, prune after build, full plan and approval gate. Not applicable: `/isrc:pull`, theme and data analysis, `/isrc:migrate`, visual regression against live.

## Design analysis
Frame audits are summarised in tokens.md (alignment report) and architecture.md (one entry per component, with Figma nodes). Reuse map:
- **Shared by home and PDP:** clinical-results, video-testimonials, before-after, FAQ accordion, social gallery, logo list, footer.
- **Variants of one component:** image-carousel (Routine and Lifestyle); hero-banner (Hero and Inset banner); product-spotlight (card, row, glass).
- **One-offs:** benefit-hotspots, ingredient-list.

Heading hierarchy:
- **Home:** H1 is the hero "Body care. Reformatted."; every other section heading is H2; card labels and product titles are H3.
- **PDP:** H1 is the product title; section headings are H2; ingredient names, reviewer names and FAQ questions are H3.

Missing states (PDP audit):
- Variant selector, sold out, sale price, quantity, gallery zoom, loading and added-to-cart. Horizon's stock behaviour is used, styled by the tokens.
- The open mobile menu and the empty reviews state also use Horizon's stock behaviour.

## Tokens
See [tokens.md](tokens.md). The source is the Figma styles and number collections, normalised into `tokens.json` and generated into `snippets/design-tokens.liquid`. The desktop switch is 990px, the same as Horizon.

## Architecture
See [architecture.md](architecture.md).
- **Custom:** 13 preset sections, 8 theme blocks, 5 snippets.
- **Stock Horizon, styled:** header, announcements, marquee, featured-product, product-information (with its sticky add to cart), footer.
- **One-offs:** benefit-hotspots and ingredient-list (PDP only).

## Template map
See the template map in [architecture.md](architecture.md#template-map).

## Data model
See [data-model.md](data-model.md): 13 product metafields and 7 metaobject types, created 2026-10-01. Seed content comes from `docs/data/seed.json` via `scripts/seed_content.py`, replacing a Matrixify import for this new build.

## SEO
Link to seo.md. Redirect count, canonical and noindex rules, JSON-LD types. New build: no crawl baseline; redirects only if a previous non-Shopify domain exists.

## Commitments
**Performance:**
- Lighthouse mobile 90+ on home and PDP, with LCP under 2.5s.
- theme.css under 14 KB gzip.
- Brand fonts subset to 16–20 KB each, with only 2 preloaded.
- No new JS libraries; videos load only on click.

**Accessibility:** WCAG 2.2 AA. Colour contrast failures go to the designer as questions, and colours aren't changed (core rule 11).

**Devices:** 1920, 1440, 1280, iPad portrait and landscape, iPhone. **Browsers:** the latest two versions of Chrome, Safari, Firefox and Edge, plus iOS Safari 16+.

## Build order
1. Foundation: tokens, fonts, global settings, shared snippets ✅
2. PDP blocks
3. Sections, built in parallel
4. Brand overrides for stock sections
5. Locale merge
6. Template assembly: home, then product
7. QA
8. Prune

## Open questions and assumptions
| # | Question | Who answers | Answer or assumption | Status |
| --- | --- | --- | --- | --- |
| T-1 | Templates (All): No collection, cart, search, account, 404, blog, article, page or FAQ page frames. Value Only home and PDP designed | Designer | Style Horizon's stock templates with the tokens; ask for frames where a custom layout is wanted | Assumed |
| T-2 | Fonts (All): Web licences not confirmed. Value Akzidenz-Grotesk Next, GT America (commercial) | Client | Use the files from the live theme | Open |
| T-3 | H3–H5, Heading Small, stats (Headings): File not supplied. Value Akzidenz Medium 500 | Client | Regular until Medium is sent | Assumed |
| T-4 | Palette names (All): A role name used as a colour name; a duplicate style. Value "BG", "neutral/BG" (duplicate), "Ingenious Black" | Designer | Rename in code to linen and ink; one entry | Assumed |
| T-5 | Glass card fill (Stats, PDP benefits): Raw colour with two opacities. Value #E7DACE at 28% and 30% | Designer | New palette colour `oat` with one opacity, 0.28 | Assumed |
| T-6 | Glass card border (Stats): The style's name says 40 but its value is 60. Value White at 60% via `Alpha/Light/40` | Designer | Use 60% | Assumed |
| T-7 | Wordmark (Footer): One step off Sepia. Value #695942 | Designer | Merge into sepia | Assumed |
| T-8 | Caption text (Carousels): Other body copy is Clay. Value Ink #181717 | Designer | Keep ink as the fixed colour "Carousel caption" | Open |
| T-9 | Product price (Home, PDP): Same element in three colours. Value Clay, Sandstone, Sepia | Designer | Follows its surface: Sandstone on dark glass, Sepia on light cards | Assumed |
| T-10 | Last review divider; sticky title (PDP): Every other instance uses Fossil or Clay. Value Black #000000 | Designer | Fossil and Clay | Assumed |
| T-11 | Spacing (All): Nothing bound; 12 is the most used gap but isn't on the scale. Value ~30 gap and ~25 padding values, including fractional ones (8.132, 9.072, 24.192, 2.184) | Designer | Scale = Figma's plus 2, 6, 12, 80; snap 5→4, 7/9→8, 15/17→16, 19→20, 27/28→30, 50/56→60, 84/85→86; fractional values rounded | Assumed |
| T-12 | Breakpoint (All): No tablet frames. Value Frames at 390 and 1440 only | Jeet | Switch to desktop at 990, the same as Horizon | Assumed |
| T-13 | Gutter (Mobile): Inconsistent. Value 10, with 16 and 17 in places; top bar 37 | Designer | 10 everywhere; header 16 to match the nav component | Assumed |
| T-14 | Benefits row, Stats, banner (Desktop): Off the page grid. Value Fixed 1150 at x145; insets of x30 + 30 | Designer | Benefits row max-width 1150 centred; Stats keeps its own padding | Assumed |
| T-15 | Text without a style (Several): 98 text segments have no style. Value Top bar Akzidenz Regular 12; nav GT Medium 14; stats 96/70 and 64/53; % at 44; mini card 24 | Designer | New type roles: announcement, nav, stat, stat_unit | Assumed |
| T-16 | Mobile vs desktop nav (Header): Different families. Value Mobile Akzidenz ExtraBold 14; desktop GT Medium 14 | Designer | Keep both as designed | Open |
| T-17 | Mixed-style paragraphs (Home): One text node, two styles. Value First line Akzidenz Medium or GT Medium inside Body | Designer | Rich-text bold maps to medium weight | Assumed |
| T-18 | States (Buttons): No colour change on hover. Value Opacity 86/72/35%; focus is a Clay glow | Jeet | Implement as designed; keyboard focus also keeps a visible outline for WCAG | Assumed |
| T-19 | Sizes in use (Buttons): Instances resized off the set. Value 31 (Take the test), 43, 45, 47 | Designer | Small 40, Medium 44, Large 55; the mobile ATC uses Large | Assumed |
| T-20 | Two primary components (Buttons): Duplicate component; MAIN CTA has no text style or states. Value MAIN CTA (667) vs Button (676) | Designer | One button system; the price in the ATC label stays ExtraBold, separators Medium | Assumed |
| T-21 | Secondary background (Buttons): Not linked to a style. Value Raw #F9F7ED; "Our science" uses White | Designer | Secondary uses the background colour | Assumed |
| T-22 | Play icon (Components): Four sizes. Value 57, 40, 30.333, 20.333 | Designer | Two sizes | Assumed |
| T-23 | Ingredient image shadows (PDP): No effect style used. Value Three different raw shadows | Designer | Bake the shadow into the PNG asset; no CSS shadow | Assumed |
| T-24 | Blurs (Several): Effect styles 42/50/64 unused. Value 30, 27, 6, 60, 24, 12.77, 8.56 | Designer | Three blur tokens | Assumed |
| T-25 | Inactive opacity (Several): Inconsistent. Value Dots 34%, timeline ticks 30%, footer labels 80% | Designer | Two tokens | Assumed |
| T-26 | FAQ answer size and dividers (PDP, FAQ): Same component, different values. Value Body 14 vs 16; borders differ per item | Designer | Body 14 in the buy box, 16 in the FAQ section; one divider rule (bottom border on every item) | Assumed |
| T-27 | Reviewer name (PDP): Inconsistent. Value 20 vs 18 | Designer | 18 | Assumed |
| T-28 | Layout bugs (Mobile): Overflow. Value Fixed widths of 458, 453 and 382 in a 370 container; video cards 1px wide | n/a | Fluid widths | Fixed in build |
| T-29 | Copy (Content): Placeholder or typo. Value £ and $ mixed; "reformated"; "1Month"; "12,00 Reviews" | Client | The store currency is USD, so prices come from Shopify; typos fixed in schema defaults | Assumed |
| T-30 | Hero image overlay (PDP): Two options. Value OP1 seal chip vs OP2 "Save 25%" + NEA card | Jeet | Build OP2 (it matches the main PDP frame) with the badge from `custom.media_badge`; the seal chip stays an option | Open |
| D-1 | Products to build against | Jeet | Created by Claude, unpublished; Jeet publishes (2026-10-01) | Answered |
| D-2 | Subscription app for selling plans | Client | Recharge (Jeet, 2026-10-01). Prices from Recharge selling plans, card copy from custom.subscription_plans metaobjects. Recharge plan names still to be entered in each entry's Selling plan name | Answered |
| D-3 | Reviews and Q&A app | Client | Judge.me (installed) styled to the design | Assumed |
| D-4 | Instagram feed source | Client | Manual image tiles with links | Assumed |
| D-5 | "The 8" price and "Starts from" figures ($27.99/mo, $24.99/mo, $68.99) disagree across frames | Client | Prices come from Shopify and the selling plans; design figures treated as placeholders | Open |
| D-6 | UGC video files | Client | Not in Figma; sections render posters only until videos are uploaded | Open |
| D-7 | Copy marked Lorem ipsum (press quotes, Stats intro, Lifestyle caption) and repeated ingredient benefits | Client | Draft placeholders; final copy needed. Also placeholder: clinician quotes 2 and 3 (Dr. Amelia Hart, Dr. Samuel Reyes, invented names, must be replaced or removed before launch), the Claims and Size & pack details accordion copy on both products, The 8 description and how-to-use, and the National Psoriasis Foundation recognition copy (seal file is from the client store; confirm the product holds it) | Open |
| D-8 | "The 8" has no description in Figma | Client | Empty description | Open |
| D-9 | The before/after quote card shows "Marco Bellini" beside a woman's photo, and the quote reads like the How to use copy | Designer | Treated as placeholder | Open |
| D-10 | The 4th gallery item is a video in the design; the close-up image is only 480px (cropped from a composite) | Client | Stills used; full-resolution photography needed | Open |
| D-11 | The Claims, Size and pack details, and Full ingredient list accordions have headings but no copy | Client | Rows hide when empty | Open |
| D-12 | Full-resolution photography | Client / designer Also: before/after entries 2 and 3 (placeholder-result-2/3) reuse the day-0/day-14 photos to fill the 3-slide carousel; real result photos needed, or delete those entries before launch. | Figma only holds the photos at 1402–1672px wide (the stats background at 736px), so they soften at a 1920 wrapper on retina. Originals at 3840 wide are needed to replace them in place | Open |
| D-13 | Recharge selling plan names | Jeet / client | Once the plans exist in Recharge, put each plan's exact name in its subscription_plan entry's "Selling plan name"; until then cards match by order (3 month first, then 1 month) | Open |
| D-14 | Klaviyo list for the footer signup | Client | The footer uses Shopify customer signup, which Klaviyo syncs; confirm the list | Open |
| D-15 | Mobile search | Jeet | The design hides search on mobile, so it's hidden there for now | Open |
| D-17 | The 8 highlights are placeholder copy written to match The 30 ("Eight cloths in a travel-size pack." and so on) | Client | Replace with approved copy | Open |
| 1 | Figma design file, library file and prototype links | Client / designer | Design file received; no separate library | Answered |
| 2 | Brand font files and licences | Client | Files taken from the live theme; licence confirmation is T-2 | Partly answered |
| 3 | Launch date | Client | | Open |
| 4 | Markets and languages | Client | Export: United States market, USD, English only | Assumed |
| 5 | Apps the client already pays for; form, CRM or email platform | Client | Installed: Judge.me, Google & YouTube. Newsletter uses Shopify customer email signup until told otherwise | Partly answered |
| 6 | Who writes the content | Client | | Open |
| 7 | Staging and production store handles | Jeet | the-barrier-co.myshopify.com | Answered |
| 8 | Any previous website or domain (redirects) | Client | wearebarrier.com currently runs a landing page with no other URLs, so no redirects | Assumed |
