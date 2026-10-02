# Figma diff: home page (`/`)

Figma: HOMEPAGE 965:1253 (1440) and HOMEPAGE MOBILE 965:3078 (390). Build measured on theme 167298138367 with `getBoundingClientRect`, relative to each section's top-left, on 2026-10-02. Values are px. "OK" means within 2px after the fix.

## Hero (965:1254), `hero-banner`
| Element | Figma | Build (before) | Fix |
| --- | --- | --- | --- |
| Hero height incl. top bar, desktop | 34 + 745 = 779 | 836 (press strip started 57 low) | Min height `80×10−20` = 780. OK |
| Hero height incl. top bar, mobile | 34 + 700 = 734 | 700 | Min height `80×9+14` = 734. OK |
| Spotlight button width | 200 (full card width) | 90 | `width: 100%` in `product-spotlight`. OK |
| Copy block, bar, heading, body, card | as Figma | within 3 | Body sits 30 below the heading, not 27 (L7 snap) |

## Intro (965:1329), `intro-media`
| Element | Figma | Build (before) | Fix |
| --- | --- | --- | --- |
| Title column | 714 wide, heading on 2 lines (108) | 675, heading on 3 lines (162), section +54 | Columns `1fr / 636`, gap 30. OK (839 tall, as Figma) |
| Body | x 744, 636 wide | x 770, 640 wide | Same fix. OK |

## Routine (965:1339), `image-carousel`
| Element | Figma | Build (before) | Fix |
| --- | --- | --- | --- |
| Cards, bars, labels, captions | 372 cards, 51 gaps | OK | None. The rebuilt geometry is verified |
| Arrows x | glyphs flush at 30 and 1410 | 66 and 1374 (inside the bars) | Desktop: controls widened by the bar width, and the arrow buttons lose their inline padding. OK |
| Arrows y (glyph centre) | 743 | 740 | 30 gap between cards and controls. 744. OK |
| Mobile dots | centred, 27 below the caption | left-aligned, 46 below | Dots centred, 4 gap. OK |

## Featured product (965:1385): stock. Deltas are listed in the summary for brand-overrides.

## Real use (965:1433), `video-testimonials`
| Element | Figma | Build (before) | Fix |
| --- | --- | --- | --- |
| Arrows y | glyph centre 475 | 446 (no gap under the cards) | 30 margin. 474. OK |
| Arrows x | 30 / 1410 | 36 / 1404 | Padding removed. OK |
| Stars | 16 each, 8 gap (112 wide) | 16 each, 2 gap (90 wide) | `star-rating` medium: 8 spacing, trailing space trimmed. OK |
| Disabled arrow | not drawn | hidden (`visibility`) | Disabled opacity, as K6 |
| Section height | 492 | 498 | The arrow frame is 44 (tap target), not 34. Accepted |
| Mobile dots | centred | left | Centred. OK |
| Video cards | 3 of 5 cards are videos | only 2 quote cards render | **Template:** add the 3 video blocks |

## Stats (978:4083), `clinical-results`
| Element | Figma | Build (before) | Fix |
| --- | --- | --- | --- |
| Panel height | 672 | 636 | Cards use the Figma ratio 462/276. OK |
| Grid | x 426, 924 wide, cards 462×276 | x 447, 903 wide, 452×258 | Columns `1fr / 70%`, no gap. OK |
| Number / caption top in card | 66 / 152 | 60 / 151 (centred in a shorter card) | Figure is `0.7×` the stat size tall; bottom padding +12. 66 / 152. OK |
| Caption width | 310 / 270 / 208 / 252 | 331 | Capped at 310 for all four (correction H5) |
| Mobile card | 185×195, number 40, caption 101 | 185×206 | Figure height fix. 195 / 40 / 101. OK |

## Benefit icons (965:1502), `feature-icons`
| Element | Figma | Build (before) | Fix |
| --- | --- | --- | --- |
| Icon box | 110×110 | 110×114 | Fixed height. OK |
| Column step | 310 (220 + 90) | 309 (223 + 86) | Gap 86 + 4. OK |
| Caption width | 168 widest | 223 | Max 168 on desktop and mobile. OK |

