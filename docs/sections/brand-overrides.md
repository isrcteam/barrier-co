# brand-overrides

## Ticket
From docs/architecture.md ("Stock sections: styling plan"). Figma: header 977:705, footer 966:753 / 966:917, buttons 676:177, FAQ item 977:1007, buy box 965:2045, sticky add to cart 965:1973 / 965:4237, gallery in 965:2031 / 965:3458, press marquee 965:1296, ticker 965:1384.
- Global buttons: square, uppercase, `button` type role; Large 55 / Medium 44 / Small 40; hover, pressed and disabled by opacity; focus via `--effect-focus-ring`; `.button--medium` and `.button--small` modifiers.
- header-announcements: Clay bar, announcement type role, thin chevrons.
- header: logo left, menu centred (nav role, uppercase), utilities as "| SEARCH |", "| PROFILE |", "| CART |"; transparent white over the home hero; Clay on Sandstone elsewhere; mobile MENU · logo · CART.
- marquee: Tan press strip; Clay ticker in `title_bold` uppercase with bar separators.
- product-information / featured product: thumbnail rail left on desktop, horizontal thumbnails between Fossil bars on mobile, square edges, buy box 482, title h2 role, FAQ-style accordion rows, sticky add-to-cart bar per 965:1973.
- footer: Clay, underline email input with SUBMIT, column headings at 80%, "| BARRIER |" jumbo text, legal row.
- Slideshow arrows and Tan dots (inactive at `--opacity-brand-inactive`).

## Plan
- One snippet, `snippets/brand-overrides.liquid`, holding a single `{% stylesheet %}` (about 2.3 KB gzipped). No markup, no JS, no stock file edited. Jeet adds `{% render 'brand-overrides' %}` to the layout.
- Everything that Horizon exposes as a setting is done by settings (see `docs/locale-fragments/brand-overrides.settings.md`); CSS only covers what settings can't reach.
- Every selector is scoped by a stock wrapper (`.header`, `.announcement-bar`, `.product-information`, `.product-details`, `.sticky-add-to-cart`, `footer`, `slideshow-controls`, `marquee-component`).
- Buttons: size by Horizon's own `--button-padding-*` variables (20/40 gives 55), modifiers set `min-block-size` from the layout tokens. Hover keeps the same colours and drops opacity; Horizon's colour-shift hover is neutralised.
- Header: Horizon's "Text" utility style (`actions_display_style: text`) gives the words; CSS frames each word with `border-inline` bars (2 = `--border-strong`, 8 gap). Mobile un-hides the cart word, hides the cart/menu icons and prints the menu summary's own `aria-label` ("Menu") as text, so names stay translated and accessible.
- Ticker: a marquee whose blocks are all text blocks gets the `title_bold` role and a Fossil "|" before each word (generated content with empty alt text, so screen readers skip it). The press strip has image blocks, so it is untouched.
- Gallery: rail and bars are pseudo-elements on Horizon's thumbnail list; they become horizontal top/bottom bars in the left rail and vertical end bars in the mobile row.
- Footer bars: two pseudo-elements on `jumbo-text`, which gets inline margin so Horizon's fit-to-width script still measures only the word.

