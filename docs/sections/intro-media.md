# intro-media

## Ticket
From the architecture entry (Figma 965:1329 / 965:3147, editorial option 965:3065):
- Eyebrow and large heading on the left, body text on the right; stacked on mobile.
- Full-width video or image underneath, or two tiles (Editorial preset).
- Video uses the `video-player` snippet: poster first, plays on click.
- Settings: eyebrow, heading, heading tag, text, media type, image, video, poster, second tile toggle, background colour, padding.

## Plan
- Two-column header grid at 990px (`1fr 1fr`; Editorial aligns to the tile columns `1fr / (text-width − 8)` = 552).
- Tiles loop over `first` and optional `second` settings with the same shape (type, image, video, video URL, cover image).
- Aspect ratios from the frames: single 23/11 desktop (1380×660), 13/11 mobile (390×330); editorial first tile 399/287 (798×574), second stretches to its height.
- Media is full-bleed on mobile, inside the 30 gutter on desktop.

## Reasoning
- **What:** a custom section; Horizon's `media-with-content` puts media beside text, not under a split header.
- **Why:** the editorial option is the same header with two tiles, so it's a preset and a toggle, not another section.
- **Alternatives rejected:** stock `section` with group blocks (merchant would rebuild the grid by hand; no poster-first video); a separate editorial section (duplicate code).
- **Impact:** no JS beyond Horizon's `deferred-media`. A YouTube/Vimeo link without any cover image falls back to a placeholder so no iframe loads on page load.
- **Approver:** Jeet (delegated)

### 2026-10-02: video playback setting
- **What:** a `video_playback` setting (Play on click / Autoplay) passed to `video-player` as `autoplay`. Figma's play buttons mark where video can go, and that video can autoplay.
- **Why:** autoplay is the default, since the Figma tiles are ambient footage.
- **How:** an uploaded video autoplays through Horizon's `video-background-component` (muted, looped, inline, over the poster); a YouTube or Vimeo link autoplays through Horizon's `video` snippet with its controls hidden, scaled from the centre to cover the frame. Under reduced motion an uploaded video stays on its poster.
- **Alternatives rejected:** always autoplay (talking-head UGC loses its sound); a separate autoplay section (duplicate markup and settings).
- **Impact:** an autoplaying uploaded video starts downloading when the page loads (`preload="none"` until the component connects). Keep files short and compressed.
- **Approver:** Jeet (delegated)

## QA checklist
- [ ] 1440: heading left, text right, bottoms aligned, 30 gap; media 1380×660.
- [ ] 390: eyebrow, heading, text stacked with 10 gutters; media full width at 390×330.
- [ ] Video tile: poster and frosted play button; no video request until click; one video plays at a time.
- [ ] Editorial preset: image tile 798 wide and video tile 552 wide at 1440, both 574 tall; stacked on mobile.
- [ ] Heading tag setting changes the element only.
- [ ] Images lazy-loaded with widths and sizes.
- [ ] Background color blank = Sandstone.

## Merchant guide
Add **Intro with media** from Storytelling, or the **Editorial** preset for two tiles. Fill in the eyebrow, heading and text. Under **Media 1**, choose Image or Video; for a video, upload it (or paste a YouTube/Vimeo link) and add a cover image. Tick **Show second tile** to add a narrower tile on the right with its own image or video.

## Figma diff 2026-10-02
Measured against HOMEPAGE 965:1253 and 965:3078. Deltas and fixes: `docs/qa/figma-diff-home.md`.
- **Video playback** applies to both tiles: Autoplay plays muted and looped with no play button; Play on click shows the cover with a play button and plays with sound.

## Changes 2026-10-06 (internal QA and Dev Ready)
- Two-tile version on the homepage; the single-video version is built and disabled (QA 5, annotation 8). **Show only the second tile on mobile**. Mobile text inset 17 (QA 30).
