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
| K4 | Play icon in four sizes: 57, 40, 30.3 and 20.3 (T-22) | Two sizes: 57 large, 40 small |
| K5 | FAQ dividers differ on every item: top+bottom, bottom only, or none (T-26) | Every item has one bottom hairline |
| K6 | Carousel arrows drawn as 24×14 Clay arrows; Horizon renders a small thin chevron | Every carousel uses the same 24px arrow, and the disabled arrow uses the disabled opacity token |
| K7 | Carousel dots are 6px (12px tap area) | The dot stays 6px with a 24px tap area (accessibility) |
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
