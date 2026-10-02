# video-banner

## Ticket
From the architecture entry (Figma 965:2346 / 965:3766):
- Full-bleed video poster with a play button that plays inline.
- `video-player` snippet; poster desktop and mobile.
- Aspect ratio 1440:776 on desktop and 1:1 on mobile, adjustable.
- Settings: video (file or URL), poster desktop and mobile, aspect ratio (range), padding.

## Plan
- Height ratio range (% of width, step 2): desktop default 54 (776/1440), mobile 100 in the preset, with "Same at mobile".
- `video-player` with the large play button (79 in Figma maps to `--icon-play-large`, T-22).
- A different mobile cover renders a second `video-player` shown only below 990px; the hidden one's lazy poster is never fetched and neither video loads before a click.

## Reasoning
- **What:** a thin section around the shared `video-player`.
- **Why:** Horizon's video section has no separate mobile cover or ratio per breakpoint.
- **Alternatives rejected:** extending `video-player` with a mobile poster (not in this ticket's files); one `<picture>` inside Horizon's poster button (the `video` snippet only takes one image).
- **Impact:** with a separate mobile cover, the video's markup appears twice in the HTML (inside templates, so nothing downloads).
- **Approver:** Jeet (delegated)

### 2026-10-02: video playback setting
- **What:** a `video_playback` setting (Play on click / Autoplay) passed to `video-player` as `autoplay`. Figma's play buttons mark where video can go, and that video can autoplay.
- **Why:** autoplay is the default, since the Figma banner is ambient footage. In autoplay the section renders one player, so the separate mobile cover is not used (two autoplay players would both download the video).
- **How:** an uploaded video autoplays through Horizon's `video-background-component` (muted, looped, inline, over the poster); a YouTube or Vimeo link autoplays through Horizon's `video` snippet with its controls hidden, scaled from the centre to cover the frame. Under reduced motion an uploaded video stays on its poster.
- **Alternatives rejected:** always autoplay (talking-head UGC loses its sound); a separate autoplay section (duplicate markup and settings).
- **Impact:** an autoplaying uploaded video starts downloading when the page loads (`preload="none"` until the component connects). Keep files short and compressed.
- **Approver:** Jeet (delegated)

## QA checklist
- [ ] 1440: 1440×776 frame, large frosted play button centred.
- [ ] 390: 390×390 frame.
- [ ] Network: no video request before clicking play; video plays inline after click.
- [ ] Different mobile cover shows below 990px only; desktop cover above.
- [ ] YouTube/Vimeo link with a cover image loads the iframe only after click.
- [ ] Height ranges change the ratio; "Same at mobile" hides the mobile range.

## Merchant guide
Add **Video banner** from Storytelling. Upload the video (or paste a YouTube/Vimeo link) and choose a desktop cover image. Untick **Same at mobile** to choose a square mobile cover. Use **Height** to set how tall the banner is as a percentage of its width.
- Turn on **Video playback → Autoplay** for silent background footage, or **Play on click** for a film with sound. A separate mobile cover only applies with Play on click.
