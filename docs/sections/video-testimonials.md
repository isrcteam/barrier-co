# video-testimonials

## Ticket
From docs/architecture.md (video-testimonials). Figma: home 965:1433 / 965:3223, PDP 965:2235 / 965:3649.
- "Real use. Real routines." heading over a horizontal row of portrait UGC video cards that play on click (small play icon).
- Clay quote cards (stars, quote, name) can sit between the videos.
- Videos come from `ugc_video` metaobjects: the section's metaobject list, or `product.metafields.custom.ugc_videos` on the PDP when "Use product data" is on.
- Quote cards are section blocks that reference a `testimonial` metaobject or are typed in.
- Videos load only on click (`preload="none"` with a poster) and one plays at a time.
- Arrows on desktop, dots on mobile.
- Merchant can set heading, source toggle, video list, background colour and padding.

## Plan
- Section `sections/video-testimonials.liquid`, no new JS. Horizon `slideshow` + `slideshow-slide` + `slideshow-controls` (dots plus arrows in one bar; CSS shows arrows at 990px and up, dots below).
- Video cards render `snippets/video-player.liquid` with `play_size: 'small'`; quote cards render `snippets/star-rating.liquid` (medium).
- Slides interleave: video, quote, video, quote... and then whatever is left of either list.
- Card width: 70% of the row on mobile (one card plus a peek), `columns_desktop` cards per row on desktop (default 5, gap 20). Cards are 13:17 (260 x 340 in Figma).
- Quote cards get their own surface through a second `contrast-override` scoped to `<section id>-quote`, driven by the "Quote card background" setting.

## Reasoning
- **What:** one section with a metaobject list for videos and section-local `quote` blocks.
- **Why:** videos repeat across home and PDP, so they belong in `ugc_video` metaobjects (data-model.md). Quote cards are placement-specific, so blocks keep them editable in place, with a testimonial reference for reuse.
- **Alternatives rejected:** a `video` block per card (architecture listed it) was left out because the metaobject list already covers home and PDP, and two sources for the same card would confuse editors. A custom carousel script was rejected in favour of Horizon's `slideshow-component`. A fixed Clay colour was rejected because the colour model forbids hex in Liquid, so the quote surface is a colour setting set in the template.
- **Impact:** no new JS or CSS files; styles live in the section's stylesheet. The PDP needs `use_product_data` on.
- **Approver:** Jeet (delegated).

### 2026-10-02: video playback setting
- **What:** a `video_playback` setting (Play on click / Autoplay) passed to `video-player` as `autoplay`. Figma's play buttons mark where video can go, and that video can autoplay.
- **Why:** play on click is the default, since creators talking need sound. The merchant can switch to autoplay for silent clips.
- **How:** an uploaded video autoplays through Horizon's `video-background-component` (muted, looped, inline, over the poster); a YouTube or Vimeo link autoplays through Horizon's `video` snippet with its controls hidden, scaled from the centre to cover the frame. Under reduced motion an uploaded video stays on its poster.
- **Alternatives rejected:** always autoplay (talking-head UGC loses its sound); a separate autoplay section (duplicate markup and settings).
- **Impact:** an autoplaying uploaded video starts downloading when the page loads (`preload="none"` until the component connects). Keep files short and compressed.
- **Approver:** Jeet (delegated)

## QA checklist
- [ ] Desktop 1440: heading centred, 5 cards of equal width with 20 gaps, arrows at the row's edges below; previous arrow is hidden on the first slide.
- [ ] Mobile 390: one card plus a peek, 10 gap, square Tan dots (6) below; no arrows.
- [ ] Clicking a poster loads and plays the video; starting a second video pauses the first. No video downloads before a click (Network tab).
- [ ] With "Use product data" on the PDP and the product's `custom.ugc_videos` filled, the product's videos show; with it empty, the section's list shows.
- [ ] Quote block with a testimonial picked shows that testimonial's quote, name and stars; without one, the typed fields show.
- [ ] Quote card background setting changes the card surface and the text contrasts with it.
- [ ] Keyboard: play buttons, arrows and dots are reachable and show the focus ring.
- [ ] Reduced motion: the carousel jumps instead of scrolling smoothly.

## Merchant guide
1. Add videos in Content > Metaobjects > UGC video (title, video file, optional poster).
2. In the theme editor, open "Video testimonials" and pick the videos under "UGC videos". On the product template, turn on "Use product data" to use each product's own "UGC videos" metafield instead.
3. Add "Quote card" blocks. Pick a testimonial, or type a quote, name and rating. Quote cards sit between videos in the order you add them.
4. Set "Quote card background" (Clay in the design) and the section background, then adjust padding (turn off "Same at mobile" to set mobile padding separately).

## Figma diff 2026-10-02
Measured against HOMEPAGE 965:1253 and 965:3078. Deltas and fixes: `docs/qa/figma-diff-home.md`.

### Reasoning, 2026-10-02: UGC cards with posters, ready for video files
- **What:** the five creator frames from Figma (965:2238) are uploaded as `ugc-creator-1…5.jpg` and attached to five `ugc_video` entries (`customer-video-1…5`). Home shows 1, 3 and 4 interleaved with the quote cards; the PDP shows all five through `custom.ugc_videos`, with no quote cards, as in the Figma desktop PDP.
- **Video field now optional:** `ugc_video.video` is no longer required, so an entry can exist with a poster only. A card without a video shows its poster and no play button; once a video file is added to the entry, the play button appears and it plays on click. Template changes aren't needed for that.
- **Bug fixed:** cards were picked with `videos[video_index]`, which doesn't resolve on metaobject lists. Cards are now pre-rendered in a `for` loop into a plain array, then interleaved with the quotes.
- **Open:** the actual video files (D-6). Upload each to Files and set it on its entry under Content › Metaobjects › UGC video.
- **Approver:** Jeet.
- **Video playback** sets all creator videos to play on click (with sound) or autoplay (muted, looped).

## Changes 2026-10-06 (internal QA and Dev Ready)
- Play on click now toggles pause and play on tap, with no native controls (annotation 2).
- Arrows hide when every card fits (QA 14); trackpad scrolling works (QA 12); on mobile the track runs to the screen edge (QA 35).