## Banner (965:1579), `hero-banner` inset
| Element | Figma | Build (before) | Fix |
| --- | --- | --- | --- |
| Text inset | 45 | 40 | 40 + 6. OK |
| Body | 16 | 18 | Inset banner body uses the body size (16). OK |
| Button | 253×43 | 254×55 (Large) | Medium, as K2. OK |

## Lifestyle (965:1587), `image-carousel` tall
| Element | Figma | Build (before) | Fix |
| --- | --- | --- | --- |
| Section top | heading at 0 (plain section) | heading at 40 (40 default padding) | **Template:** set lifestyle padding to 0 / 0 / 0 / 0 (L6) |
| Header to cards | 64 | 30 | Kept at 30, as Routine (H2) |
| Cards and bars | 296 / 397×458 / bars 28 | OK | None |
| Arrows x | under the side cards (142 / 1299) | 64 / 1376 | Content edges 30 / 1410, as every other carousel (H3) |
| Glass product card | 374×148, inset 10, image 124, gap 20, body 132, title Medium 14 | 374×119, inset 12, image 86, gap 12, ExtraBold | Snippet row/glass layout rebuilt. 378×148. OK |
| Mobile glass card | 298×128, image 92, padding 6 | image 86, padding 10 | Fixed. 298×125. OK |
| Middle caption | "Lorem ipsum…" under the middle card | missing | **Template:** add a caption to the middle card |
| Mobile first slide | middle (product) card | first card | Not fixed: Horizon ignores `initial_slide` here. Open |
| Subheading, mobile | 18 | 16 (body-large mobile) | Token level. Open |

## Before / after (965:1614), `before-after`
| Element | Figma | Build (before) | Fix |
| --- | --- | --- | --- |
| Product card | 338×148, title Medium 14 | 428×138, title 24, image 86 | Shared snippet fix plus end padding 50. 338×148. OK |
| Labels | Akzidenz Medium 14, 86×34 | GT America 12, 79×29 | `type-h5`. 84×34. OK |
| Arrows | below the quote, flush to the column | none (only one comparison) | **Template:** add comparison blocks. When there are more, the arrows follow the shared rule |
| Disabled arrow | n/a | hidden | Disabled opacity (K6) |

## Instagram (978:4357), `social-gallery`
| Element | Figma | Build (before) | Fix |
| --- | --- | --- | --- |
| Tile | 252×290, step 268 | 241×277 | Width `(100% + gutter) / 5.6`. 252×290. Section 454. OK |

## Logos (965:1668), `logo-list`
| Element | Figma | Build (before) | Fix |
| --- | --- | --- | --- |
| Logo sizes | Equinox 129×28, Delta 168×32, Credo 96×46 | all 32 tall: 242 / 179 / 92 wide | Logos fit a 168×32 box (`object-fit: contain`): Delta 168, Credo 92, Equinox 168 (H6) |
| Strip height | 94 | 80 | 24 + 32 + 24. Kept (H6) |

## Corrections (ready to merge into design-corrections.md)
| # | In Figma | In code |
| --- | --- | --- |
| H1 | Carousel arrows sit at the content edges on Routine, Real use and Before/after, but under the side cards on Lifestyle | Every carousel's arrows are flush with the content edges, with the glyph on the edge, 30 below the cards |
| H2 | Header-to-cards gap is 28 on Routine and 64 on Lifestyle | 30 on both |
| H3 | Stat caption boxes are 310, 270, 208 and 252 wide, so identical copy would wrap differently | One cap of 310 |
| H4 | Product card titles: ExtraBold on the hero card, Medium on the lifestyle and before/after cards; image 124 on desktop and 92 or 124 on mobile | Card style uses ExtraBold 14; row and glass styles use Medium 14 (H5 style) with a 124 image (92 on mobile glass) and a 132 text column |
| H5 | Benefit captions wrap at 168, 101, 141 and 95 | One cap of 168 |
| H6 | Logos are hand-sized (28, 32 and 46 tall) | Each logo fits a 168×32 box. The strip is 80 tall, not 94 |
| H7 | Review stars are 16 with an 8 gap (Real use) and 15 with a 6 gap (Before/after) | 16 with an 8 gap everywhere |
| H8 | Stats panel pads 60 at the top and 24 at the bottom on mobile | 60 both |
