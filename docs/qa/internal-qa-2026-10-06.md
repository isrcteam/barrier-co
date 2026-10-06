# Internal QA round and Dev Ready annotations, 2026-10-06

Sources: the internal QA sheet (82 rows: home, PDP, collection, cart) and the 10 Dev Ready annotations on page 776:4700 of file V6s6rko0NxG4CPfctCnH29. Checked on the development theme through `shopify theme dev` at 1440 and 390, plus 2560, 1280, 1024 and 768 for the new sustainability page. Nothing is committed or pushed yet.

Status key: **Fixed** (changed and checked in the browser), **Checked** (already right; confirmed), **Needs input** (waiting on someone), **Not theme** (outside the theme's control).

## Homepage
| Row | Section | QA note | Status | What changed |
| --- | --- | --- | --- | --- |
| 2 | Announcement | Centre the text | Checked | Centred at 1440 and 390 |
| 3 | Hero | CTA text looks small | Fixed | Spotlight button is the Medium size |
| 4 | Hero | Bottom-align text and product | Fixed | Content aligns to the bottom on desktop |
| 5 | Intro | Build the other option too | Fixed | Two-tile version shown; the single-video version (annotation 8) is built and disabled in the template |
| 6 | Press marquee | Too fast; match the ticker | Fixed | Both marquees run at a constant 40 px/s at every width (and a Horizon resize bug is fixed) |
| 7 | Routine | No background colour | Fixed | Dev Ready shows the Linen band on mobile only; the new setting **Background on mobile only** is on (design-corrections D2) |
| 8 | Routine | Hide arrows | Fixed | New **Show arrows** setting, off |
| 9 | Featured product | Thumbnails move on scroll; 5px between rail lines and thumbnails | Fixed | Rail no longer sticky; 5px spacing |
| 10 | Featured product | Accordion headings bolder | Fixed | Akzidenz Medium emulated site-wide (D1) |
| 11 | Featured product | One accordion open at a time | Fixed | Native exclusive `<details name>` |
| 12 | Real use | Trackpad scrolling | Fixed | |
| 13 | Real use | Reviewer name bold | Fixed | Medium emulation |
| 14 | Real use | No arrows when there are only 4 reviews | Fixed | Arrows hide when every card fits |
| 15 | Clinically proven | Animate the numbers | Fixed | Count-up when the row scrolls into view (setting; off for reduced motion) |
| 16 | Clinically proven | Numbers too light | Fixed | Medium emulation on the stat style |
| 17 | Clinically proven | Lines too dark | Fixed | Divider at the faded opacity token |
| 18 | Clinically proven | Captions always on two lines | Fixed | Captions balance themselves to two lines |
| 19 | Icons | Captions always on two lines | Fixed | Line breaks as in Figma, no width cap |
| 20 | Inset banner | Paragraph width wrong | Needs input | Measures as Figma (483 at the 60 heading). Which width did you expect? |
| 21 | Comparison table | Missing | Fixed | New `product-comparison` section (D6) |
| 22 | Lifestyle | Arrows should highlight the next image | Fixed | Centre mode: arrows move the focus card |
| 23 | Lifestyle | Product card appears on hover | Fixed | Product glass card shows on hover or focus |
| 24 | Lifestyle | Product text width | Fixed | Title column 132 as in Figma |
| 25 | Before/after | Belongs on the PDP | Fixed | Removed from the homepage |
| 26 | Instagram | No hover on the heading | Fixed | |
| 27 | Logos | Too large, not centred | Fixed | Per-logo heights (18, 30, 34) and centred |
| 28 | Footer | Wrong footer | Fixed | Desktop footer rebuilt to Figma (D3) |
| 29 | Announcement (mobile) | Scroll or rotate | Checked | Rotates every 5 seconds |
| 30 | Intro (mobile) | Text width | Fixed | 17px inset as in Figma |
| 31 | Routine (mobile) | Text width | Fixed | |
| 32 | Featured product (mobile) | Main image 1:1 | Fixed | |
| 33 | Featured product (mobile) | CTA too tall | Fixed | Medium buttons |
| 34 | Real use (mobile) | More space above | Fixed | 63px from the accordion to the heading, as in Figma |
| 35 | Real use (mobile) | Cards cut off at the end | Fixed | Track runs to the screen edge |
| 36 | Real use (mobile) | Indicator squares have a border | Fixed | Selected-dot ring removed everywhere |
| 37 | All | Copy needs updating | Needs input | Final copy from the client (plan D-7) |
| 38 | All | Sticky header only on scroll up | Fixed | Header sticky mode: scroll up |

## PDP
| Row | Section | QA note | Status | What changed |
| --- | --- | --- | --- | --- |
| 39 | Breadcrumbs | Space under the header | Fixed | About 20px, as in Figma |
| 40 | Gallery | Space between lines and thumbnails | Fixed | 5px |
| 41 | Gallery | Highlight the selected thumbnail | Fixed | Outline on the selected thumbnail |
| 42 | Gallery | Tag and verification badge on the main image | Fixed | Gallery settings **Badge text** and **Show recognition seal** |
| 43 | Clinicians' choice | Bolder text and symbol | Fixed | |
| 44 | Clinicians' choice | "View clinicians" clickable | Fixed | Links to the clinical-trial quotes on the page |
| 45 | Clinicians' choice | Smaller divider bar | Fixed | |
| 46 | Subscriptions | Price and plan text bolder | Fixed | |
| 47 | Subscriptions | Space around the perks separator | Fixed | |
| 48 | Recognition | Title bolder | Fixed | |
| 49 | Recognition | Indicators without border | Fixed | |
| 50 | Recognition | Left border darker after sliding | Fixed | Border drawn on the slide track, not each card |
| 51 | Confused about which item | Bold text, Figma width | Fixed | Body capped at 232 |
| 52 | Clinical trial | Doctor's name bolder | Fixed | |
| 53 | Clinical trial | Indicators without border | Fixed | |
| 54 | Accordion | Headings bolder | Fixed | |
| 55 | Accordion | One open at a time | Fixed | |
| 56 | Sticky ATC | Appears too early | Fixed | Shows once the whole product section has scrolled past |
| 57 | Sticky ATC | Too tall | Fixed | Compact bar |
| 58 | Sticky ATC | Second outline on the dropdown | Fixed | |
| 59 | Routine | Titles bolder | Fixed | |
| 60 | Clinically proven | Same points as the homepage | Checked | Same four results on both |
| 61 | Key ingredients | Title, image and name top-aligned | Fixed | |
| 62 | Key ingredients | Ticks too small | Fixed | Tick size from Figma, now a token |
| 63 | Before/after | Square photos | Fixed | |
| 64 | Before/after | Name bolder | Fixed | |
| 65 | Before/after | "Before & after 14 days" bolder | Fixed | |
| 66 | FAQ | Questions bolder | Fixed | |
| 67 | FAQ | One open at a time | Fixed | |
| 68 | Instagram | Remove from the PDP | Fixed | Section setting **Hide on product pages** |
| 69 | Routine (mobile) | Text on the image | Fixed | Hotspots and callouts on the image, with mobile positions |
| 70 | FAQ (mobile) | Image missing | Fixed | |
| 71 | FAQ (mobile) | No background colour | Fixed | |

## Collection
| Row | Section | QA note | Status | What changed |
| --- | --- | --- | --- | --- |
| 72, 77 | Products | Ticks small and light | Fixed | Same tick as the homepage table |
| 73 | Products | Show certification badges | Fixed | Recognition seals under each product |
| 74 | Products | CTA too large, text too small | Fixed | Medium full-width button |
| 75 | Comparison table | Match the homepage style | Fixed | Uses the homepage comparison columns; points come from `custom.comparison_points` when that metafield exists |
| 76 | Comparison table (mobile) | Titles on one line | Fixed | |

## Cart
| Row | Section | QA note | Status | What changed |
| --- | --- | --- | --- | --- |
| 78 | Empty cart | Heading and close missing | Fixed | |
| 79 | Cart | Heading font | Fixed | Akzidenz ExtraBold |
| 80 | Header | Count inside "\| CART 2 \|" | Fixed | |
| 81 | Cart | Heading and close style | Fixed | "\| CLOSE \|" like the menu |
| 82 | Header | Square count, not a circle | Fixed | |
| 83 | Cart | 3-month and 1-month plans add as the same item | Not theme | No Recharge selling plans exist yet, so every add is a one-time purchase. Once the plans exist, each plan adds as its own line (plan D-13) |

## Dev Ready annotations
| # | Annotation | Status |
| --- | --- | --- |
| 1 | Featured product: "As per PDP" | Fixed: same gallery as the PDP (1:1 main image, thumbnail rail, badge) |
| 2 | Real use: "Pause and Play video" | Fixed: tap pauses and plays, no native controls |
| 3 | Clinically proven: "Numbers need to have the animation" | Fixed (row 15) |
| 4 | Comparison: "to be developed and carried forward on the Collection page" | Fixed (rows 21, 75) |
| 5 | Lifestyle: "next card should come in centre" | Fixed (row 22) |
| 6 | Lifestyle product: "Comes on hover" | Fixed (row 23) |
| 7 | Logos: "Marquee on mobile, desktop stays static" | Checked |
| 8 | Intro single video: "Also to be developed, but hidden" | Fixed: built and in the template, disabled |
| 9 | Hero product card: "sticky, moves to the bottom of the viewport" | Fixed: docks to the bottom on mobile once the hero scrolls past (setting **Keep on screen on mobile**); it covers the homepage, not other pages |
| 10 | PDP "Try once": "Make it look like it's clickable" | Fixed: underlined |

## Sustainability page (new)
Built from the "Sustainablity + Pact Final" frames (787:9003 desktop, 787:9428 mobile) on a new `landing` layout. Viewable on the dev theme at `/pages/contact?view=sustainability` until a real page exists. Measured against Figma at 1440 and 390: type sizes, insets and the page height (5486 vs 5469 on mobile) match. Normalised sizes are listed in design-corrections D7–D11.

Store set-up done 2026-10-06: the 12 images are in Files, and the page "Sustainability" (`/pages/sustainability`, template `page.sustainability`) exists, hidden. Certification logos now take their own heights from Figma (72, 62, 100, 70, 86 on desktop; wide logos fit a 100 square on mobile).

Open before it can go live:
- Publish the page (Jeet).
- Pact links point to pactcollective.org as placeholders (plan D-21).
- The production diagram's Sandstone-on-Tan labels are about 2.9:1 (D10).

## Checks
- Schema validation: no new errors compared with HEAD. The new warnings are the validator flagging the "Same at mobile" toggles themselves, plus split-banner's mobile tile height, which is a separate stacked-tile measure rather than a mobile copy of the desktop height.
- Theme check: the same findings as HEAD (translations in other locales, header settings count, header-drawer complexity, the Judge.me app block).
- CSS check: unchanged count (365, all in stock Horizon files). Names: every new file is free in Horizon upstream.

## Follow-ups from Jeet's review (2026-10-06)
| Item | Change |
| --- | --- |
| How it works: animate steps 1–3 on scroll | Each step fades up as it reaches the lower part of the screen, its dot grows in, then its line draws down to the next step; steps that arrive together play 0.22s apart. Section setting **Reveal steps on scroll** (on). Skipped for reduced motion and in the theme editor; without JavaScript the steps simply show |
| Clinically proven numbers don't animate | The count-up worked but began as the row first peeked in, so it had mostly finished before it was in view. Each number now starts when it reaches three quarters of the way up the screen (so the second row counts when it is reached on mobile), runs 2.2s and staggers 0.15s. Still skipped when the device asks for reduced motion |
| Cart drawer padding | One inset for header, items and summary: 16 on mobile, 30 from 750. 24/30 gap under the header. Full width below 750 (Horizon kept it 480 wide down to 480, leaving a strip). The per-item price is hidden when it repeats the line total (quantity 1, no sale). The close button's keyboard focus is an underline instead of a box, since the drawer focuses it on open |
| Accelerated checkout in the cart | Theme setting **Cart › Accelerated checkout buttons** off (the PDP and home buy buttons already had theirs disabled) |
