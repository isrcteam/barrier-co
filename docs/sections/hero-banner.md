# hero-banner

## Ticket
From the architecture entry (Figma hero 965:1254 / 965:3083, inset banner 965:1579 / 965:3294):
- Full-bleed ("Hero") or inset ("Inset banner") image, optional background video loop.
- `image_desktop` and `image_mobile` in one `<picture>`; eager and high priority only when the section is first on the page.
- Heading tag separate from size (display or h1 role).
- Vertical bar beside the copy using `--icon-bar-desktop` / `--icon-bar-mobile` in the text colour.
- Play button opens a native `<dialog>` holding the `video-player` snippet; nothing loads before the click.
- Product spotlight renders `product-spotlight` (card style) with "Starts from [price]/mo" and Shop now.
- White text on the image; optional overlay gradient with `--color-overlay` at `--opacity-brand-overlay`.
- Content sits clear of a transparent header overlay.

## Plan
- Section shell: `contrast-override` + `color-custom-{id}`, `background_color` (no default), padding pairs with "Same at mobile".
- Media layer absolutely positioned under a flex column (`hero-banner__inner`) that pushes content to the bottom (Hero) or centre (Inset).
- First-section offset: `--header-height × --transparent-header-offset-boolean`, measured by Horizon's `measure-header-heights`.
- Play: Horizon `dialog-component` (dialog.js already loaded by `scripts.liquid`), `dialog-styles`, `video-player` inside.
- Heights from tokens: Hero desktop `80×10+30+6` (≈836), mobile `80×8+60` (700); Inset desktop `80×8+40−4` (676), mobile `80×8` (640).

## Reasoning
- **What:** one section with two presets rather than two sections, because both are the same image-plus-copy banner and differ only in width, alignment and optional pieces.
- **Why:** Horizon's stock `hero` can't place a spotlight card beside the copy, draw the bar, or open a film in a dialog without custom blocks, and its block model would make the preset harder for the merchant to edit.
- **Alternatives rejected:** stock `hero` with blocks (no bar, no dialog trigger, heavy settings surface); a custom JS module to auto-play the film when the dialog opens (Horizon has no hook for it, and adding JS for one click wasn't worth it, so the poster's own play button starts the film).
- **Impact:** no new JS; CSS scoped to `.hero-banner`. The film costs nothing until the shopper clicks play twice (open, then play).
- **Approver:** Jeet (delegated)

## QA checklist
- [ ] Hero preset first on the home page: image has `loading="eager"` and `fetchpriority="high"`; inset preset lower on the page is lazy.
- [ ] Different mobile image shows below 990px when "Same at mobile" is off.
- [ ] With a transparent header, heading and play button are not covered by the header at 390 and 1440.
- [ ] Bar is 12 wide on mobile and 30 wide on desktop, full height of the copy, white over the image.
- [ ] Play button: keyboard focus ring visible; Enter opens the dialog; Network tab shows no video request until the poster's play button is pressed; Esc and the close button close it and pause the video.
- [ ] Spotlight shows the product image, title, "Starts from $X/mo" (lowest selling-plan price) and Shop now; image left/text right on mobile, stacked card on desktop.
- [ ] Inset banner: 1380 wide with 30 gutters at 1440, full-bleed on mobile; eyebrow, heading, text and Know more button centred vertically on the left.
- [ ] Heading tag setting changes the element only; heading size switches between display and h1.
- [ ] Reduced motion: background video hidden, image shows; dialog opens without animation.
- [ ] Theme editor: both presets add with real copy; blank background = Sandstone.

## Merchant guide
Add **Hero banner** from Banners and pick the **Hero** or **Inset banner** preset. Choose a desktop image (and untick "Same at mobile" to set a mobile crop). Type the eyebrow, heading and text; bold text in the text box shows in the medium weight. To show the film, upload it under **Play video** (or paste a YouTube/Vimeo link with a cover image). Pick a product under **Product spotlight** to show the Shop now card; `[price]` in the price label becomes the lowest subscription price. Width and content position switch between the two layouts. Leave Background color empty to use the page background.


### Reasoning, 2026-10-01: preload the first hero image
- **What:** when the hero is the first section, its base `<img>` (the mobile crop when one is set) is output with `preload: true`. Shopify then sends a `Link: rel=preload` header.
- **Why:** Lighthouse mobile showed about 2.8 s of LCP load delay while the hero waited behind CSS, fonts and scripts. Home scored 83–84 with a 4.2 s LCP.
- **Trade-off:** a preload can't carry the `<picture>` media query, so desktop visitors also fetch the mobile crop (about 80 KB). Mobile is the larger audience and the weaker LCP, so it gets the preload.
- **Alternative rejected:** a hand-written preload in the layout. The layout can't read the hero's settings.
- **Approver:** Jeet (delegated).

**Outcome, same day:** reverted. Measured on the preview theme (Lighthouse mobile, two runs each), the preload made the page slower: 72/76 with it against 83/84 without, and LCP load delay rose from 2.8 s to 3.6–3.9 s. The image stays `eager` + `fetchpriority="high"` with no preload. Re-measure on the published theme at launch, where pages are cached and the preview bar is gone.
