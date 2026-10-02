# Figma diff: product page (`/products/the-30-the-everyday`)

Figma: PDP 965:2002 (1440) and PDP MOBILE 965:3441 (390); sticky add to cart 965:1973 (desktop) and 965:4237 (mobile). Build measured on theme 167298138367 with `getBoundingClientRect` and text ranges, relative to each section's top-left, on 2026-10-02. Values are px. "OK" means within 2px after the fix. Also checked at 1000 and 1920 for regressions.

The purchase options (Subscription 978:3704) only render with Recharge selling plans, which don't exist yet. They were not measured, and neither were the parts that depend on them: the price inside the add-to-cart label, the savings badge and the plan select in the sticky bar.

## Announcement bar and header (stock, `brand-overrides`; same on every page)
| Element | Figma | Build (before) | Fix |
| --- | --- | --- | --- |
| Announcement bar height | 34 | 16 | Slider min height `30+4`. OK |
| Header height, desktop | 58 (20 / 18 text / 20) | 66 | Row padding `14/2` = 7 around the 44 tap targets. OK |
| Header height, mobile | 64 (24 / 16 / 24) | 60 | Row min height `60+4`. OK |
| Nav item gap | 48 (SHOP to ABOUT spans 243) | 22 (spans 192) | Link title padding 24 each side. 48, span 244. OK |
| Nav colour | all Clay | inactive items at 80% | All at full foreground. Hover underlines the title instead of dimming the others |
| Action group gap (SEARCH, ACCOUNT, CART) | 30 | 20 | `header-actions` gap 30. OK |
| Logo width | 197 desktop, 170 mobile | 182, 159 | **Setting:** logo width (config). Not changed |
| Breadcrumb section, mobile | none | 16-high empty band (block hidden, padding kept) | Section hidden below 990 when the trail is desktop-only. OK |
| Breadcrumb text y / gallery y, desktop | 92 / 130 | 100 / 126 | **Template:** `breadcrumb_bar` padding 0 top, 20 bottom (now 8 / 8) |

## Product information (965:2031 gallery, 965:2045 buy box), stock plus custom blocks
| Element | Figma | Build (before) | Fix |
| --- | --- | --- | --- |
| Buy box width | 482 at x928 | 446 at x964 | Sidebar `buy box + gap/2`; columns `2fr minmax(sidebar, 1fr)` from 1200. OK, and 1920 keeps the 2:1 split |
| Main image | 780 square at x120 | 812 at x124 | Same fix, plus thumbnail rail padding `0 10 0 0`. OK |
| Thumbnails | x30, first at y24 | x33, y27 | Rail padding removed; the selected outline is drawn inset so it isn't clipped. OK |
| Stars + label | stars 99.6, label at x108.6 | 90, label at x98 | `product-rating`: 6 star spacing, trailing space trimmed, 4 gap. Label at 108. OK |
| Rating to title / title to description / description to highlights | 16 / 20 / 20 desktop, 16 / 10 / 10 mobile | 24 / 24 / 24 | Margins against the group gap. OK both widths |
| Description size, mobile | 16/1.3 | 14/1.3 | `14+2` / body line on both widths. OK |
| Clinician mark | laurels 10×20, title on 2 lines, divider at 121, text at x139 | laurels 13×24, title on 1 line, text at x170 | Laurels 20 high, 10 gap, 14 before the divider, title `min-content`. Text at x138. OK |
| Guarantee line | 10 below the button, centred across 482 | 24 below, left-aligned (block is fit-width) | 10 gap. OK. **Template:** guarantee text block `width: 100%` to centre it |
| Recognition seal | 33×45, text at x58 | 30×41, x55 | Logo `30+2` wide (32×43), text at x57. OK |
| Promo card | text x94, button 128 at x342, GT America Medium 12 | text x98, button 122 at x348, Akzidenz | Image gap 12, button 16 from the text, min width `112+16`. Small buttons use GT America Medium 12 (label) everywhere. OK |
| Promo card, mobile | padding 10, button 10 below the image | 12 / 12 | Padding and row gap 10 below 990. OK |
| Accordion answer | 14/1.3, 12 below the title (T7) | 16/1.3, 20 below | Body-small size; open summary has 12 bottom padding. OK |
| Separate price block | not in Figma (price sits in the button label) | `$70.00` above the button | Kept until Recharge plans exist (see above) |