## Reasoning
- **What:** brand styling of stock Horizon sections through one scoped stylesheet plus settings.
- **Why:** keeps stock files untouched so Horizon updates merge; settings carry anything the merchant may want to change.
- **Alternatives rejected:** editing stock section stylesheets (merge conflicts); custom header/footer sections (lose Horizon's drawer, sticky, transparent and predictive search logic); a JS shim for the header labels (not needed, the text mode exists).
- **Impact:** about 2.3 KB gzip on the bundled CSS. Fossil hairlines read `var(--color-input-border)`, which Horizon fills from `palette_input_border` (Fossil); if that setting changes, the hairlines change too. Mobile header hides search and account to match the design (account is in the menu drawer; search is not).
- **Deviations:** announcement arrows 34 tall (design bar height) instead of the 44 touch size; mobile thumbnails 74 = `--space-60 + --space-14`; footer jumbo gap 112 desktop / 24 mobile from the frames; the sticky bar keeps Horizon's content (no subscription select); on-media slideshow arrows keep Horizon's white hover style, only in-flow arrows and dots are restyled.
- **Approver:** Jeet (delegated).

## QA checklist
- [ ] Buttons: any `.button` is square, Akzidenz ExtraBold 14 uppercase, 55 tall; `.button--medium` 44, `.button--small` 40 with Akzidenz Medium 12. Hover 86%, pressed 72%, disabled 35% opacity, no colour change. Keyboard focus shows the glow plus the outline.
- [ ] `.button-unstyled` controls (thumbnails, slideshow dots, drawer close) are unchanged.
- [ ] Announcement bar: Clay, Akzidenz Regular 12 uppercase, thin chevrons at the edges, bar 34 tall.
- [ ] Header 1440: logo left, SHOP / SCIENCE / ABOUT centred in GT Medium 14 uppercase, "| SEARCH |", "| PROFILE |", "| CART |" right. Home: transparent, white text, inverse logo. Other pages: Sandstone with Clay text.
- [ ] Header 390: "| MENU |" left, logo centred, "| CART |" right in Akzidenz ExtraBold 14; tapping MENU opens the drawer and shows the close icon; screen reader reads "Menu" and "Cart".
- [ ] Cart count bubble sits next to CART without overlapping.
- [ ] Home press strip: Tan, logos and quotes unchanged. Ticker: Clay, words in Akzidenz ExtraBold 18 uppercase, Fossil bars between, 20 apart; screen reader does not read the bars.
- [ ] PDP 1440: 80 thumbnails in a left rail with Fossil bars above and below; buy box 482 wide; title Akzidenz ExtraBold 36 uppercase; square media.
- [ ] PDP 390: 74 thumbnails in a row below the image between Fossil end bars.
- [ ] Accordion rows: plus/minus icon left of an Akzidenz Medium 14 uppercase title, 20 padding, Fossil hairline under each row and above the first, answer indented 24.
- [ ] Sticky bar 1440: white, square, shadow above, 30 padding, 80 image, title in `title_bold` uppercase, ADD TO CART at the right. 390: full width, image + info, full-width ADD TO CART below with its label; content clears the home indicator.
- [ ] Footer: Clay; headings GT Medium 16 uppercase at 80%; email input underlined with a Sandstone SUBMIT button 30 tall; "| BARRIER |" with bars at both edges (30 desktop, 12 mobile).
- [ ] Carousel dots: square Tan dots at 34%, active at 100%; no blend mode.
- [ ] Reduced motion: no button transition.

## Merchant guide
This file has no settings. The look comes from theme settings and section settings:
1. Theme settings > Buttons: keep corner radius 0 and text case uppercase. Theme settings > Icons: stroke Thin.
2. Header: keep "Utility style" on Text and the menu font on Subheading. To change the home header colour, edit "Transparent header text" on the home page.
3. Marquee ticker: add only Text blocks (one word each); the bars appear automatically. Adding an image or icon block turns the bars off (the press strip style).
4. Product page: in the media gallery keep "Carousel" with thumbnails on the left; add FAQ rows with an Accordion block (icon Plus, dividers off).
5. Footer: keep the jumbo text block last so it spans the full width.

### Reasoning, 2026-10-02: product gallery / buy box split on wide screens
- **What:** the PDP and featured product grid is `minmax(0, 1fr)` for the gallery and `max(sidebar, sidebar + (100% − (content − 480)) × 0.75)` for the buy box. The buy box content is capped at 640.
- **Why:** Jeet: the image looks too big on large screens. With the old fixed 2:1 split, the image grew to about 1180 at 1920.
- **Result (image size / split):**

  | Width | Image | Split |
  | --- | --- | --- |
  | 1280 | 620 | 59/41 |
  | 1440 | 780 | 64/36 (the Figma) |
  | 1600 | 820 | 60/40 |
  | 1920 | 900 | 54/46 |

  The image never shrinks as the screen widens.
- **Alternatives rejected:**
  - A breakpoint switch to 55/45 at 1441: the image shrank from 780 to 743 at 1600.
  - Horizon's "constrain to viewport": it limits by height, not by the split.
- **Approver:** Jeet.
