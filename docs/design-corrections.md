# Design corrections

These are the places where the Figma file disagrees with itself, and how the code resolves each one. Each is resolved once, in the token layer or a shared rule, so that every section behaves the same. Jeet asked for this on 2026-10-02: fix Figma inconsistencies at code level, and record each one.

Node IDs refer to file oZ00gYRP11BAdFQYwo4fxj. "T-" numbers link to the alignment report in tokens.md.

## Layout and spacing
| # | In Figma | In code |
| --- | --- | --- |
| L1 | Only 1440 and 390 frames, with nothing about wider screens | The page wrapper is 1920: content up to 1860, a 30 gutter, centred beyond 1920. Every section, stock and custom, uses this one grid, and it's checked at 1400, 1440, 1920 and 2000 |
| L2 | Stock Horizon sections (header, featured product, footer) would use Horizon's 40px margin and 1920 content width | Horizon's `--page-margin` and `--page-content-width` now read our gutter and content-width tokens, so stock and custom sections share their edges |
| L3 | Desktop gutter is 30, but STATS and the banner are inset by a further 30, and the benefits row is a fixed 1150 at x145 (T-14) | Everything sits on the shared grid. Inset cards keep their inner padding, and the benefits row is centred at max 1150 |
| L4 | Mobile gutter is 10, except 16 and 17 in some frames and 37 in the top bar (T-13) | 10 everywhere |
| L5 | Vertical spacing is 80 between frames on desktop. Mobile sections pad themselves by 20, 30, 40 or 50, and some sections have no padding (T-11) | One rule: 80 desktop and 30 mobile between sections, applied once, globally. The press strip, ticker, logo strip and footer attach to their neighbours |
| L6 | Coloured bands (Routine, Instagram) pad 40 inside; other sections vary | Coloured surfaces: 40 desktop and 30 mobile inside. Plain sections: 0 (the gap does the work) |
| L7 | Spacing values off the scale: 5, 7, 9, 15, 17, 19, 27, 28, 50, 56, 84, 85, and fractional 8.132 and 9.072 (T-11) | Snapped to the scale 2–112 (merge log in tokens.md) |
| L8 | Fixed widths overflow mobile: 458, 453 and 382 in a 370 column, and video cards collapsed to 1px (T-28) | Fluid widths |
| L9 | Padding controls differ section to section | Every section has the same five padding settings: top, bottom, "Same at mobile", mobile top, mobile bottom, all 0–160 in steps of 2 |
| L10 | Body copy beside headings runs as wide as its column (about 860 at 1920) | Paragraphs are capped at 640 (about 65 characters) |
| L11 | Featured product buy box sits at the top of a tall gallery | Centred vertically against the gallery |
| L12 | Tablet has no frames; Horizon would put the PDP gallery and buy box side by side at 750 | Below 990 the gallery and buy box stack, and the image carousels show two cards |

## Typography
| # | In Figma | In code |
| --- | --- | --- |
| T1 | Section headings are 60/54 on desktop. Mobile uses 32/1.1 in most frames but 40/0.9 in others; the mobile Display 40 style is used only by the hero (T-15, PDP audit) | Hero: 60 and 40. Every other section heading: 60 and 32 |
| T2 | Horizon's own heading presets would use Horizon sizes, e.g. a 48px product title | Horizon's h1–h6 and paragraph presets read the brand type tokens, so stock blocks match custom ones |
| T3 | 98 text layers have no style: top bar, nav, stats numbers, the % sign, the mini-card title (T-15) | Given named roles: announcement, nav, stat, stat_unit, card_label |
| T4 | "lineHeight 100" in the Figma styles means AUTO | Rendered as `normal` |
| T5 | Paragraphs switch font or weight on their first line inside one text layer (T-17) | Bold in rich text maps to the medium weight |
| T6 | Reviewer name is 20 on the first review and 18 on the rest (T-27) | 18 everywhere |
| T7 | FAQ answers are 14 in the buy box and 16 in the FAQ section (T-26) | Both kept on purpose: buy box at 14, FAQ section at 16 |
| T8 | Footer column headings use 80% opacity text with no style | GT America Medium 14, caps, 80% opacity |
| T9 | Headings wrap wherever the frame width ends | Balanced wrapping for headings and pretty wrapping for copy. "Before / After" keeps its line break after the slash |