## Sticky add to cart (965:1973, 965:4237), stock, `brand-overrides`
| Element | Figma | Build (before) | Fix |
| --- | --- | --- | --- |
| Price position | under the title, 8 gap | right of the title | Grid: image, title over price, button. OK |
| Button height | 45 → Medium 44 (K2) | 55 | Medium 44. OK |
| Mobile | image + title/price row, button full width 12 below | wrapped flex | Same grid, button spans both columns. OK |
| Bar height | 143 (image frame 83) | 140 (image 80) | Accepted: the image itself is 80 in Figma; the 83 frame is an artefact |
| Rating row above the title | stars, 4.7, reviews | absent | **Stock markup:** needs a rating line in `sections/product-information.liquid` (not my file) |
| Button width | 267 | 177 | Label carries no price without Recharge |

## Benefit hotspots (965:2198), `benefit-hotspots`
| Element | Figma | Build (before) | Fix |
| --- | --- | --- | --- |
| Panel / photo widths | 817 / 563 | 828 / 552 | Columns `817fr 563fr`. OK |
| Label y | centred on the marker (label 26) | offset by 12 (label 24) | Offset `(24+2)/2`. Labels at 111 / 235 / 483 vs 109 / 233 / 485. OK |
| Marker x, line length | 381/126, 317/290, 320/265 | 381/123, 316/286, 316/261 | Residual 3–8 on PROTECT: the template positions are whole percentages (`x 39`, `line 32`), the nearest values available |
| Message card | 224 high with 3 dots | 202, no dots | Template has one message block, so no dots render |
| Mobile | callouts drawn over the image | callouts listed under the image | Architecture decision; kept. Story card matches (24 / 88 offsets) |

## Ingredients (965:2290), `ingredient-list`
The section collapses on this product (no published ingredient entries, K14), so it was checked against the CSS.
| Element | Figma | Build (before) | Fix |
| --- | --- | --- | --- |
| Tick and text | tick 10.5×7, text at x20.5 | tick 16, text at x26 | Tick 12 (as the buy-box highlights), text at x22. OK |
| Name line height, desktop | 32/1.1 | 32/1 | 1.1. OK |
| Columns, image, gaps | 431 / 160 / 273 / 24 / 40 | same | None |

## Video banner (965:2346), `video-banner`
1440: 776 vs 778. 390: 390 vs 390. No change.

## FAQ (978:4245), `faq-panel`
| Element | Figma | Build (before) | Fix |
| --- | --- | --- | --- |
| Side bars | x183 and x1226 (frame hugs the panel, 183 inside) | x30 and x1380 (frame full width, 144 inside) | Fixed panel width so the frame can hug it; inner padding `min(184, space left)`. Bars at 183. OK, and at 1000 |
| Question y | 20 into the item | 31 | Summary padding removed. OK |
| Icon / answer indent | 14 / 24 | 16 / 26 | 14 / 24. OK |
| Mobile stage padding | 50 | 60 | Kept: L7 snaps 50 to the scale |
| Items and button | 4 questions + READ MORE FAQ | 1 question, no button | Content |

