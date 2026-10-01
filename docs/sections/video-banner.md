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

## QA checklist
- [ ] 1440: 1440×776 frame, large frosted play button centred.
- [ ] 390: 390×390 frame.
- [ ] Network: no video request before clicking play; video plays inline after click.
- [ ] Different mobile cover shows below 990px only; desktop cover above.
- [ ] YouTube/Vimeo link with a cover image loads the iframe only after click.
- [ ] Height ranges change the ratio; "Same at mobile" hides the mobile range.

## Merchant guide
Add **Video banner** from Storytelling. Upload the video (or paste a YouTube/Vimeo link) and choose a desktop cover image. Untick **Same at mobile** to choose a square mobile cover. Use **Height** to set how tall the banner is as a percentage of its width.