## Colour
| # | In Figma | In code |
| --- | --- | --- |
| C1 | "BG" and "neutral/BG" are the same colour under two names (T-4) | One palette entry, `linen` |
| C2 | Footer wordmark #695942 is one step off Sepia (T-7) | Sepia |
| C3 | Glass fill #E7DACE at 28% in one place and 30% in another (T-5) | One token: `oat` at 0.28 |
| C4 | The `Alpha/Light/40` style is actually 60% (T-6) | 60% |
| C5 | Carousel captions are Ink #181717 in one carousel and Clay in another (T-8) | Clay, the body text colour, everywhere |
| C6 | Product price is Clay, Sandstone or Sepia depending on the frame (T-9) | It follows the surface: foreground on plain surfaces, Sandstone on glass |
| C7 | The last review divider is Black, and the sticky title is Black (T-10) | Fossil divider; Clay title |
| C8 | Dividers are Fossil, Tan or Black in different places | One token, `divider` (Fossil) |
| C9 | Text over images is Sandstone in some frames and White in others | One token, `on_media` (Sandstone) |
| C10 | Inactive dots at 34%, timeline ticks at 30% (T-25) | Two tokens: inactive 0.34 and muted 0.8 |

## Components
| # | In Figma | In code |
| --- | --- | --- |
| K1 | Two primary button components (MAIN CTA and Button), with different padding and no text style on MAIN CTA (T-20) | One button system: Large 55, Medium 44, Small 40. The ATC label keeps its price |
| K2 | Button instances resized to 31, 43, 45 and 47 (T-19) | Snapped to 40, 44 or 55. "Take the test" and the spotlight "Shop now" use Small |
| K3 | Secondary button background is a raw hex; "Our science" is White (T-21) | Secondary uses the surface background. "Our science" is the white primary on images |
| K4 | Play icon in four sizes: 57, 40, 30.3 and 20.3 (T-22), plus 79 on the video banner | Three sizes: 79 on the video banner (Sandstone glyph, 12 blur), 57 large, 40 small |
| K5 | FAQ dividers differ on every item: top+bottom, bottom only, or none (T-26) | Every item has one bottom hairline |
| K6 | Carousel arrows drawn as 24×14 Clay arrows; Horizon renders a small thin chevron | Every carousel uses the same 24px arrow, and the disabled arrow uses the disabled opacity token |
| K7 | Carousel dots are 6px (12px tap area) | Superseded by P12: 6px dots 6 apart on 12 × 24 targets |
| K8 | Avatar radius is 0 in one quote card and round in another | Round everywhere |
| K9 | Badge padding is px10 py2 on one, px4 on another, px6 on a third | **Open:** to unify once the Recharge plans render (the savings and Recommended badges only appear with live plans) |
| K10 | The quote mark sits on the first line's baseline and pushes the line down | Hung outside the line box |
| K11 | The clinician laurel exists as a left half only | Mirrored on both sides of "Clinicians' Choice" |
| K12 | Ingredient image shadows: three different raw shadows (T-23) | No CSS shadow is applied. **Open:** the designer should confirm whether the exported PNGs need one baked in |
| K13 | "Real use" assumes five cards; with fewer, the row looks broken | Cards centre when they don't fill the row |
| K14 | Empty sections (for example ingredients with only Draft entries) would still take up a section gap | Empty sections collapse completely |
| K15 | Logo strip has 24 inner padding in Figma; it was lost when section padding was standardised | Restored: 24 on desktop and mobile |

