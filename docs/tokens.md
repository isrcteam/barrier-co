# Tokens

## Source of truth
`docs/tokens.json` built by `tools/tokens/build_tokens.py` from the Figma variables. New build on Horizon 4.2.0: the token layer drives Horizon's colour schemes and font settings (see Fonts for the commercial-font caveat). Desktop breakpoint: proposed 1025 (iSourceit default). Horizon itself switches at 750 (239 uses) and 990 (16 uses), so custom sections switching at 1025 would sit beside stock ones switching at 750 and 990 (question T-12).

## Figma access
| File | Library files | Connected account | Seat | Status |
| --- | --- | --- | --- | --- |
| [BARRIER CO DEV READY](https://www.figma.com/design/oZ00gYRP11BAdFQYwo4fxj/BARRIER-CO-%7C%7C-DEV-READY--JEET--?node-id=965-1236&m=dev) | None with brand variables. Linked: community kits only (Material 3, Simple Design System, iOS/iPadOS 18 and 26, watchOS, visionOS, macOS 26) | jeet@isrcit.com | Full (isrcit team, pro) | Confirmed 2026-10-01: `get_metadata`, `get_variable_defs` read OK |

Pages: `READY FOR DEV` (965:1236) and `COMPONENTS` (976:3089).

Frames in scope:

| Frame | Node | Width |
| --- | --- | --- |
| Homepage | 965:1253 | 1440 |
| Homepage mobile | 965:3078 | 390 |
| PDP | 965:1998 | 1440 |
| PDP mobile | 965:3441 | 390 |
| PDP sticky add to cart | 965:1738 | 1440 |
| PDP mobile sticky add to cart | 965:4059 | 390 |
| PDP OP1 | 965:2655 | 1440 |
| PDP OP2 | 965:2857 | 1440 |
| OP2 / OP1 | 965:3065 | 1440 |
| Components | 977:968 | |

No frames for collection, cart (drawer or page), search, account, 404, blog, article or content pages (question T-1).

## Variable system in Figma
### Collections
Variables are local to this file, read with `get_variable_defs` on home, PDP, both mobile frames and the components section.

**Colour** (flat, no primitive/semantic split):

| Variable | Value |
| --- | --- |
| Sandstone | #F9F7ED |
| BG | #F0ECE1 |
| neutral/BG | #f0ece1 (duplicate of BG) |
| Clay | #322C27 |
| TAN | #A38D76 |
| Fossil | #BBAE9A |
| Sepia | #695A43 |
| Accent | #FFA83E |
| Ingenious Black | #181717 |
| Black | #000000 |
| White | #FFFFFF |
| Alpha/Light/20, /30, /40 | #FFFFFF (opacity not returned by the MCP) |
| Alpha/Dark/30 | #000000 (opacity not returned by the MCP) |

**Typography** (text styles exposed as variables):

| Style | Family | Weight | Size | Line height | Tracking |
| --- | --- | --- | --- | --- | --- |
| Display/Display Heading (60) | Akzidenz-Grotesk Next | 800 | 60 | 54px | 0 |
| Display/Display Heading | Akzidenz-Grotesk Next | 800 | 40 | 0.9 | 0 |
| Display/Heading Extra BOLD | Akzidenz-Grotesk Next | 800 | 36 | 0.9 | 0 |
| Display/Heading H1 | Akzidenz-Grotesk Next | 800 | 32 | 1.1 | 0 |
| Display/Heading H2 | Akzidenz-Grotesk Next | 800 | 24 | 1 | 0 |
| Display/Heading EX B | Akzidenz-Grotesk Next | 800 | 18 | 1 | 0 |
| Heading/H3 - Heading | Akzidenz-Grotesk Next | 500 | 20 | 100% | 0 |
| Heading/H4 - Heading | Akzidenz-Grotesk Next | 500 | 18 | 100% | 0 |
| Heading/H5 - Heading | Akzidenz-Grotesk Next | 500 | 14 | 100% | 0 |
| Heading/Heading Small | Akzidenz-Grotesk Next | 500 | 12 | 100% | 0 |
| LABEl & BUTTON/Button Primary | Akzidenz-Grotesk Next | 800 | 14 | 1.1 | 0 |
| LABEl & BUTTON/Label 12 | GT America | 500 | 12 | 1.1 | 0 |
| Body/Body 18 | GT America | 400 | 18 | 1.3 | 0 |
| Body/Body 16 | GT America | 400 | 16 | 1.3 | 0 |
| Body/Body 14 | GT America | 400 | 14 | 1.3 | 0 |
| Body/Body 12 | GT America | 400 | 12 | 100% | 0 |
| Body/Body 10 | GT America | 400 | 10 | 100% | 0 |
| Caption/20 | GT America | 400 | 20 | 100% | 4 |
| Caption/16 | GT America | 500 | 16 | 100% | 4 |

**Spacing and other number collections** (found by the components audit; `get_variable_defs` only reports variables that are bound, and almost none are):

| Collection | Values |
| --- | --- |
| 04 Spacing | 0, 4, 8, 10, 14, 16, 20, 24, 30, 40, 60, 86, 112 |
| 05 Radius | 0, 4, 5, 8, 16, 40, 999 |
| 06 Border | 0.5, 1, 2 |
| 08 Component sizes | button lg/md/sm height 55/44/40, select 44 |
| `space/lg` | 16, outside the local collection; the only number variable bound anywhere |

Colours are paint styles, not variables. The Alpha styles are white or black at 100/80/60/30/20/10/5%; `Alpha/Light/40` is actually 60%.

Effect styles exist (Blur 42/50/64, Elevation 1–3 and Modal in Clay) but no frame uses them; every shadow and blur in the frames is raw.

### Modes
None. Mobile uses separate styles (Display Heading 40 on mobile against Display Heading (60) on desktop) rather than a desktop/mobile mode.

### Aliasing
None. Every colour variable holds a raw value.

### Naming and SCSS mapping
Names are colour names (Sandstone, Clay, Sepia), which suits `color.palette`. Planned mapping: `Sandstone` → `palette.sandstone`, `BG` → `palette.linen` (renamed, "BG" is a role, not a colour; question T-4), `Ingenious Black` → `palette.ink`. Roles and schemes are built on top in `tokens.json`. Text styles map to `type.*` roles; mobile/desktop pairs are joined into one role with `mobile` and `desktop` sizes.

### Gaps (categories with no variables)
- Values exist but are not bound: spacing, radius, border and button heights are defined in Figma, but every node uses raw numbers.
- Breakpoints, gutters, section spacing, icon sizes, z-index and motion have no variables.
- Semantic roles (text, background, button) are missing, so the schemes are inferred from the frames.

### Line height and tracking
Text styles reported as "lineHeight 100" are AUTO in Figma and render as `normal`. These are H3–H5, Heading Small, Body 12, Body 10 and the Captions. Caption letter-spacing is 4%, which is 0.04em, the same value the live landing page uses.

### Horizon 4.2 colour model
Horizon 4.2 has no colour schemes. It has one `color_palette` setting plus per-section background and text pickers, and its `contrast-override` snippet derives `--color-foreground`, `--color-border` and the button variables. So the token roles use Horizon's variable names: `background`, `foreground`, `border` and `primary-button-*`. The five schemes in `tokens.json` (Sandstone, Linen, Clay, Tan, On image) document the surfaces each section offers as background presets. The palette goes into `settings_data.json` (`color_palette`), and the fixed colours become the theme settings group "Brand colors".

### How tokens reach the theme
`python3 scripts/build_token_css.py` writes `snippets/design-tokens.liquid`. It holds every size as a rem custom property, the desktop overrides at 990px, the opacity and effect tokens, the fixed colours read from settings, and one `.type-<role>` class per type role. Horizon builds style in plain CSS in each `{% stylesheet %}` and reference only these variables (core rules 1 and 2). `build_tokens.py --scss-only` also ran for the duplicate checks, but its SCSS output isn't used on Horizon.

Desktop switch: **990px**, the same as Horizon's own desktop breakpoint, so custom and stock sections change layout at the same width. The design has only 390 and 1440 frames.

## Fonts
| Family | Weights used | Source | Licence | Files supplied | Hosting |
| --- | --- | --- | --- | --- | --- |
| Akzidenz-Grotesk Next | 400, 800 supplied; 500 used in Figma | Commercial (Berthold) | Licence to confirm (T-2) | ExtraBold and Regular OTF, from the live theme | `assets/akzidenz-grotesk-next-{extrabold,regular}.woff2` |
| GT America | 400, 500 | Commercial (Grilli Type) | Licence to confirm (T-2) | Regular and Medium OTF, from the live theme | `assets/gt-america-{regular,medium}.woff2` |

The files came from the live theme's assets, so they're the client's own. They were converted to woff2 and subset to Latin plus punctuation, arrows, ™ and €, which took each file from about 105 KB to 16–20 KB. `snippets/brand-fonts.liquid` declares the faces, preloads ExtraBold and GT Regular, and points Horizon's `--font-*--family` variables at them, so stock components use the brand fonts too. Horizon's font pickers are set to the system `sans-serif`, so Horizon never preloads a library font.

**Akzidenz Medium (500) isn't among the supplied files.** Until it arrives, the Regular file is declared for weights 400–500, so the browser uses Regular rather than faking a bold. This affects H3–H5, Heading Small and the stat numbers (T-3).

## Token alignment report
Grouped by issue. Node-level detail is kept in the audit CSVs (homepage, PDP, components); the nodes listed are examples.

| # | Frame | Element | Value used | Nearest token | Issue | Proposal | Question for | Answer |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T-1 | All | Templates | Only home and PDP designed | n/a | No collection, cart, search, account, 404, blog, article, page or FAQ page frames | Style Horizon's stock templates with the tokens; ask for frames where a custom layout is wanted | Designer | Assumed |
| T-2 | All | Fonts | Akzidenz-Grotesk Next, GT America (commercial) | n/a | Web licences not confirmed | Use the files from the live theme | Client | Open |
| T-3 | Headings | H3–H5, Heading Small, stats | Akzidenz Medium 500 | Regular 400 | File not supplied | Regular until Medium is sent | Client | Assumed |
| T-4 | All | Palette names | "BG", "neutral/BG" (duplicate), "Ingenious Black" | linen, ink | A role name used as a colour name; a duplicate style | Rename in code to linen and ink; one entry | Designer | Assumed |
| T-5 | Stats, PDP benefits | Glass card fill | #E7DACE at 28% and 30% | none | Raw colour with two opacities | New palette colour `oat` with one opacity, 0.28 | Designer | Assumed |
| T-6 | Stats | Glass card border | White at 60% via `Alpha/Light/40` | white + opacity 0.6 | The style's name says 40 but its value is 60 | Use 60% | Designer | Assumed |
| T-7 | Footer | Wordmark | #695942 | sepia #695A43 | One step off Sepia | Merge into sepia | Designer | Assumed |
| T-8 | Carousels | Caption text | Ink #181717 | clay | Other body copy is Clay | Keep ink as the fixed colour "Carousel caption" | Designer | Open |
| T-9 | Home, PDP | Product price | Clay, Sandstone, Sepia | n/a | Same element in three colours | Follows its surface: Sandstone on dark glass, Sepia on light cards | Designer | Assumed |
| T-10 | PDP | Last review divider; sticky title | Black #000000 | fossil, clay | Every other instance uses Fossil or Clay | Fossil and Clay | Designer | Assumed |
| T-11 | All | Spacing | ~30 gap and ~25 padding values, including fractional ones (8.132, 9.072, 24.192, 2.184) | Figma scale 4–112 | Nothing bound; 12 is the most used gap but isn't on the scale | Scale = Figma's plus 2, 6, 12, 80; snap 5→4, 7/9→8, 15/17→16, 19→20, 27/28→30, 50/56→60, 84/85→86; fractional values rounded | Designer | Assumed |
| T-12 | All | Breakpoint | Frames at 390 and 1440 only | 990 | No tablet frames | Switch to desktop at 990, the same as Horizon | Jeet | Assumed |
| T-13 | Mobile | Gutter | 10, with 16 and 17 in places; top bar 37 | layout.gutter-mobile 10 | Inconsistent | 10 everywhere; header 16 to match the nav component | Designer | Assumed |
| T-14 | Desktop | Benefits row, Stats, banner | Fixed 1150 at x145; insets of x30 + 30 | content-width 1380 | Off the page grid | Benefits row max-width 1150 centred; Stats keeps its own padding | Designer | Assumed |
| T-15 | Several | Text without a style | Top bar Akzidenz Regular 12; nav GT Medium 14; stats 96/70 and 64/53; % at 44; mini card 24 | announcement, nav, stat, stat_unit, h2 | 98 text segments have no style | New type roles: announcement, nav, stat, stat_unit | Designer | Assumed |
| T-16 | Header | Mobile vs desktop nav | Mobile Akzidenz ExtraBold 14; desktop GT Medium 14 | button, nav | Different families | Keep both as designed | Designer | Open |
| T-17 | Home | Mixed-style paragraphs | First line Akzidenz Medium or GT Medium inside Body | n/a | One text node, two styles | Rich-text bold maps to medium weight | Designer | Assumed |
| T-18 | Buttons | States | Opacity 86/72/35%; focus is a Clay glow | opacity tokens, effect-focus-ring | No colour change on hover | Implement as designed; keyboard focus also keeps a visible outline for WCAG | Jeet | Assumed |
| T-19 | Buttons | Sizes in use | 31 (Take the test), 43, 45, 47 | 40, 44, 55 | Instances resized off the set | Small 40, Medium 44, Large 55; the mobile ATC uses Large | Designer | Assumed |
| T-20 | Buttons | Two primary components | MAIN CTA (667) vs Button (676) | button-large | Duplicate component; MAIN CTA has no text style or states | One button system; the price in the ATC label stays ExtraBold, separators Medium | Designer | Assumed |
| T-21 | Buttons | Secondary background | Raw #F9F7ED; "Our science" uses White | sandstone, white | Not linked to a style | Secondary uses the background colour | Designer | Assumed |
| T-22 | Components | Play icon | 57, 40, 30.333, 20.333 | icon play-large 57, play-small 40 | Four sizes | Two sizes | Designer | Assumed |
| T-23 | PDP | Ingredient image shadows | Three different raw shadows | none | No effect style used | Bake the shadow into the PNG asset; no CSS shadow | Designer | Assumed |
| T-24 | Several | Blurs | 30, 27, 6, 60, 24, 12.77, 8.56 | blur-glass 30, blur-card 27, blur-label 6 | Effect styles 42/50/64 unused | Three blur tokens | Designer | Assumed |
| T-25 | Several | Inactive opacity | Dots 34%, timeline ticks 30%, footer labels 80% | opacity inactive 0.34, muted 0.8 | Inconsistent | Two tokens | Designer | Assumed |
| T-26 | PDP, FAQ | FAQ answer size and dividers | Body 14 vs 16; borders differ per item | body-small | Same component, different values | Body 14 in the buy box, 16 in the FAQ section; one divider rule (bottom border on every item) | Designer | Assumed |
| T-27 | PDP | Reviewer name | 20 vs 18 | h4 | Inconsistent | 18 | Designer | Assumed |
| T-28 | Mobile | Layout bugs | Fixed widths of 458, 453 and 382 in a 370 container; video cards 1px wide | n/a | Overflow | Fluid widths | n/a | Fixed in build |
| T-29 | Content | Copy | £ and $ mixed; "reformated"; "1Month"; "12,00 Reviews" | n/a | Placeholder or typo | The store currency is USD, so prices come from Shopify; typos fixed in schema defaults | Client | Assumed |
| T-30 | PDP | Hero image overlay | OP1 seal chip vs OP2 "Save 25%" + NEA card | n/a | Two options | Build OP2 (it matches the main PDP frame) with the badge from `custom.media_badge`; the seal chip stays an option | Jeet | Open |

## Merges and rounding log
| Date | From | To | Reason | Designer OK |
| --- | --- | --- | --- | --- |
| 2026-10-01 | neutral/BG #f0ece1 | linen | Duplicate of BG | |
| 2026-10-01 | #695942 | sepia | One step off | |
| 2026-10-01 | Glass 0.30 | 0.28 | Two opacities for one surface | |
| 2026-10-01 | 24.192, 8.132, 9.072, 2.184, 30.333, 26.211 | 24, 8, 8, 2, 30, 26 | Scaled-layer artefacts | |
| 2026-10-01 | Gaps 5, 7, 9, 15, 17, 19, 27, 28, 50, 56, 84, 85 | 4, 8, 8, 16, 16, 20, 30, 30, 60, 60, 86, 86 | Off the scale | |

## Fluid type above 1440 (2026-10-02, Jeet)
Type matches the Figma exactly up to 1440. Between 1440 and 1920 the roles below grow linearly, using `clamp()` generated from `type.<role>.wide` in tokens.json. From 1920 up they stay at the wide size. Mobile and laptop are unchanged.

| Role | ≤1440 | 1920+ |
| --- | --- | --- |
| display, h1 | 60 | 72 |
| h2 | 36 | 42 |
| body_large | 18 | 20 |
| body | 16 | 18 |
| body_small | 14 | 16 |
| eyebrow | 20 | 22 |

Captions, labels, buttons and stats keep their sizes. Why: on a 1920 wrapper, 1440-sized type read small, with long line lengths. Text boxes sized for a heading scale with it; for example, the inset banner's text width is 8 × the h1 size, so it keeps its four-line break.