## Footer (966:754, mobile 966:1024), stock, `brand-overrides`
| Element | Figma | Build (before) | Fix |
| --- | --- | --- | --- |
| Wordmark bars | 47 wide, 270 high, 47 above and below the letters, 94 to the letters | 30 wide, 171 high (letter height) | Bar `40+6`, extends by its own width, offset `46+80+14`. Letters stay at x170. OK |
| Mobile bars | 12.6 wide, 12.6 above and below | 12, flush | Same rule. OK |
| Menu headings | level with JOIN THE COMMUNITY, links 20 below | 11 lower, 24 below | Summary padding 0, 20 gap. OK |
| Email row | 30 row + line at 36 | 45 | Input 36 high, 6 under the text. OK |
| Consent line | 14 below the line | 32 | OK (16) |
| Mobile menus | 2 columns (Company, Support), Community below; 16px | 1 column, 14px | 2 columns, 16 gap, 40 after the newsletter, links `14+2`. OK |
| Mobile bars gap | 30 after the menus | 56 | OK |
| Mobile bottom row | left / right aligned, 31 above, 24 below | centred, stacked, 39 / 20 | Row, space-between, 30 / 24. OK |
| Footer height | 658 / 762 | 476 (letters only) / 1017 | 664 / 733. Mobile is shorter because the bottom row has 2 links, not 4 |
| JOIN THE COMMUNITY line height | 18/1 | 18/1.4 | **Template:** `footer-group.json` join text `line_height: tight` |
| Bottom links | 4 items | copyright + policy popover | Content/settings |
| Email placeholder | 14 | 16 | Kept at 16 to avoid iOS zoom |

## Shared sections (owned by the home-page pass; not edited)
| Section | Figma 1440 / 390 | Build 1440 / 390 |
| --- | --- | --- |
| Real use (`video-testimonials`) | 488 / 508 incl. 30 padding | 498 / 459. Desktop: 44 arrow frame vs 34 (accepted on home) |
| Stats (`clinical-results`) | 672 / 678 | 636 / 716 |
| Before / after | 638 / 833 incl. 30 padding | 605 / 769 |
| Reviews (stock + app) | 1000 / 1352 | 438 / 533 (app widget content) |
| Instagram (`social-gallery`) | 454 / 470 | 454 / 450 |
| Logos (`logo-list`) | 94 / 106 | 80 / 80 |

## Corrections where the Figma disagrees with itself
| # | In Figma | In code |
| --- | --- | --- |
| P1 | Buy-box gaps: 16 / 20 / 20 under the rating on desktop, 16 / 10 / 10 on mobile, 24 between every other block | Same values, as margins against the block gap |
| P2 | Header nav sits 337 after the logo, so it is off-centre | Nav centred on the page; item gap 48 as drawn |
| P3 | Sticky bar inset 24 from the page edge | On the 30 grid like everything else (L1) |
| P4 | Hotspot labels 26 high, the positions use the dot centre | Labels centred on the marker line |
| P5 | Footer wordmark bars are 47 wide on desktop but the hero bars are 30 | Footer bars keep the Figma ratio (bar = 0.27 × letter height, 46 desktop, 12 mobile) and extend past the letters by their width |
| P6 | PDP stars 15 with 6 gap; review-card stars 16 with 8 gap (see home H7) | Two sizes kept: buy-box rating at 6 spacing, cards at 8 |
| P7 | Small button label is GT America Medium 12 in "Components / Button" but Akzidenz in code | GT America Medium 12 (label) for every Small button |
| P8 | Sticky CTA is 45 high, the main CTA 55 | Sticky uses Medium 44, main stays Large 55 |
| P9 | PDP description is 16 on both widths; body copy elsewhere is 14 on mobile | Description 16 on both widths |
| P10 | FAQ panel icons are 14, Horizon's are 16 | 14 in both accordions |

## Re-QA 2026-10-02: buy box (965:2045) and every multi-entry component

The first pass measured spacing with one entry per list, so it missed every carousel and the subscription cards. This pass counted entries against Figma on home and PDP at 390, 1440 and 1920.