## Content (fixed in schema defaults, not the client's data)
| # | In Figma | In code |
| --- | --- | --- |
| X1 | Typos: "reformated", "1Month", "12,00 Reviews", "WHATS" | Corrected in defaults |
| X2 | £ and $ mixed | Prices come from Shopify (USD) |
| X3 | Placeholder (Lorem ipsum) copy | Kept visibly as placeholder until the client supplies copy (D-7). Invented copy was removed from presets |


## Section-by-section Figma diff (2026-10-02)
Every home and PDP section was measured against its Figma node at 1440 and 390, and differences over 2px were fixed (about 70 in total). The full tables are in docs/qa/figma-diff-home.md and docs/qa/figma-diff-product.md. Where the Figma disagreed with itself:

| # | In Figma | In code |
| --- | --- | --- |
| G1 | Carousel cards: equal spacing between bar, card and card (Routine 372 cards with ~51 gaps, Lifestyle 296/397 with 84 gaps). The build had cards anchored to the left | Card sizes are ratios of the space between the bars (Routine 0.2816; Lifestyle 0.224 / 0.3005), spread with equal gaps, so they stay centred at any width. Bars match the side-card height |
| H1 | Carousel arrows sit at the content edges on Routine, Real use and Before/after, but under the side cards on Lifestyle | Every carousel's arrows are flush with the content edges, with the glyph on the edge, 30 below the cards |
| H2 | Header-to-cards gap is 28 on Routine and 64 on Lifestyle | 30 on both |
| H3 | Stat caption boxes are 310, 270, 208 and 252 wide, so identical copy would wrap differently | One cap of 310 |
| H4 | Product card titles: ExtraBold on the hero card, Medium on the lifestyle and before/after cards; image 124 on desktop and 92 or 124 on mobile | Card style uses ExtraBold 14; row and glass styles use Medium 14 (H5 style) with a 124 image (92 on mobile glass) and a 132 text column |
| H5 | Benefit captions wrap at 168, 101, 141 and 95 | One cap of 168 |
| H6 | Logos are hand-sized (28, 32 and 46 tall) in a 94 strip | Each logo fits a 168×32 box, and the strip keeps the Figma height of 94 through padding (30 top, 32 bottom) |
| H7 | Review stars are 16 with an 8 gap (Real use) and 15 with a 6 gap (Before/after) | 16 with an 8 gap everywhere |
| H8 | Stats panel pads 60 at the top and 24 at the bottom on mobile | 60 both |
| P1 | Buy-box gaps: 16 / 20 / 20 under the rating on desktop, 16 / 10 / 10 on mobile, 24 between every other block | Same values, as margins against the block gap |
| P2 | Header nav sits 337 after the logo, so it is off-centre | Nav centred on the page; item gap 48 as drawn |
| P3 | Sticky bar inset 24 from the page edge | On the 30 grid like everything else (L1) |
| P4 | Hotspot labels 26 high, the positions use the dot centre | Labels centred on the marker line |
| P5 | Footer wordmark bars are 47 wide on desktop but the hero bars are 30 | Footer bars keep the Figma ratio (bar = 0.27 × letter height, 46 desktop, 12 mobile) and extend past the letters by their width |
| P6 | PDP stars 15 with 6 gap; review-card stars 16 with 8 gap (see home H7) | Two sizes kept: buy-box rating at 6 spacing, cards at 8 |
| P7 | Small button label is GT America Medium 12 in one instance ("Take the test") and Akzidenz in the button set | Every button size uses the Akzidenz ExtraBold button style; Small is 12. One treatment for all buttons |
| P8 | Sticky CTA is 45 high, the main CTA 55 | Sticky uses Medium 44, main stays Large 55 |
| P9 | PDP description is 16 on both widths; body copy elsewhere is 14 on mobile | Description 16 on both widths |
| P10 | FAQ panel icons are 14, Horizon's are 16 | 14 in both accordions |
| P11 | Before/after product card: the home frame draws a compact card (Akzidenz Medium 14 title, small button), the PDP frame a large one (ExtraBold 24 title, full-width 43 button, 287 text column) | Section setting **Card size**: Compact (default, home) and Large (PDP template). Mobile is compact on both, as in both mobile frames |
| P12 | Slider dots are 6 squares 6 apart, tan with inactive at 34%; Horizon blended them with `difference` (they showed blue-grey) and each section had its own spacing (6 to 18 apart) | One global rule: 6 square, 6 apart, tan / 34%, no blend, every slider. Targets are 12 × 24, below the 24 × 24 guideline, at Jeet's request to match Figma exactly; swiping still works |
| P13 | UGC row: the mobile PDP frame puts a written review card fourth, the desktop PDP frame shows five creators only | PDP shows creators only on both widths; home interleaves review cards as drawn |
| P15 | Clinical-trial author photo is grayscale in Figma; the uploaded photo is colour | `filter: grayscale(1)` on quote-slider avatars |
| P16 | Light text on Clay: Figma uses Sandstone; Horizon's contrast helper picked the palette's pure white (announcement, header brackets, ticker, footer, review cards) | `contrast-override` prefers the page background (Sandstone) for light text when it passes 4.5:1 |
| P17 | Ingredient rows: row 1 centred, rows 2 and 3 top-aligned | All rows top-aligned |
| P18 | Before/after quote: Figma shows stars and name only, the data has a role line | Role not shown in the before/after card (still shown in the clinical-trial card) |
| P19 | Lifestyle glass card is white at 30%; the stats glass is #E7DACE at 28% | Two glass treatments: lifestyle white/30% with a Sandstone multiply thumbnail box, stats unchanged |
| P20 | Home featured product: Figma's button reads "ADD TO CART - $24.99/MO" with no plan choice on the page | The home button carries the one-time price; a subscription is only added where the plan cards are visible (product page) |
| P21 | Featured gallery and PDP: Figma draws no arrows on the main image and no selected-thumbnail outline | Arrows hidden, outline only on keyboard focus |
| P22 | Hero photo: Figma starts it under the solid announcement bar; Horizon put it behind | Photo starts at 34 on the first-section hero |
| P23 | Thumbnail rail end bars: Tan on the desktop frames, Fossil on mobile | Tan at 990 and up, Fossil below |
| P14 | Ingredient images: the PNGs in the file have uneven canvases (the witch hazel is tall portrait), so rows came out 270 to 470 high | Every image sits in the 112 × 94 box from the mobile frame (273 × 229 on desktop), object-fit contain |