| Component | Figma | Build (before) | Cause | Fix |
| --- | --- | --- | --- | --- |
| Subscription cards | 2 plan cards, recommended tag, savings tag, per day, timeline, perks, "Try once" | Not rendered | No selling plans on the store (Recharge not set up) | **Preview plans** setting draws the cards from `custom.subscription_plans` with a new `discount_percentage` field until Recharge creates the plans; ignored once plans exist. Card markup moved to `purchase-option-card` so real and preview cards are one component. Block measures 376, Figma 376 |
| Add to cart label / price | "ADD TO CART - price", no separate price | Separate $70.00 line, plain button | Price block in the template; label only set when plans existed | Price block removed; the purchase block always sets the button label (The 8: "Add to cart - $16.99") |
| Recognition slider | 2 entries, dots left under the card | 1 entry, no dots | Only one recognition linked | National Psoriasis Foundation entry (seal from the client's files), linked to both products; dots left-aligned |
| Clinical-trial quotes | 3 entries, dots below the card | 1 entry; linen painted behind the dots | One testimonial linked; block background on the wrapper | 2 placeholder clinician quotes (D-7); colour on the card only; dots left-aligned |
| Benefit message panel | 3 slides with dots | 1 message | One message block in the template | 2 more messages from the Cleanse/Hydrate callout copy |
| Key ingredients | 3 rows | Section missing (height 0) | The 3 ingredient entries were Draft | Activated (still placeholder copy, D-7); image box fixed (P14) |
| PDP FAQ | 4 questions | 1 | 3 FAQ entries were Draft | Activated |
| Before/after | 3 slides, arrows (desktop), dots (mobile) | 1 slide, no controls | One comparison | 2 placeholder comparisons (D-12) on both products and on home |
| Accordion Claims / Size & pack | Content | Empty rows on both products | Metafields empty | Filled from claims already in the Figma copy (D-7) |
| The 8 | Same buy box as The 30 | No description, no recognitions, quotes, FAQ, ingredients, results, UGC, before/after | Lists only filled on The 30 | Shared entries linked; description and how-to-use filled (D-7) |
| Before/after card | See P11 | One size | | Card size setting |
| Highlight ticks | Tan | Tan | | Unchanged (checked against the asset) |

Not fixable in code: Akzidenz **Medium** (plan names, accordion rows, quote names, recognition titles, promo heading) renders as Regular because no Medium file exists in the client's files or the live theme (T-3).

Checked with no Liquid errors on `/`, both PDPs and `/collections/all` at 390, 1440 and 1920.

## Property-level audit, 2026-10-02 (home, PDP, footer)

Five auditors compared computed styles on the preview with Figma's exact values at 1440 and 390 (157 findings). Two fix rounds, each re-measured by the same auditors. Tables: scratchpad `qa/audit/*.md` and `*-verify.md`; decisions in design-corrections P12–P23.

Confirmed fixed in round 2 (re-measured): header brackets Sandstone, mobile logo centred (110–280), Search–Account 30, press quotes Sandstone 16/1.3 with 50 between items, routine band 803 (Figma 800), featured split 790/34/556 with a 700 image, breadcrumb "Home | Products | …", radio dot, timeline on one line, accordion item 145 (144), before/after photos 397.5 × 450 and a 38 arrow row, Judge.me stars 15 Accent, heading-to-rating 16, review button without border, reviewer name Medium, sticky select 270, lifestyle mobile opens on the product card.

Left on purpose or waiting on inputs:
- Akzidenz Medium renders Regular (T-3, font file).
- Play buttons on hero, intro and video banner appear once videos exist (D-6).
- Reviews sidebar, histogram, search, Q&A tabs, summary stars and the date beside the stars are Judge.me layout settings (D-19).
- FAQ page (D-18). Stats desktop background is 736 px wide in Figma (D-12).
- The " - " in the add to cart label is one string, so it can't take Medium weight while the label is ExtraBold.
- Announcement "1/5" counter: Figma shows a counter for five messages; the store has two and the counter isn't built.
- Header logo: the supplied logo file is 193 × 17 at the set height; Figma's is 197 × 16.2 (different file aspect).
- Sticky bar shadow: Figma's drop shadow points down off-screen from a bottom bar; the upward shadow stays.
- Media badge: Sepia text as on the home frame (the PDP frame uses Clay); hidden on mobile as in both mobile frames.