### Height differences left on purpose (content, not layout)
- **Lifestyle:** about 49 shorter, because the Figma's middle-card caption is placeholder copy and is left empty until the client sends copy.
- **Before/after:** now has three comparisons (two are placeholders, D-12), so the arrows row shows as in Figma.
- **Real use:** cards come from content, and the UGC videos aren't uploaded yet.

## Additions beyond the Figma (2026-10-02)
| # | Gap in Figma | In code |
| --- | --- | --- |
| A1 | No collection page design. With two products, a grid shows two small cards | `product-showcase`: side-by-side product panels and a comparison table (Jeet chose this option) |
| A2 | The PDP split is only defined at 1440 (870 gallery / 482 buy box); at 1920 the image grew to about 1180 | Fluid split: the Figma at 1440, about 55/45 at 1920. The image never shrinks as the screen widens |
| A3 | Product photography was replaced in the store with white-backdrop, portrait images, so the square gallery cropped them | Product galleries use the images exactly as framed in Figma (square, 2× where the source allows). The Body Cloth: shelf, close-up, towel hands, squeeze, as in the Figma thumbnail rail. The 8: the warm stone shot first (from the Figma lifestyle carousel), then the white-backdrop pack. Jeet approved removing the five white-backdrop images; they're backed up in docs/data/backups/product-media-2026-10-02 |
| A4 | Type is only defined at 1440 and 390, so on a 1920 wrapper it read small | Fluid type from 1440 to 1920 for headings and body (tokens.md); unchanged at and below 1440 |
| A5 | The Shop mega menu wasn't designed; Horizon's default spread the links and cards across the full page | A compact, centred panel: links, a divider, and the two product cards |
